from abc import ABC
from abc import abstractmethod
from abc import abstractproperty

from logging import Logger
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple
from typing import Union

from poke_env.data import _REPLAY_TEMPLATE, GenData, to_id_str
from poke_env.environment.field import Field
from poke_env.environment.pokemon import Pokemon
from poke_env.environment.side_condition import STACKABLE_CONDITIONS, SideCondition
from poke_env.environment.weather import Weather

import os


class AbstractBattle(ABC):
    MESSAGES_TO_IGNORE = {
        "-anim",
        "-burst",
        "-block",
        "-center",
        "-crit",
        "-combine",
        "-fail",
        "-fieldactivate",
        "-hint",
        "-hitcount",
        "-ohko",
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
        "debug",
        "chat",
        "c",
        "crit",
        "deinit",
        "gametype",
        "gen",
        "html",
        "init",
        "immune",
        "join",
        "j",
        "J",
        "leave",
        "l",
        "L",
        "name",
        "n",
        "rated",
        "resisted",
        "split",
        "supereffective",
        "teampreview",
        "tier",
        "upkeep",
        "zbroken",
    }

    __slots__ = (
        "_available_moves",
        "_available_switches",
        "_battle_tag",
        "_can_dynamax",
        "_can_mega_evolve",
        "_can_terastallize",
        "_can_z_move",
        "_dynamax_turn",
        "_fields",
        "_finished",
        "_force_switch",
        "_format",
        "_in_team_preview",
        "_max_team_size",
        "_maybe_trapped",
        "_move_on_next_request",
        "_opponent_can_dynamax",
        "_opponent_can_mega_evolve",
        "_opponent_can_terastallize",
        "_opponent_can_z_move",
        "_opponent_dynamax_turn",
        "_opponent_rating",
        "_opponent_side_conditions",
        "_opponent_team",
        "_opponent_username",
        "_player_role",
        "_player_username",
        "_players",
        "_rating",
        "_rqid",
        "_rules",
        "_reviving",
        "_side_conditions",
        "_team_size",
        "_team",
        "_teampreview_opponent_team",
        "_teampreview",
        "_trapped",
        "_turn",
        "_wait",
        "_weather",
        "_won",
        "logger",
    )

    def __init__(
        self,
        battle_tag: str,
        username: str,
        logger: Logger,
        save_replays: Union[str, bool],
        gen: int,
    ):
        # Load data
        self._data = GenData.from_gen(gen)

        # Utils attributes
        self._battle_tag: str = battle_tag
        self._format: Optional[str] = None
        self._max_team_size: Optional[int] = None
        self._opponent_username: Optional[str] = None
        self._player_role: Optional[str] = None
        self._player_username: str = username
        self._players = []
        self._replay_data: List[List[str]] = []
        self._save_replays: Union[bool, str] = save_replays
        self._team_size: Dict[str, int] = {}
        self._teampreview: bool = False
        self._teampreview_opponent_team: Set[Pokemon] = set()
        self._anybody_inactive: bool = False
        self._reconnected: bool = True
        self.logger: Logger = logger

        # Turn choice attributes
        self._in_team_preview: bool = False
        self._move_on_next_request: bool = False
        self._wait: Optional[bool] = None

        # Battle state attributes
        self._dynamax_turn: Optional[int] = None
        self._finished: bool = False
        self._rqid = 0
        self._rules = []
        self._turn: int = 0
        self._opponent_can_terrastallize: bool = True
        self._opponent_dynamax_turn: Optional[int] = None
        self._opponent_rating: Optional[int] = None
        self._rating: Optional[int] = None
        self._won: Optional[bool] = None

        # In game battle state attributes
        self._weather: Dict[Weather, int] = {}
        self._fields: Dict[Field, int] = {}  # set()
        self._opponent_side_conditions: Dict[SideCondition, int] = {}  # set()
        self._side_conditions: Dict[SideCondition, int] = {}  # set()
        self._reviving: bool = False

        # Pokemon attributes
        self._team: Dict[str, Pokemon] = {}
        self._opponent_team: Dict[str, Pokemon] = {}

    def get_pokemon(
        self,
        identifier: str,
        force_self_team: bool = False,
        details: str = "",
        request: Optional[dict] = None,
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
        :raises ValueError: If the team has too many pokemons, as determined by the
            teamsize component of battle initialisation.
        """
        if identifier[3] != " ":
            identifier = identifier[:2] + identifier[3:]

        if identifier in self._team:
            return self._team[identifier]
        elif identifier in self._opponent_team:
            return self._opponent_team[identifier]

        player_role = identifier[:2]
        is_mine = player_role == self._player_role

        if is_mine or force_self_team:
            team: Dict[str, Pokemon] = self._team
        else:
            team: Dict[str, Pokemon] = self._opponent_team

        if self._team_size and len(team) >= self._team_size[player_role]:
            raise ValueError(
                "%s's team already has %d pokemons: cannot add %s to %s"
                % (
                    player_role,
                    self._team_size[player_role],
                    identifier,
                    ", ".join(team.keys()),
                )
            )

        if request:
            team[identifier] = Pokemon(request_pokemon=request, gen=self._data.gen)
        elif details:
            team[identifier] = Pokemon(details=details, gen=self._data.gen)
        else:
            species = identifier[4:]
            team[identifier] = Pokemon(species=species, gen=self._data.gen)

        return team[identifier]

    @abstractmethod
    def _clear_all_boosts(self):  # pragma: no cover
        pass

    def _check_damage_message_for_item(self, split_message: List[str]):
        # Catches when a side takes damage from the opponent's item
        # The item belongs to the side not taking damage
        # Example:
        #   |-damage|p2a: Archeops|88/100|[from] item: Rocky Helmet|[of] p1a: Ferrothorn
        if (
            len(split_message) == 6
            and split_message[4].startswith("[from] item:")
            and split_message[5].startswith("[of]")
        ):
            item = split_message[4].split("item:")[-1]
            pkmn = split_message[5].split("[of]")[-1].strip()
            self.get_pokemon(pkmn).item = to_id_str(item)

        # Catches when a side takes damage from it's own item
        # The item belongs to the same side taking damage
        # Example:
        #   |-damage|p2a: Pikachu|90/100|[from] item: Life Orb
        elif len(split_message) == 5 and split_message[4].startswith("[from] item:"):
            item = split_message[4].split("item:")[-1]
            pkmn = split_message[2]
            self.get_pokemon(pkmn).item = to_id_str(item)

    def _check_damage_message_for_ability(self, split_message: List[str]):
        # Catches when a side takes damage from the opponent's ability
        # the item is from the side not taking damage
        # Example:
        #   |-damage|p2a: Archeops|88/100|[from] ability: Iron Barbs|[of] p1a: Ferrothorn
        if (
            len(split_message) == 6
            and split_message[4].startswith("[from] ability:")
            and split_message[5].startswith("[of]")
        ):
            ability = split_message[4].split("ability:")[-1]
            pkmn = split_message[5].split("[of]")[-1].strip()
            self.get_pokemon(pkmn).ability = to_id_str(ability)

    def _check_heal_message_for_item(self, split_message: List[str]):
        # Catches when a side heals from it's own item
        # the check for item is not None is necessary because the PS simulator will
        #  show the heal message AFTER a berry has already been consumed
        # Examples:
        #  |-heal|p2a: Quagsire|100/100|[from] item: Leftovers
        #  |-heal|p2a: Quagsire|100/100|[from] item: Sitrus Berry
        if len(split_message) == 5 and split_message[4].startswith("[from] item:"):
            pkmn = split_message[2]
            item = split_message[4].split("item:")[-1]
            pkmn_object = self.get_pokemon(pkmn)
            if pkmn_object.item is not None:
                pkmn_object.item = to_id_str(item)

    def _check_heal_message_for_ability(self, split_message: List[str]):
        # Catches when a side heals from it's own ability
        # the "of" component sent by the PS server is a bit misleading
        #   it implies the ability is from the opposite side
        # Example:
        #   |-heal|p2a: Quagsire|100/100|[from] ability: Water Absorb|[of] p1a: Genesect
        if len(split_message) == 6 and split_message[4].startswith("[from] ability:"):
            ability = split_message[4].split("ability:")[-1]
            pkmn = split_message[2]
            self.get_pokemon(pkmn).ability = to_id_str(ability)

    @abstractmethod
    def _end_illusion(self, pokemon_name: str, details: str):  # pragma: no cover
        pass

    def _end_illusion_on(
        self, illusionist: str, illusioned: Optional[Pokemon], details: str
    ):
        if illusionist is None:
            raise ValueError("Cannot end illusion without an active pokemon.")
        if illusioned is None:
            raise ValueError("Cannot end illusion without an illusioned pokemon.")
        illusionist_mon = self.get_pokemon(illusionist, details=details)

        if illusionist_mon is illusioned:
            return illusionist_mon

        illusionist_mon._switch_in(details=details)
        illusionist_mon.status = illusioned.status
        illusionist_mon._set_hp(f"{illusioned.current_hp}/{illusioned.max_hp}")

        illusioned._was_illusionned()

        return illusionist_mon

    def _field_end(self, field):
        field = Field.from_showdown_message(field)
        if field is not Field._UNKNOWN:
            self._fields.pop(field)

    def _field_start(self, field):
        field = Field.from_showdown_message(field)

        if field.is_terrain:
            self._fields = {
                field: turn
                for field, turn in self._fields.items()
                if not field.is_terrain
            }

        self._fields[field] = self.turn

    def _finish_battle(self) -> None:
        if self._save_replays:
            if self._save_replays is True:
                folder = "replays"
            else:
                folder = str(self._save_replays)

            if not os.path.exists(folder):
                os.mkdir(folder)

            with open(
                os.path.join(
                    folder, f"{self._player_username} - {self.battle_tag}.html"
                ),
                "w+",
                encoding="utf-8",
            ) as f:
                formatted_replay = _REPLAY_TEMPLATE

                formatted_replay = formatted_replay.replace(
                    "{BATTLE_TAG}", f"{self.battle_tag}"
                )
                formatted_replay = formatted_replay.replace(
                    "{PLAYER_USERNAME}", f"{self._player_username}"
                )
                formatted_replay = formatted_replay.replace(
                    "{OPPONENT_USERNAME}", f"{self._opponent_username}"
                )
                replay_log = f">{self.battle_tag}" + "\n".join(
                    ["|".join(split_message) for split_message in self._replay_data]
                )
                formatted_replay = formatted_replay.replace("{REPLAY_LOG}", replay_log)

                f.write(formatted_replay)

        self._finished = True

    def _parse_message(self, split_message: List[str]) -> None:
        if self._save_replays:
            self._replay_data.append(split_message)

        if split_message[1] in self.MESSAGES_TO_IGNORE:
            return
        elif split_message[1] in ["drag", "switch"]:
            pokemon, details, hp_status = split_message[2:5]
            self._switch(pokemon, details, hp_status)
        elif split_message[1] == "-damage":
            pokemon, hp_status = split_message[2:4]
            self.get_pokemon(pokemon)._damage(hp_status)
            self._check_damage_message_for_item(split_message)
            self._check_damage_message_for_ability(split_message)
        elif split_message[1] == "move":
            failed = False
            override_move = None
            reveal_other_move = False

            for move_failed_suffix in ["[miss]", "[still]", "[notarget]"]:
                if split_message[-1] == move_failed_suffix:
                    split_message = split_message[:-1]
                    failed = True

            if split_message[-1] == "[notarget]":
                split_message = split_message[:-1]

            if split_message[-1].startswith("[spread]"):
                split_message = split_message[:-1]

            if split_message[-1] in {"[from]lockedmove", "[from]Pursuit", "[zeffect]"}:
                split_message = split_message[:-1]

            if split_message[-1].startswith("[anim]"):
                split_message = split_message[:-1]

            if split_message[-1].startswith("[from]move: "):
                override_move = split_message.pop()[12:]

                if override_move == "Sleep Talk":
                    # Sleep talk was used, but also reveals another move
                    reveal_other_move = True
                elif override_move in {"Copycat", "Metronome", "Nature Power"}:
                    pass
                else:
                    self.logger.warning(
                        "Unmanaged [from]move message received - move %s in cleaned up "
                        "message %s in battle %s turn %d",
                        override_move,
                        split_message,
                        self.battle_tag,
                        self.turn,
                    )

            if split_message[-1] == "null":
                split_message = split_message[:-1]

            if split_message[-1].startswith("[from]ability: "):
                revealed_ability = split_message.pop()[15:]
                pokemon = split_message[2]
                self.get_pokemon(pokemon).ability = revealed_ability

                if revealed_ability == "Magic Bounce":
                    return
                elif revealed_ability == "Dancer":
                    return
                else:
                    self.logger.warning(
                        "Unmanaged [from]ability: message received - ability %s in "
                        "cleaned up message %s in battle %s turn %d",
                        revealed_ability,
                        split_message,
                        self.battle_tag,
                        self.turn,
                    )
            if split_message[-1] == "[from]Magic Coat":
                return

            while split_message[-1] == "[still]":
                split_message = split_message[:-1]

            if split_message[-1] == "":
                split_message = split_message[:-1]

            if len(split_message) == 4:
                pokemon, move = split_message[2:4]
            elif len(split_message) == 5:
                pokemon, move, presumed_target = split_message[2:5]

                if len(presumed_target) > 4 and presumed_target[:4] in {
                    "p1: ",
                    "p2: ",
                    "p1a:",
                    "p1b:",
                    "p2a:",
                    "p2b:",
                }:
                    pass
                else:
                    self.logger.warning(
                        "Unmanaged move message format received - cleaned up message %s"
                        " in battle %s turn %d",
                        split_message,
                        self.battle_tag,
                        self.turn,
                    )
            else:
                pokemon, move, presumed_target = split_message[2:5]
                self.logger.warning(
                    "Unmanaged move message format received - cleaned up message %s in "
                    "battle %s turn %d",
                    split_message,
                    self.battle_tag,
                    self.turn,
                )

            # Check if a silent-effect move has occurred (Minimize) and add the effect

            if move.upper().strip() == "MINIMIZE":
                temp_pokemon = self.get_pokemon(pokemon)
                temp_pokemon._start_effect("MINIMIZE")

            if override_move:
                # Moves that can trigger this branch results in two `move` messages being sent.
                # We're setting use=False in the one (with the override) in order to prevent two pps from being used
                # incorrectly.
                self.get_pokemon(pokemon)._moved(
                    override_move, failed=failed, use=False
                )
            if override_move is None or reveal_other_move:
                self.get_pokemon(pokemon)._moved(move, failed=failed, use=False)
        elif split_message[1] == "cant":
            pokemon, _ = split_message[2:4]
            self.get_pokemon(pokemon)._cant_move()
        elif split_message[1] == "turn":
            self.end_turn(int(split_message[2]))
        elif split_message[1] == "-heal":
            pokemon, hp_status = split_message[2:4]
            self.get_pokemon(pokemon)._heal(hp_status)
            self._check_heal_message_for_ability(split_message)
            self._check_heal_message_for_item(split_message)
        elif split_message[1] == "-boost":
            pokemon, stat, amount = split_message[2:5]
            self.get_pokemon(pokemon)._boost(stat, int(amount))
        elif split_message[1] == "-weather":
            weather = split_message[2]
            if weather == "none":
                self._weather = {}
                return
            else:
                self._weather = {Weather.from_showdown_message(weather): self.turn}
        elif split_message[1] == "faint":
            pokemon = split_message[2]
            self.get_pokemon(pokemon)._faint()
        elif split_message[1] == "-unboost":
            pokemon, stat, amount = split_message[2:5]
            self.get_pokemon(pokemon)._boost(stat, -int(amount))
        elif split_message[1] == "-ability":
            pokemon, ability = split_message[2:4]
            self.get_pokemon(pokemon).ability = ability
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
                    self.opponent_can_dynamax = False
        elif split_message[1] == "-activate":
            target, effect = split_message[2:4]
            if target:
                self.get_pokemon(target)._start_effect(effect)
        elif split_message[1] == "-status":
            pokemon, status = split_message[2:4]
            self.get_pokemon(pokemon).status = status
        elif split_message[1] == "rule":
            self._rules.append(split_message[2])

        elif split_message[1] == "-clearallboost":
            self._clear_all_boosts()
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
            pokemon = split_message[2]
            team = (
                self.team if pokemon[:2] == self._player_role else self._opponent_team
            )
            for mon in team.values():
                mon._cure_status()
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
        elif split_message[1] == "-invertboost":
            pokemon = split_message[2]
            self.get_pokemon(pokemon)._invert_boosts()
        elif split_message[1] == "-item":
            pokemon, item = split_message[2:4]
            self.get_pokemon(pokemon).item = to_id_str(item)
        elif split_message[1] == "-mega":
            if not split_message[2].startswith(self._player_role):  # pyre-ignore
                self._opponent_can_mega_evolve = False  # pyre-ignore
            pokemon, megastone = split_message[2:4]
            self.get_pokemon(pokemon)._mega_evolve(megastone)
        elif split_message[1] == "-mustrecharge":
            pokemon = split_message[2]
            self.get_pokemon(pokemon).must_recharge = True
        elif split_message[1] == "-prepare":
            try:
                attacker, move, defender = split_message[2:5]
                defender = self.get_pokemon(defender)
                if to_id_str(move) == "skydrop":
                    defender._start_effect("Sky Drop")
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
        elif split_message[1] == "-swapboost":
            source, target, stats = split_message[2:5]
            source = self.get_pokemon(source)
            target = self.get_pokemon(target)
            for stat in stats.split(", "):
                source._boosts[stat], target._boosts[stat] = (
                    target._boosts[stat],
                    source._boosts[stat],
                )
        elif split_message[1] == "-transform":
            pokemon, into = split_message[2:4]
            self.get_pokemon(pokemon)._transform(self.get_pokemon(into))
        elif split_message[1] == "-zpower":
            if not split_message[2].startswith(self._player_role):  # pyre-ignore
                self._opponent_can_mega_z_move = False  # pyre-ignore

            pokemon = split_message[2]
            self.get_pokemon(pokemon)._used_z_move()
        elif split_message[1] == "clearpoke":
            self._in_team_preview = True
            for mon in self.team.values():
                mon._clear_active()
        elif split_message[1] == "gen":
            self._format = split_message[2]
        elif split_message[1] == "inactive":
            if "disconnected" in split_message[2]:
                self._anybody_inactive = True
            elif "reconnected" in split_message[2]:
                self._anybody_inactive = False
                self._reconnected = True
        elif split_message[1] == "player":
            if len(split_message) == 6:
                player, username, avatar, rating = split_message[2:6]
            else:
                if not self._anybody_inactive:
                    if self._reconnected:
                        self._reconnected = False
                    else:
                        raise RuntimeError(f"Invalid player message: {split_message}")
                return
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
        elif split_message[1] == "start":
            self._in_team_preview = False
        elif split_message[1] == "swap":
            pokemon, position = split_message[2:4]
            self._swap(pokemon, position)
        elif split_message[1] == "teamsize":
            player, number = split_message[2:4]
            number = int(number)
            self._team_size[player] = number
        elif split_message[1] in {"message", "-message"}:
            self.logger.info("Received message: %s", split_message[2])
        elif split_message[1] == "-immune":
            if len(split_message) == 4:
                mon, cause = split_message[2:]

                if cause.startswith("[from] ability:"):
                    ability = cause.replace("[from] ability:", "")
                    self.get_pokemon(mon).ability = to_id_str(ability)
        elif split_message[1] == "-swapsideconditions":
            self._side_conditions, self._opponent_side_conditions = (
                self._opponent_side_conditions,
                self._side_conditions,
            )
        elif split_message[1] == "title":
            player_1, player_2 = split_message[2].split(" vs. ")
            self.players = player_1, player_2
        elif split_message[1] == "-terastallize":
            pokemon, type_ = split_message[2:]
            pokemon = self.get_pokemon(pokemon)
            pokemon._terastallize(type_)

            if pokemon.terastallized:
                if pokemon in set(self.opponent_team.values()):
                    self._opponent_can_terrastallize = False
        else:
            raise NotImplementedError(split_message)

    @abstractmethod
    def _parse_request(self, request: Dict) -> None:  # pragma: no cover
        pass

    def _register_teampreview_pokemon(self, player: str, details: str):
        if player != self._player_role:
            mon = Pokemon(details=details, gen=self._data.gen)
            self._teampreview_opponent_team.add(mon)

    def _side_end(self, side, condition):
        if side[:2] == self._player_role:
            conditions = self.side_conditions
        else:
            conditions = self.opponent_side_conditions
        condition = SideCondition.from_showdown_message(condition)
        if condition is not SideCondition._UNKNOWN:
            conditions.pop(condition)

    def _side_start(self, side, condition):
        if side[:2] == self._player_role:
            conditions = self.side_conditions
        else:
            conditions = self.opponent_side_conditions
        condition = SideCondition.from_showdown_message(condition)
        if condition in STACKABLE_CONDITIONS:
            conditions[condition] = conditions.get(condition, 0) + 1
        elif condition not in conditions:
            conditions[condition] = self.turn

    def _swap(self, *args, **kwargs):
        self.logger.warning("swap method in Battle is not implemented")

    @abstractmethod
    def _switch(self, pokemon, details, hp_status):  # pragma: no cover
        pass

    def _tied(self):
        self._finish_battle()

    def _update_team_from_request(self, side: Dict) -> None:
        for pokemon in side["pokemon"]:
            if pokemon["ident"] in self._team:
                self._team[pokemon["ident"]]._update_from_request(pokemon)
            else:
                self.get_pokemon(
                    pokemon["ident"], force_self_team=True, request=pokemon
                )

    def _won_by(self, player_name: str):
        if player_name == self._player_username:
            self._won = True
        else:
            self._won = False
        self._finish_battle()

    def end_turn(self, turn: int) -> None:
        self.turn = turn

        for mon in self.all_active_pokemons:
            if mon:
                mon._end_turn()

    @property
    @abstractmethod
    def active_pokemon(self):  # pragma: no cover
        pass

    @abstractproperty
    def all_active_pokemons(self):  # pragma: no cover
        pass

    @property
    @abstractmethod
    def available_moves(self):  # pragma: no cover
        pass

    @property
    @abstractmethod
    def available_switches(self) -> List[Pokemon]:  # pragma: no cover
        pass

    @property
    def battle_tag(self) -> str:
        """
        :return: The battle identifier.
        :rtype: str
        """
        return self._battle_tag

    @property
    @abstractmethod
    def can_dynamax(self) -> bool:  # pragma: no cover
        pass

    @property
    @abstractmethod
    def can_mega_evolve(self):  # pragma: no cover
        pass

    @property
    @abstractmethod
    def can_z_move(self):  # pragma: no cover
        pass

    @property
    def dynamax_turns_left(self) -> Optional[int]:
        """
        :return: How many turns of dynamax are left. None if dynamax is not active
        :rtype: int, optional
        """
        if self._dynamax_turn is not None and any(
            map(lambda pokemon: pokemon.is_dynamaxed, self._team.values())
        ):
            return max(3 - (self.turn - self._dynamax_turn), 0)

    @property
    def fields(self) -> Dict[Field, int]:
        """
        :return: A dict mapping fields to the turn they have been activated.
        :rtype: Dict[Field, int]
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
    @abstractmethod
    def force_switch(self):  # pragma: no cover
        pass

    @property
    def lost(self) -> Optional[bool]:
        """
        :return: If the battle is finished, a boolean indicating whether the battle is
            lost. Otherwise None.
        :rtype: Optional[bool]
        """
        return None if self._won is None else not self._won

    @property
    def max_team_size(self) -> Optional[int]:
        """
        :return: The maximum acceptable size of the team to return in teampreview, if
            applicable.
        :rtype: int, optional
        """
        return self._max_team_size

    @property
    @abstractmethod
    def maybe_trapped(self):  # pragma: no cover
        pass

    @property
    @abstractmethod
    def opponent_active_pokemon(self):  # pragma: no cover
        pass

    @property
    @abstractmethod
    def opponent_can_dynamax(self) -> bool:  # pragma: no cover
        pass

    @opponent_can_dynamax.setter
    @abstractmethod
    def opponent_can_dynamax(self, value) -> None:  # pragma: no cover
        pass

    @property
    def opponent_dynamax_turns_left(self) -> Optional[int]:
        """
        :return: How many turns of dynamax are left for the opponent's pokemon.
            None if dynamax is not active
        :rtype: Optional[int]
        """
        if self._opponent_dynamax_turn is not None and any(
            map(lambda pokemon: pokemon.is_dynamaxed, self._opponent_team.values())
        ):
            return max(3 - (self.turn - self._opponent_dynamax_turn), 0)

    @property
    def opponent_role(self) -> Optional[str]:
        """
        :return: Opponent's role in given battle. p1/p2
        :rtype: str, optional
        """
        if self.player_role == "p1":
            return "p2"
        if self.player_role == "p2":
            return "p1"

    @property
    def opponent_side_conditions(self) -> Dict[SideCondition, int]:
        """
        :return: The opponent's side conditions. Keys are SideCondition objects, values
            are:

            - the number of layers of the SideCondition if the side condition is
                stackable
            - the turn where the SideCondition was setup otherwise
        :rtype: Dict[SideCondition, int]
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
    def player_role(self) -> Optional[str]:
        """
        :return: Player's role in given battle. p1/p2
        :rtype: str, optional
        """
        return self._player_role

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
    def side_conditions(self) -> Dict[SideCondition, int]:
        """
        :return: The player's side conditions. Keys are SideCondition objects, values
            are:

            - the number of layers of the side condition if the side condition is
                stackable
            - the turn where the SideCondition was setup otherwise
        :rtype: Dict[SideCondition, int]
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
    @abstractmethod
    def trapped(self):  # pragma: no cover
        pass

    @trapped.setter
    @abstractmethod
    def trapped(self, value):  # pragma: no cover
        pass

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
    def weather(self) -> Dict[Weather, int]:
        """
        :return: A dict mapping the battle's weather (if any) to its starting turn
        :rtype: Dict[Weather, int]
        """
        return self._weather

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

    @property
    def reviving(self) -> bool:
        return self._reviving
