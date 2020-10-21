# -*- coding: utf-8 -*-
from aiologger import Logger  # pyre-ignore
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple

from poke_env.environment.field import Field
from poke_env.environment.move import Move
from poke_env.environment.move import SPECIAL_MOVES
from poke_env.environment.pokemon import Pokemon
from poke_env.environment.side_condition import SideCondition
from poke_env.environment.weather import Weather
from poke_env.utils import to_id_str


class Battle:

    MESSAGES_TO_IGNORE = {
        "-anim",
        "-burst",
        "-block",
        "-cant",
        "-center",
        "-crit",
        "-combine",
        "-fail",
        "-fieldactivate",
        "-hint",
        "-hitcount",
        "-immune",
        "-ohko",
        "-message",
        "-miss",
        "-notarget",
        "-nothing",
        "-resisted",
        "-singlemove",
        "-singleturn",
        "-supereffective",
        "-waiting",
        "-zbroken",
        "askreg",
        "c",
        "cant",
        "crit",
        "deinit",
        "gametype",
        "gen",
        "html",
        "inactive",
        "immune",
        "j",
        "l",
        "n",
        "rated",
        "resisted",
        "supereffective",
        "tier",
        "t:",
        "upkeep",
        "zbroken",
    }

    __slots__ = (
        "_available_moves",
        "_available_switches",
        "_battle_tag",
        "_can_dynamax",
        "_can_mega_evolve",
        "_can_z_move",
        "_dynamax_turn",
        "_fields",
        "_finished",
        "_force_swap",
        "_force_switch",
        "_format",
        "_in_team_preview",
        "_max_team_size",
        "_maybe_trapped",
        "_move_on_next_request",
        "_opponent_can_dynamax",
        "_opponent_dynamax_turn",
        "_opponent_side_conditions",
        "_opponent_rating",
        "_opponent_team",
        "_opponent_username",
        "_player_role",
        "_player_username",
        "_players",
        "_rating",
        "_rqid",
        "_rules",
        "_side_conditions",
        "_team",
        "_team_size",
        "_teampreview",
        "_teampreview_opponent_team",
        "_trapped",
        "_turn",
        "_wait",
        "_weather",
        "_won",
        "logger",
    )

    def __init__(self, battle_tag: str, username: str, logger: Logger):  # pyre-ignore
        # Utils attributes
        self._battle_tag: str = battle_tag
        self._format: Optional[str] = None
        self._max_team_size: Optional[int] = None
        self._opponent_username: Optional[str] = None
        self._player_role: Optional[str] = None
        self._player_username: str = username
        self._players = []
        self._team_size: Dict[str, int] = {}
        self._teampreview: bool = False
        self._teampreview_opponent_team: Set[Pokemon] = set()
        self.logger: Logger = logger

        # Turn choice attributes
        self._available_moves: List[Move] = []
        self._available_switches: List[Pokemon] = []
        self._can_mega_evolve: bool = False
        self._can_z_move: bool = False
        self._can_dynamax: bool = False
        self._opponent_can_dynamax = True
        self._force_switch: bool = False
        self._in_team_preview: bool = False
        self._maybe_trapped: bool = False
        self._move_on_next_request: bool = False
        self._trapped: bool = False
        self._force_swap: bool = False
        self._wait: Optional[bool] = None

        # Battle state attributes
        self._dynamax_turn: Optional[int] = None
        self._finished: bool = False
        self._rqid = 0
        self._rules = []
        self._turn: int = 0
        self._opponent_dynamax_turn: Optional[int] = None
        self._opponent_rating: Optional[int] = None
        self._rating: Optional[int] = None
        self._won: Optional[bool] = None

        # In game battle state attributes
        self._weather = None
        self._fields = set()
        self._side_conditions = set()
        self._opponent_side_conditions = set()

        # Pokemon attributes
        self._team: Dict[str, Pokemon] = {}
        self._opponent_team: Dict[str, Pokemon] = {}

    def get_pokemon(
        self, identifier: str, force_self_team: bool = False, details: str = ""
    ) -> Pokemon:
        """Returns the Pokemon object corresponding to given identifier. Can force to
        return object from the player's team if force_self_team is True. If the Pokemon
        object does not exist, it will be created. Details can be given, which is
        necessary to initialize alternate forms (eg. alolan pokemons) properly.

        :param identifier: The identifier to use to retrieve the pokemon.
        :type identifier: str
        :param force_self_team: Wheter to force returning a Pokemon from the player's
            team. Defaults to False.
        :type details: str, optional
        :param details: Detailled information about the pokemon. Defaults to ''.
        :type force_self_team: bool, optional, defaults to False
        :return: The corresponding pokemon object.
        :rtype: Pokemon
        :raises AssertionError: If the team has too many pokemons, as determined by the
            teamsize component of battle initialisation.
        """
        player_role = identifier[:2]
        is_mine = player_role == self._player_role
        if identifier[3] != " ":
            identifier = identifier[:2] + identifier[3:]
            species = identifier[5:]
        if details:
            species = details.split(", ")[0]
        else:
            species = identifier[4:]

        if is_mine or force_self_team:
            team: Dict[str, Pokemon] = self._team
        else:
            team: Dict[str, Pokemon] = self._opponent_team

        if identifier in team:
            return team[identifier]
        else:
            try:
                if self._team_size:
                    assert len(team) < self._team_size[player_role]
            except AssertionError:
                self.logger.critical(team, identifier)
                raise ValueError(
                    "%s's team already has 6 pokemons: cannot add %s to %s"
                    % (identifier[:2], identifier, ", ".join(team.keys()))
                )
            team[identifier] = Pokemon(species=species)

            return team[identifier]

    def _end_illusion(self, pokemon_name: str, details: str):
        if pokemon_name[:2] == self._player_role:
            active = self.active_pokemon
        else:
            active = self.opponent_active_pokemon

        if active is None:
            raise ValueError("Cannot end illusion without an active pokemon.")

        pokemon = self.get_pokemon(pokemon_name, details=details)
        pokemon._set_hp(f"{active.current_hp}/{active.max_hp}")
        active._was_illusionned()
        pokemon._switch_in()
        pokemon.status = active.status

    def _field_end(self, field):
        field = Field.from_showdown_message(field)
        assert field in self.fields
        self._fields.remove(field)

    def _field_start(self, field):
        field = Field.from_showdown_message(field)
        self._fields.add(field)

    def _parse_message(self, split_message: List[str]) -> None:
        if split_message[1] in self.MESSAGES_TO_IGNORE:
            return
        elif split_message[1] == "-ability":
            pokemon, ability = split_message[2:4]
            self.get_pokemon(pokemon).ability = ability
        elif split_message[1] == "-activate":
            target, effect = split_message[2:4]
            if target:
                self.get_pokemon(target)._start_effect(effect)
        elif split_message[1] == "-boost":
            pokemon, stat, amount = split_message[2:5]
            self.get_pokemon(pokemon)._boost(stat, int(amount))
        elif split_message[1] == "-clearallboost":
            self.active_pokemon._clear_boosts()
            if self.opponent_active_pokemon is not None:
                self.opponent_active_pokemon._clear_boosts()  # pyre-ignore
        elif split_message[1] == "-clearboost":
            pokemon = split_message[2]
            self.get_pokemon(pokemon)._clear_boosts()
        elif split_message[1] == "-clearnegativeboost":
            pokemon = split_message[2]
            self.get_pokemon(pokemon)._clear_negative_boosts()
        elif split_message[1] == "-clearpositiveboost":
            pokemon = split_message[2]
            self.get_pokemon(pokemon)._clear_positive_boosts()
        elif split_message[1] == "-copyboost":
            source, target = split_message[2:4]
            self.get_pokemon(target)._copy_boosts(self.get_pokemon(source))
        elif split_message[1] == "-curestatus":
            pokemon, status = split_message[2:4]
            self.get_pokemon(pokemon)._cure_status(status)
        elif split_message[1] == "-cureteam":
            self.logger.warning(
                "cureteam management not implemented in battle. Message: %s"
                % split_message
            )
        elif split_message[1] == "-damage":
            pokemon, hp_status = split_message[2:4]
            self.get_pokemon(pokemon)._damage(hp_status)
        elif split_message[1] == "-end":
            pokemon, effect = split_message[2:4]
            self.get_pokemon(pokemon)._end_effect(effect)
        elif split_message[1] == "-endability":
            pokemon = split_message[2]
            self.get_pokemon(pokemon).ability = None
        elif split_message[1] == "-enditem":
            pokemon, item = split_message[2:4]
            self.get_pokemon(pokemon)._end_item(item)
        elif split_message[1] == "-fieldend":
            condition = split_message[2]
            self._field_end(condition)
        elif split_message[1] == "-fieldstart":
            condition = split_message[2]
            self._field_start(condition)
        elif split_message[1] in ["-formechange", "detailschange"]:
            pokemon, species = split_message[2:4]
            self.get_pokemon(pokemon)._forme_change(species)
        elif split_message[1] == "-heal":
            pokemon, hp_status = split_message[2:4]
            self.get_pokemon(pokemon)._heal(hp_status)
        elif split_message[1] == "-invertboost":
            pokemon = split_message[2]
            self.get_pokemon(pokemon)._invert_boosts()
        elif split_message[1] == "-item":
            pokemon, item = split_message[2:4]
            self.get_pokemon(pokemon).item = to_id_str(item)
        elif split_message[1] == "-mega":
            pokemon, megastone = split_message[2:4]
            self.get_pokemon(pokemon)._mega_evolve(megastone)
        elif split_message[1] == "-mustrecharge":
            pokemon = split_message[2]
            self.get_pokemon(pokemon).must_recharge = True
        elif split_message[1] == "-prepare":
            try:
                attacker, move, defender = split_message[2:5]
                self.get_pokemon(defender)
            except ValueError:
                attacker, move = split_message[2:4]
                defender = None
            self.get_pokemon(attacker)._prepare(move, defender)
        elif split_message[1] == "-primal":
            pokemon = split_message[2]
            self.get_pokemon(pokemon)._primal()
        elif split_message[1] == "-setboost":
            pokemon, stat, amount = split_message[2:5]
            self.get_pokemon(pokemon)._set_boost(stat, int(amount))
        elif split_message[1] == "-sethp":
            pokemon, hp_status = split_message[2:4]
            self.get_pokemon(pokemon)._set_hp(hp_status)
        elif split_message[1] == "-sideend":
            side, condition = split_message[2:4]
            self._side_end(side, condition)
        elif split_message[1] == "-sidestart":
            side, condition = split_message[2:4]
            self._side_start(side, condition)
        elif split_message[1] == "-start":
            pokemon, effect = split_message[2:4]
            pokemon = self.get_pokemon(pokemon)
            pokemon._start_effect(effect)

            if pokemon.is_dynamaxed:
                if pokemon in set(self.team.values()) and self._dynamax_turn is None:
                    self._dynamax_turn = self.turn
                    # self._can_dynamax value is set via _parse_request()
                elif (
                    pokemon in set(self.opponent_team.values())
                    and self._opponent_dynamax_turn is None
                ):
                    self._opponent_dynamax_turn = self.turn
                    self._opponent_can_dynamax = False
        elif split_message[1] == "-status":
            pokemon, status = split_message[2:4]
            self.get_pokemon(pokemon).status = status
        elif split_message[1] == "-swapboost":
            source, target, stats = split_message[2:5]
            self.get_pokemon(target)._swap_boosts()
        elif split_message[1] == "-transform":
            pokemon, into = split_message[2:4]
            self.get_pokemon(pokemon)._transform(self.get_pokemon(into))
        elif split_message[1] == "-unboost":
            pokemon, stat, amount = split_message[2:5]
            self.get_pokemon(pokemon)._boost(stat, -int(amount))
        elif split_message[1] == "-weather":
            weather = split_message[2]
            self.weather = weather
        elif split_message[1] == "-zpower":
            pokemon = split_message[2]
            self.get_pokemon(pokemon)._used_z_move()
        elif split_message[1] == "clearpoke":
            self._in_team_preview = True
        elif split_message[1] in ["drag", "switch"]:
            pokemon, details, hp_status = split_message[2:5]
            self._switch(pokemon, details, hp_status)
        elif split_message[1] == "faint":
            pokemon = split_message[2]
            self.get_pokemon(pokemon)._faint()
        elif split_message[1] == "gen":
            self._format = split_message[2]
        elif split_message[1] == "move":
            pokemon, move, target = split_message[2:5]
            self.get_pokemon(pokemon)._moved(move)
        elif split_message[1] == "player":
            player, username, avatar, rating = split_message[2:6]
            if username == self._player_username:
                self._player_role = player
            return self._players.append(
                {
                    "username": username,
                    "player": player,
                    "avatar": avatar,
                    "rating": rating,
                }
            )
        elif split_message[1] == "poke":
            player, details = split_message[2:4]
            self._register_teampreview_pokemon(player, details)
        elif split_message[1] == "raw":
            username, rating_info = split_message[2].split("'s rating: ")
            rating = int(rating_info[:4])
            if username == self.player_username:
                self._rating = rating
            elif username == self.opponent_username:
                self._opponent_rating = rating
            else:
                self.logger.warning(
                    "Rating information regarding an unrecognized username received. "
                    "Received '%s', while only known players are '%s' and '%s'",
                    username,
                    self.player_username,
                    self.opponent_username,
                )
        elif split_message[1] == "replace":
            pokemon = split_message[2]
            details = split_message[3]
            self._end_illusion(pokemon, details)
        elif split_message[1] == "rule":
            self._rules.append(split_message[2])
        elif split_message[1] == "start":
            self._in_team_preview = False
        elif split_message[1] == "swap":
            pokemon, position = split_message[2:4]
            self._swap(pokemon, position)
        elif split_message[1] == "teamsize":
            player, number = split_message[2:4]
            number = int(number)
            self._team_size[player] = number
        else:
            raise NotImplementedError(split_message)

    def _parse_request(self, request: Dict) -> None:
        """
        Update the object from a request.
        The player's pokemon are all updated, as well as available moves, switches and
        other related information (z move, mega evolution, forced switch...).
        Args:
            request (dict): parsed json request object
        """
        self.logger.debug(
            "Parsing the following request update in battle %s:\n%s",
            self.battle_tag,
            request,
        )

        if "wait" in request and request["wait"]:
            self._wait = True
        else:
            self._wait = False

        self._available_moves = []
        self._available_switches = []
        self._can_mega_evolve = False
        self._can_z_move = False
        self._can_dynamax = False
        self._maybe_trapped = False
        self._trapped = False
        self._force_switch = request.get("forceSwitch", False)

        if self._force_switch:
            self._move_on_next_request = True

        if request["rqid"]:
            self._rqid = max(self._rqid, request["rqid"])

        if request.get("teamPreview", False):
            self._teampreview = True
            self._max_team_size = request["maxTeamSize"]
        else:
            self._teampreview = False
        self._update_team_from_request(request["side"])

        if "active" in request:
            active_request = request["active"][0]
            active_pokemon = self.active_pokemon

            if active_request.get("trapped"):
                self._trapped = True

            for move in active_request["moves"]:
                if not move.get("disabled", False):
                    if move["id"] in active_pokemon.moves:
                        self._available_moves.append(active_pokemon.moves[move["id"]])
                    elif move["id"] in SPECIAL_MOVES:
                        self._available_moves.append(SPECIAL_MOVES[move["id"]])
                    else:
                        try:
                            if not {
                                "copycat",
                                "metronome",
                                "mefirst",
                                "mirrormove",
                                "assist",
                            }.intersection(self.active_pokemon.moves.keys()):
                                self.logger.critical(
                                    "An error occured in battle %s while adding "
                                    "available moves. The move '%s' was either unknown "
                                    "or not available for the active pokemon: %s",
                                    self.battle_tag,
                                    move["id"],
                                    self.active_pokemon.species,
                                )
                            else:
                                self.logger.warning(
                                    "The move '%s' was received in battle %s for your "
                                    "active pokemon %s. This move could not be added, "
                                    "but it might come from a special move such as "
                                    "copycat or me first. If that is not the case, "
                                    "please make sure there is an explanation for this "
                                    "behavior or report it if it is an error.",
                                    move["id"],
                                    self.battle_tag,
                                    self.active_pokemon.species,
                                )
                            move = Move(move["id"])
                            self._available_moves.append(move)
                        except AttributeError:
                            pass
            if active_request.get("canMegaEvo", False):
                self._can_mega_evolve = True
            if active_request.get("canZMove", False):
                self._can_z_move = True
            if active_request.get("canDynamax", False):
                self._can_dynamax = True
            if active_request.get("maybeTrapped", False):
                self._maybe_trapped = True

        side = request["side"]

        if side["pokemon"]:
            self._player_role = side["pokemon"][0]["ident"][:2]

        if not self.trapped:
            for pokemon in side["pokemon"]:
                if pokemon:
                    pokemon = self._team[pokemon["ident"]]
                    if not pokemon.active and not pokemon.fainted:
                        self._available_switches.append(pokemon)

    def _register_teampreview_pokemon(self, player: str, details: str):
        if player != self._player_role:
            mon = Pokemon(details=details)
            self._teampreview_opponent_team.add(mon)

    def _side_end(self, side, condition):
        if side[:2] == self._player_role:
            conditions = self.side_conditions
        else:
            conditions = self.opponent_side_conditions
        condition = SideCondition.from_showdown_message(condition)
        conditions.remove(condition)

    def _side_start(self, side, condition):
        if side[:2] == self._player_role:
            conditions = self.side_conditions
        else:
            conditions = self.opponent_side_conditions
        condition = SideCondition.from_showdown_message(condition)
        conditions.add(condition)

    def _swap(self, *args, **kwargs):
        self.logger.warning("swap method in Battle is not implemented")

    def _switch(self, pokemon, details, hp_status):
        identifier = pokemon.split(":")[0][:2]
        if identifier == self._player_role:
            self.active_pokemon._switch_out()
        else:
            if self.opponent_active_pokemon:
                self.opponent_active_pokemon._switch_out()
        pokemon = self.get_pokemon(pokemon, details=details)
        pokemon._switch_in()
        pokemon._set_hp_status(hp_status)

    def _tied(self):
        self._finished = True

    def _update_team_from_request(self, side: Dict) -> None:
        for pokemon in side["pokemon"]:
            self.get_pokemon(
                pokemon["ident"], force_self_team=True, details=pokemon["details"]
            )._update_from_request(pokemon)

    def _won_by(self, player_name: str):
        if player_name == self._player_username:
            self._won = True
        else:
            self._won = False
        self._finished = True

    @property
    def active_pokemon(self) -> Pokemon:
        """
        :return: The active pokemon
        :rtype: Pokemon
        """
        for pokemon in self.team.values():
            if pokemon.active:
                return pokemon
        raise ValueError("No active pokemon found in the current team")

    @property
    def available_moves(self) -> List[Move]:
        """
        :return: The list of moves the player can use during the current move request.
        :rtype: List[Move]
        """
        return self._available_moves

    @property
    def available_switches(self) -> List[Pokemon]:
        """
        :return: The list of switches the player can do during the current move request.
        :rtype: List[Pokemon]
        """
        return self._available_switches

    @property
    def battle_tag(self) -> str:
        """
        :return: The battle identifier.
        :rtype: str
        """
        return self._battle_tag

    @property
    def can_dynamax(self) -> bool:
        """
        :return: Wheter of not the current active pokemon can dynamax
        :rtype: bool
        """
        return self._can_dynamax

    @property
    def can_mega_evolve(self) -> bool:
        """
        :return: Wheter of not the current active pokemon can mega evolve.
        :rtype: bool
        """
        return self._can_mega_evolve

    @property
    def can_z_move(self) -> bool:
        """
        :return: Wheter of not the current active pokemon can z-move.
        :rtype: bool
        """
        return self._can_z_move

    @property
    def dynamax_turns_left(self) -> Optional[int]:
        """
        :return: How many turns of dynamax are left. None if dynamax is not active
        :rtype: int, optional
        """
        if self.active_pokemon.is_dynamaxed:
            return 3 - (self.turn - self._dynamax_turn)  # pyre-ignore

    @property
    def fields(self) -> Set[Field]:
        """
        :return: The set of active fields.
        :rtype: Set[Field]
        """
        return self._fields

    @property
    def finished(self) -> bool:
        """
        :return: A boolean indicating whether the battle is finished.
        :rtype: Optional[bool]
        """
        return self._finished

    @property
    def force_switch(self) -> bool:
        """
        :return: A boolean indicating whether the active pokemon is forced to switch
            out.
        :rtype: Optional[bool]
        """
        return self._force_switch

    @property
    def lost(self) -> Optional[bool]:
        """
        :return: If the battle is finished, a boolean indicating whether the battle is
            lost. Otherwise None.
        :rtype: Optional[bool]
        """
        return self._won is False

    @property
    def max_team_size(self) -> Optional[int]:
        """
        :return: The maximum acceptable size of the team to return in teampreview, if
            applicable.
        :rtype: int, optional
        """
        return self._max_team_size

    @property
    def maybe_trapped(self) -> bool:
        """
        :return: A boolean indicating whether the active pokemon is maybe trapped by the
            opponent.
        :rtype: bool
        """
        return self._maybe_trapped

    @property
    def opponent_active_pokemon(self) -> Optional[Pokemon]:
        """
        :return: The opponent active pokemon
        :rtype: Pokemon
        """
        for pokemon in self.opponent_team.values():
            if pokemon.active:
                return pokemon
        return None

    @property
    def opponent_can_dynamax(self) -> bool:
        """
        :return: Wheter of not opponent's current active pokemon can dynamax
        :rtype: bool
        """
        return self._opponent_can_dynamax

    @property
    def opponent_dynamax_turns_left(self) -> Optional[int]:
        """
        :return: How many turns of dynamax are left for the opponent's pokemon.
            None if dynamax is not active
        :rtype: Optional[int]
        """
        if (
            self.opponent_active_pokemon is not None
        ) and self.opponent_active_pokemon.is_dynamaxed:  # pyre-ignore
            return 3 - (self.turn - self._opponent_dynamax_turn)  # pyre-ignore

    @property
    def opponent_side_conditions(self) -> Set[SideCondition]:
        """
        :return: The opponent's set of side conditions.
        :rtype: Set[SideCondition]
        """
        return self._opponent_side_conditions

    @property
    def opponent_team(self) -> Dict[str, Pokemon]:
        """
        During teampreview, keys are not definitive: please rely on values.

        :return: The opponent's team. Keys are identifiers, values are pokemon objects.
        :rtype: Dict[str, Pokemon]
        """
        if self._opponent_team:
            return self._opponent_team
        else:
            return {mon.species: mon for mon in self._teampreview_opponent_team}

    @property
    def opponent_username(self) -> Optional[str]:
        """
        :return: The opponent's username, or None if unknown.
        :rtype: str, optional.
        """
        return self._opponent_username

    @property
    def player_username(self) -> str:
        """
        :return: The player's username.
        :rtype: str
        """
        return self._player_username

    @property
    def players(self) -> Tuple[str, str]:
        """
        :return: The pair of players' usernames.
        :rtype: Tuple[str, str]
        """
        return self._players

    @players.setter
    def players(self, players: Tuple[str, str]) -> None:
        """Sets the battle player's name:

        :param player_1: First player's username.
        :type player_1: str
        :param player_1: Second player's username.
        :type player_2: str
        """
        player_1, player_2 = players
        if player_1 != self._player_username:
            self._opponent_username = player_1
        else:
            self._opponent_username = player_2

    @property
    def rating(self) -> Optional[int]:
        """
        Player's rating after the end of the battle, if it was received.

        :return: The player's rating after the end of the battle.
        :rtype: int, optional
        """
        return self._rating

    @property
    def opponent_rating(self) -> Optional[int]:
        """
        Opponent's rating after the end of the battle, if it was received.

        :return: The opponent's rating after the end of the battle.
        :rtype: int, optional
        """
        return self._opponent_rating

    @property
    def rqid(self) -> int:
        """
        Should not be used.

        :return: The last request's rqid.
        :rtype: Tuple[str, str]
        """
        return self._rqid

    @property
    def side_conditions(self) -> Set[SideCondition]:
        """
        :return: The player's set of side conditions.
        :rtype: Set[SideCondition]
        """
        return self._side_conditions

    @property
    def team(self) -> Dict[str, Pokemon]:
        """
        :return: The player's team. Keys are identifiers, values are pokemon objects.
        :rtype: Dict[str, Pokemon]
        """
        return self._team

    @property
    def team_size(self) -> int:
        """
        :return: The number of Pokemon in the player's team.
        :rtype: int
        """
        role = self._player_role
        if role is not None:
            return self._team_size[role]
        raise ValueError(
            "Team size cannot be inferred without an assigned player role."
        )

    @property
    def teampreview(self) -> bool:
        """
        :return: Wheter the battle is awaiting a teampreview order.
        :rtype: bool
        """
        return self._teampreview

    @property
    def trapped(self) -> bool:
        """
        :return: A boolean indicating whether the active pokemon is trapped by the
            opponent.
        :rtype: bool
        """
        return self._trapped

    @trapped.setter
    def trapped(self, value):
        self._trapped = value

    @property
    def turn(self) -> int:
        """
        :return: The current battle turn.
        :rtype: int
        """
        return self._turn

    @turn.setter
    def turn(self, turn: int) -> None:
        """Sets the current turn counter to given value.

        :param turn: Current turn value.
        :type turn: int
        """
        self._turn = turn

    @property
    def weather(self) -> Optional[Weather]:
        """
        :return: The battle's weather or None if no weather is active.
        :rtype: Optional[Weather]
        """
        return self._weather

    @weather.setter
    def weather(self, weather):
        if weather == "none":
            self._weather = None
        else:
            try:
                self._weather = Weather[weather.upper()]
            except Exception as e:
                self.logger.warning("Weather %s unknown (%s)", weather, e)

    @property
    def won(self) -> Optional[bool]:
        """
        :return: If the battle is finished, a boolean indicating whether the battle is
            won. Otherwise None.
        :rtype: Optional[bool]
        """
        return self._won

    @property
    def move_on_next_request(self) -> bool:
        """
        :return: Wheter the next received request should yield a move order directly.
            This can happen when a switch is forced, or an error is encountered.
        :rtype: bool
        """
        return self._move_on_next_request

    @move_on_next_request.setter
    def move_on_next_request(self, value) -> None:
        self._move_on_next_request = value
