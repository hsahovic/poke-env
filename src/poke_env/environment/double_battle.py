# -*- coding: utf-8 -*-

from aiologger import Logger  # pyre-ignore
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

from poke_env.environment.abstract_battle import AbstractBattle
from poke_env.environment.move import Move
from poke_env.environment.pokemon import Pokemon
from poke_env.environment.move import special_moves
from poke_env.environment.move_category import MoveCategory


class DoubleBattle(AbstractBattle):
    POKEMON_1_POSITION = -1
    POKEMON_2_POSITION = -2
    OPPONENT_1_POSITION = 1
    OPPONENT_2_POSITION = 2
    ALL_TARGETS_POSITION = 0  # symbolic, not used by showdown

    def __init__(self, battle_tag: str, username: str, logger: Logger):  # pyre-ignore
        super(DoubleBattle, self).__init__(battle_tag, username, logger)

        # Turn choice attributes
        self._available_moves: List[List[Move]] = [[], []]
        self._can_mega_evolve: List[bool] = [False, False]
        self._can_z_move: List[bool] = [False, False]
        self._can_dynamax: List[bool] = [False, False]
        self._opponent_can_dynamax: List[bool] = [True, True]
        self._force_switch: List[bool] = [False, False]
        self._maybe_trapped: List[bool] = [False, False]
        self._trapped: List[bool] = [False, False]
        self._force_swap: List[bool] = [False, False]

        # Battle state attributes
        self._active_pokemon: Dict[str, Pokemon] = {}
        self._opponent_active_pokemon: Dict[str, Pokemon] = {}

        # Other
        self._move_to_pokemon_id: Dict[Move, str] = {}

    def _clear_all_boosts(self):
        for active_pokemon_group in (self.active_pokemon, self.opponent_active_pokemon):
            for active_pokemon in active_pokemon_group:
                active_pokemon._clear_boosts()

    def _end_illusion(self, pokemon_name: str, details: str):
        player_identifier = pokemon_name[:2]
        pokemon_identifier = pokemon_name[:3]
        if player_identifier == self._player_role:
            active = self._active_pokemon.get(pokemon_identifier)
        else:
            active = self._opponent_active_pokemon.get(pokemon_identifier)

        if active is None:
            raise ValueError("Cannot end illusion without an active pokemon.")

        pokemon = self.get_pokemon(pokemon_name, details=details)
        pokemon._set_hp(f"{active.current_hp}/{active.max_hp}")
        active._was_illusionned()
        pokemon._switch_in()
        pokemon.status = active.status

    def _get_pokemon_id_for_move(self, move: Move) -> str:
        cached_pokemon_id = self._move_to_pokemon_id.get(move)
        if cached_pokemon_id is not None:
            return cached_pokemon_id
        all_battle_active_pokemon = {}
        all_battle_active_pokemon.update(self._active_pokemon)
        all_battle_active_pokemon.update(self._opponent_active_pokemon)
        for pokemon_id, pokemon in all_battle_active_pokemon.items():
            for pokemon_move in pokemon.moves.values():
                if pokemon_move is move:
                    self._move_to_pokemon_id[move] = pokemon_id
                    return pokemon_id
        raise Exception(
            f"Selected move {move.id} is not owned by any Pokemon that is currently "
            f"battling"
        )

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

        self._available_moves = [[], []]
        self._available_switches = []
        self._can_mega_evolve = [False, False]
        self._can_z_move = [False, False]
        self._can_dynamax = [False, False]
        self._maybe_trapped = [False, False]
        self._trapped = [False, False]
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

        side = request["side"]
        self._update_team_from_request(side)

        if "active" in request:
            for active_pokemon_number, active_request in enumerate(request["active"]):
                pokemon_dict = request["side"]["pokemon"][active_pokemon_number]
                active_pokemon = self.get_pokemon(
                    pokemon_dict["ident"],
                    force_self_team=True,
                    details=pokemon_dict["details"],
                )
                if active_request.get("trapped"):
                    self._trapped[active_pokemon_number] = True

                for move in active_request["moves"]:
                    if not move.get("disabled", False):
                        if move["id"] in active_pokemon.moves:
                            self._available_moves[active_pokemon_number].append(
                                active_pokemon.moves[move["id"]]
                            )
                        elif move["id"] in special_moves:
                            self._available_moves[active_pokemon_number].append(
                                special_moves[move["id"]]
                            )
                        else:
                            try:
                                if not {
                                    "copycat",
                                    "metronome",
                                    "mefirst",
                                    "mirrormove",
                                    "assist",
                                }.intersection(active_pokemon.moves.keys()):
                                    self.logger.critical(
                                        "An error occured in battle %s while adding "
                                        "available moves. The move '%s' was either "
                                        "unknown or not available for the active "
                                        "pokemon: %s",
                                        self.battle_tag,
                                        move["id"],
                                        active_pokemon.species,
                                    )
                                else:
                                    self.logger.warning(
                                        "The move '%s' was received in battle %s for "
                                        "your active pokemon %s. This move could not "
                                        "be added, but it might come from a special "
                                        "move such as copycat or me first. If that is "
                                        "not the case, please make sure there is an "
                                        "explanation for this behavior or report it "
                                        "if it is an error.",
                                        move["id"],
                                        self.battle_tag,
                                        active_pokemon.species,
                                    )
                                move = Move(move["id"])
                                self._available_moves[active_pokemon_number].append(
                                    move
                                )
                            except AttributeError:
                                pass

                if active_request.get("canMegaEvo", False):
                    self._can_mega_evolve[active_pokemon_number] = True
                if active_request.get("canZMove", False):
                    self._can_z_move[active_pokemon_number] = True
                if active_request.get("canDynamax", False):
                    self._can_dynamax[active_pokemon_number] = True
                if active_request.get("maybeTrapped", False):
                    self._maybe_trapped[active_pokemon_number] = True

        if side["pokemon"]:
            self._player_role = side["pokemon"][0]["ident"][:2]

        if not self.trapped:
            for pokemon in side["pokemon"]:
                if pokemon:
                    pokemon = self._team[pokemon["ident"]]
                    if not pokemon.active and not pokemon.fainted:
                        self._available_switches.append(pokemon)

    def _switch(self, pokemon, details, hp_status):
        pokemon_identifier = pokemon.split(":")[0][:3]
        player_identifier = pokemon_identifier[:2]
        team = (
            self._active_pokemon
            if player_identifier == self._player_role
            else self._opponent_active_pokemon
        )
        pokemon_out = team.pop(pokemon_identifier, None)
        if pokemon_out is not None:
            pokemon_out._switch_out()
        pokemon_in = self.get_pokemon(pokemon, details=details)
        pokemon_in._switch_in()
        pokemon_in._set_hp_status(hp_status)
        team[pokemon_identifier] = pokemon_in

    def get_possible_showdown_targets(self, move: Move, dynamax=False) -> List[int]:
        pokemon_id = self._get_pokemon_id_for_move(move)
        move_target = move.target
        pokemon = (
            self._active_pokemon.get(pokemon_id)
            or self._opponent_active_pokemon[pokemon_id]
        )

        if pokemon_id[-1] == "a":
            self_position = self.POKEMON_1_POSITION
            ally_position = self.POKEMON_2_POSITION
        else:
            self_position = self.POKEMON_2_POSITION
            ally_position = self.POKEMON_1_POSITION

        if dynamax or pokemon.is_dynamaxed:
            if move.category == MoveCategory.STATUS:
                return [self_position]
            return [self.OPPONENT_1_POSITION, self.OPPONENT_2_POSITION]

        if move.non_ghost_target:  # changing target to "self" in case of Curse
            from poke_env.environment.pokemon_type import PokemonType

            if PokemonType.GHOST in pokemon.types:
                move_target = "self"

        targets = {
            "adjacentAlly": [ally_position],
            "adjacentAllyOrSelf": [ally_position, self_position],
            "adjacentFoe": [self.OPPONENT_1_POSITION, self.OPPONENT_2_POSITION],
            "all": [self.ALL_TARGETS_POSITION],
            "allAdjacent": [self.ALL_TARGETS_POSITION],
            "allAdjacentFoes": [self.ALL_TARGETS_POSITION],
            "allies": [self.ALL_TARGETS_POSITION],
            "allySide": [self.ALL_TARGETS_POSITION],
            "allyTeam": [self.ALL_TARGETS_POSITION],
            "any": [ally_position, self.OPPONENT_1_POSITION, self.OPPONENT_2_POSITION],
            "foeSide": [self.ALL_TARGETS_POSITION],
            "normal": [
                ally_position,
                self.OPPONENT_1_POSITION,
                self.OPPONENT_2_POSITION,
            ],
            "randomNormal": [self.ALL_TARGETS_POSITION],
            "scripted": [self.ALL_TARGETS_POSITION],
            "self": [self.ALL_TARGETS_POSITION],
        }[move_target]

        pokemon_ids = set(self._opponent_active_pokemon.keys())
        pokemon_ids.update(self._active_pokemon.keys())
        targets_to_keep = {
            {
                f"{self.player_role}a": -1,
                f"{self.player_role}b": -2,
                f"{self.opponent_role}a": 1,
                f"{self.opponent_role}b": 2,
            }[pokemon_identifier]
            for pokemon_identifier in pokemon_ids
        }
        targets_to_keep.add(self.ALL_TARGETS_POSITION)
        targets = [target for target in targets if target in targets_to_keep]

        return targets

    @property
    def active_pokemon(self) -> Tuple[Pokemon, ...]:
        """
        :return: The active pokemon
        :rtype: a tuple of one/two Pokemon
        """
        active_pokemon = tuple(
            pokemon for pokemon in self.team.values() if pokemon.active
        )
        if len(active_pokemon) > 0:
            return active_pokemon
        raise ValueError("No active pokemon found in the current team")

    @property
    def available_moves(self) -> List[List[Move]]:
        """
        :return: A list of two lists of moves the player can use during the current
            move request for each Pokemon.
        :rtype: List[List[Move]]
        """
        return self._available_moves

    @property
    def can_dynamax(self) -> List[bool]:
        """
        :return: Wheter of not the current active pokemon can dynamax
        :rtype: List[bool]
        """
        return self._can_dynamax

    @property
    def can_mega_evolve(self) -> List[bool]:
        """
        :return: Whether of not either current active pokemon can mega evolve.
        :rtype: List[bool]
        """
        return self._can_mega_evolve

    @property
    def can_z_move(self) -> List[bool]:
        """
        :return: Wheter of not the current active pokemon can z-move.
        :rtype: List[bool]
        """
        return self._can_z_move

    @property
    def force_switch(self) -> List[bool]:
        """
        :return: A boolean indicating whether the active pokemon is forced
            to switch out.
        :rtype: List[bool]
        """
        return self._force_switch

    @property
    def maybe_trapped(self) -> List[bool]:
        """
        :return: A boolean indicating whether either active pokemon is maybe trapped
            by the opponent.
        :rtype: List[bool]
        """
        return self._maybe_trapped

    @property
    def opponent_active_pokemon(self) -> Optional[Tuple[Pokemon, ...]]:
        """
        :return: The opponent active pokemon (one or two).
        :rtype: Optional[Tuple[Pokemon, ...]]
        """
        active_pokemon = tuple(
            pokemon for pokemon in self.opponent_team.values() if pokemon.active
        )
        if len(active_pokemon) > 0:
            return active_pokemon
        raise ValueError("No active pokemon found in the current team")

    @property
    def opponent_can_dynamax(self) -> List[bool]:
        """
        :return: Wheter of not opponent's current active pokemon can dynamax
        :rtype: List[bool]
        """
        return self._opponent_can_dynamax

    @opponent_can_dynamax.setter
    def opponent_can_dynamax(self, value: Union[bool, List[bool]]) -> None:
        if isinstance(value, bool):
            self._opponent_can_dynamax = [value, value]
        else:
            self._opponent_can_dynamax = value

    @property
    def trapped(self) -> List[bool]:
        """
        :return: A boolean indicating whether either active pokemon is trapped by the
            opponent.
        :rtype: List[bool]
        """
        return self._trapped

    @trapped.setter
    def trapped(self, value: List[bool]):
        self._trapped = value
