from logging import Logger
from typing import Any, Dict, List, Optional, Union

from poke_env.battle.abstract_battle import AbstractBattle
from poke_env.battle.move import SPECIAL_MOVES, Move
from poke_env.battle.move_category import MoveCategory
from poke_env.battle.pokemon import Pokemon
from poke_env.battle.pokemon_type import PokemonType
from poke_env.battle.target import Target
from poke_env.player.battle_order import (
    DefaultBattleOrder,
    PassBattleOrder,
    SingleBattleOrder,
)


class DoubleBattle(AbstractBattle):
    POKEMON_1_POSITION = -1
    POKEMON_2_POSITION = -2
    OPPONENT_1_POSITION = 1
    OPPONENT_2_POSITION = 2
    EMPTY_TARGET_POSITION = 0  # symbolic, not used by showdown

    def __init__(
        self,
        battle_tag: str,
        username: str,
        logger: Logger,
        gen: int,
        save_replays: Union[str, bool] = False,
    ):
        super(DoubleBattle, self).__init__(
            battle_tag, username, logger, save_replays, gen=gen
        )

        # Turn choice attributes
        self._available_moves: List[List[Move]] = [[], []]
        self._available_switches: List[List[Pokemon]] = [[], []]
        self._can_dynamax: List[bool] = [False, False]
        self._can_mega_evolve: List[bool] = [False, False]
        self._can_tera: List[bool] = [False, False]
        self._can_z_move: List[bool] = [False, False]
        self._force_switch: List[bool] = [False, False]
        self._maybe_trapped: List[bool] = [False, False]
        self._trapped: List[bool] = [False, False]

        # Battle state attributes
        self._active_pokemon: Dict[str, Pokemon] = {}
        self._opponent_active_pokemon: Dict[str, Pokemon] = {}

        # Other
        self._move_to_pokemon_id: Dict[Move, str] = {}

    def clear_all_boosts(self):
        for active_pokemon_group in (self.active_pokemon, self.opponent_active_pokemon):
            for active_pokemon in active_pokemon_group:
                if active_pokemon is not None:
                    active_pokemon.clear_boosts()

    def end_illusion(self, pokemon_name: str, details: str):
        player_identifier = pokemon_name[:2]
        pokemon_identifier = pokemon_name[:3]
        if player_identifier == self._player_role:
            active_dict = self._active_pokemon
        else:
            active_dict = self._opponent_active_pokemon
        active = active_dict.get(pokemon_identifier)

        active_dict[pokemon_identifier] = self._end_illusion_on(
            illusioned=active, illusionist=pokemon_name, details=details
        )

    @staticmethod
    def _get_active_pokemon(
        active_pokemon: Dict[str, Pokemon], role: str
    ) -> List[Optional[Pokemon]]:
        pokemon_1 = active_pokemon.get(f"{role}a")
        pokemon_2 = active_pokemon.get(f"{role}b")
        if pokemon_1 is None or not pokemon_1.active or pokemon_1.fainted:
            pokemon_1 = None
        if pokemon_2 is None or not pokemon_2.active or pokemon_2.fainted:
            pokemon_2 = None
        return [pokemon_1, pokemon_2]

    def parse_request(self, request: Dict[str, Any]) -> None:
        """
        Update the object from a request.
        The player's pokemon are all updated, as well as available moves, switches and
        other related information (z move, mega evolution, forced switch...).

        :param request: Parsed JSON request object.
        :type request: dict
        """
        if self.logger is not None:
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
        self._available_switches = [[], []]
        self._can_mega_evolve = [False, False]
        self._can_z_move = [False, False]
        self._can_dynamax = [False, False]
        self._can_tera = [False, False]
        self._maybe_trapped = [False, False]
        self._trapped = [False, False]
        self._force_switch = request.get("forceSwitch", [False, False])
        self._reviving = any(
            [mon.get("reviving") for mon in request["side"]["pokemon"]]
        )

        self._last_request = request

        if request.get("teamPreview", False):
            self._teampreview = True
            number_of_mons = len(request["side"]["pokemon"])
            self._max_team_size = request.get("maxTeamSize", number_of_mons)
        else:
            self._teampreview = False

        side = request["side"]
        if side["pokemon"]:
            self._player_role = side["pokemon"][0]["ident"][:2]
        self._update_team_from_request(side)

        if "active" in request:
            for active_pokemon_number, active_request in enumerate(request["active"]):
                pokemon_dict = request["side"]["pokemon"][active_pokemon_number]
                active_pokemon = self.get_pokemon(
                    pokemon_dict["ident"],
                    force_self_team=True,
                    details=pokemon_dict["details"],
                )
                if self.player_role is not None:
                    if (
                        active_pokemon_number == 0
                        and f"{self.player_role}a" not in self._active_pokemon
                    ):
                        self._active_pokemon[f"{self.player_role}a"] = active_pokemon
                    elif f"{self.player_role}b" not in self._active_pokemon:
                        self._active_pokemon[f"{self.player_role}b"] = active_pokemon
                    elif (
                        active_pokemon_number == 0
                        and self._active_pokemon[f"{self.player_role}a"].fainted
                        and self._active_pokemon[f"{self.player_role}b"]
                        == active_pokemon
                    ):
                        (
                            self._active_pokemon[f"{self.player_role}a"],
                            self._active_pokemon[f"{self.player_role}b"],
                        ) = (
                            self._active_pokemon[f"{self.player_role}b"],
                            self._active_pokemon[f"{self.player_role}a"],
                        )
                    elif (
                        active_pokemon_number == 1
                        and self._active_pokemon[f"{self.player_role}b"].fainted
                        and not active_pokemon.fainted
                        and self._active_pokemon[f"{self.player_role}a"]
                        == active_pokemon
                    ):
                        (
                            self._active_pokemon[f"{self.player_role}a"],
                            self._active_pokemon[f"{self.player_role}b"],
                        ) = (
                            self._active_pokemon[f"{self.player_role}b"],
                            self._active_pokemon[f"{self.player_role}a"],
                        )

                if active_pokemon.fainted:
                    continue

                if active_request.get("trapped"):
                    self._trapped[active_pokemon_number] = True

                # TODO: the illusion handling here works around Zoroark's
                # difficulties. This should be properly handled at some point.
                try:
                    self._available_moves[active_pokemon_number] = (
                        active_pokemon.available_moves_from_request(active_request)
                    )
                except AssertionError as e:
                    if "illusion" not in [p.ability for p in self.team.values()]:
                        raise e

                if active_request.get("canMegaEvo", False):
                    self._can_mega_evolve[active_pokemon_number] = True
                if active_request.get("canZMove", False):
                    self._can_z_move[active_pokemon_number] = True
                if active_request.get("canDynamax", False):
                    self._can_dynamax[active_pokemon_number] = True
                if active_request.get("canTerastallize", False):
                    self._can_tera[active_pokemon_number] = True
                if active_request.get("maybeTrapped", False):
                    self._maybe_trapped[active_pokemon_number] = True

        for i in range(2):
            if not self.trapped[i]:
                for pkmn_json in side["pokemon"]:
                    pokemon = self.team[pkmn_json["ident"]]
                    if not pokemon.active and self.reviving == pokemon.fainted:
                        self._available_switches[i].append(pokemon)

    def switch(self, pokemon_str: str, details: str, hp_status: str):
        pokemon_identifier = pokemon_str.split(":")[0][:3]
        player_identifier = pokemon_identifier[:2]
        team = (
            self._active_pokemon
            if player_identifier == self._player_role
            else self._opponent_active_pokemon
        )
        pokemon_out = team.pop(pokemon_identifier, None)
        if pokemon_out is not None:
            pokemon_out.switch_out()
        pokemon_in = self.get_pokemon(pokemon_str, details=details)
        pokemon_in.switch_in()
        pokemon_in.set_hp_status(hp_status)
        team[pokemon_identifier] = pokemon_in

        # Keeps battle.team in sync with Showdown order
        if player_identifier == self.player_role and pokemon_out is not None:
            keys = list(self.team.keys())
            index1 = 0 if pokemon_identifier[2] == "a" else 1
            assert self._player_role is not None
            index2 = keys.index(pokemon_in.identifier(self._player_role))
            keys[index1], keys[index2] = keys[index2], keys[index1]
            self.team = {k: self.team[k] for k in keys}

    def _swap(self, pokemon_str: str, slot: str):
        player_identifier = pokemon_str.split(":")[0][:2]
        active = (
            self._active_pokemon
            if player_identifier == self.player_role
            else self._opponent_active_pokemon
        )
        slot_a = f"{player_identifier}a"
        slot_b = f"{player_identifier}b"

        if active[slot_a].fainted or active[slot_b].fainted:
            return

        slot_a_mon = active[slot_a]
        slot_b_mon = active[slot_b]

        pokemon = self.get_pokemon(pokemon_str)

        if (slot == "0" and pokemon == slot_a_mon) or (
            slot == "1" and pokemon == slot_b_mon
        ):
            pass
        else:
            active[slot_a], active[slot_b] = active[slot_b], active[slot_a]

        # Need to keep battle.team in sync with Showdown order
        if player_identifier == self.player_role:
            keys = list(self.team.keys())
            keys[0], keys[1] = keys[1], keys[0]
            self.team = {k: self.team[k] for k in keys}

    def get_possible_showdown_targets(
        self, move: Move, pokemon: Pokemon, dynamax: bool = False
    ) -> List[int]:
        """
        Given move of an ALLY Pokemon, returns a list of possible Pokemon Showdown
        targets for it. This is smart enough so that it figures whether the Pokemon
        is already dynamaxed.

        :param move: Move instance for which possible targets should be returned
        :type move: Move
        :param pokemon: The ally using the move.
        :type pokemon: Pokemon
        :param dynamax: whether given move also STARTS dynamax for its user
        :return: a list of integers indicating Pokemon Showdown targets:
            -1, -2, 1, 2 or self.EMPTY_TARGET_POSITION that indicates "no target"
        :rtype: List[int]
        """
        if move.id in SPECIAL_MOVES:
            return [self.EMPTY_TARGET_POSITION]

        pokemon_1, pokemon_2 = self.active_pokemon
        if pokemon == pokemon_1 and move in self.available_moves[0]:
            self_position = self.POKEMON_1_POSITION
            ally_position = self.POKEMON_2_POSITION
        elif pokemon == pokemon_2 and move in self.available_moves[1]:
            self_position = self.POKEMON_2_POSITION
            ally_position = self.POKEMON_1_POSITION
        else:
            raise Exception(
                f"Selected move {move.id} is not owned by any active ally Pokemon "
                f"that is currently battling"
            )

        if dynamax or pokemon.is_dynamaxed:
            if move.category == MoveCategory.STATUS:
                targets = [self.EMPTY_TARGET_POSITION]
            else:
                targets = [self.OPPONENT_1_POSITION, self.OPPONENT_2_POSITION]
        elif move.non_ghost_target and (
            PokemonType.GHOST not in pokemon.types
        ):  # fixing target for Curse
            return [self.EMPTY_TARGET_POSITION]
        elif move.id == "terastarstorm" and pokemon.type_1 == PokemonType.STELLAR:
            targets = [self.EMPTY_TARGET_POSITION]
        else:
            targets = {
                Target.from_showdown_message("adjacentAlly"): [ally_position],
                Target.from_showdown_message("adjacentAllyOrSelf"): [
                    ally_position,
                    self_position,
                ],
                Target.from_showdown_message("adjacentFoe"): [
                    self.OPPONENT_1_POSITION,
                    self.OPPONENT_2_POSITION,
                ],
                Target.from_showdown_message("all"): [self.EMPTY_TARGET_POSITION],
                Target.from_showdown_message("allAdjacent"): [
                    self.EMPTY_TARGET_POSITION
                ],
                Target.from_showdown_message("allAdjacentFoes"): [
                    self.EMPTY_TARGET_POSITION
                ],
                Target.from_showdown_message("allies"): [self.EMPTY_TARGET_POSITION],
                Target.from_showdown_message("allySide"): [self.EMPTY_TARGET_POSITION],
                Target.from_showdown_message("allyTeam"): [self.EMPTY_TARGET_POSITION],
                Target.from_showdown_message("any"): [
                    ally_position,
                    self.OPPONENT_1_POSITION,
                    self.OPPONENT_2_POSITION,
                ],
                Target.from_showdown_message("foeSide"): [self.EMPTY_TARGET_POSITION],
                Target.from_showdown_message("normal"): [
                    ally_position,
                    self.OPPONENT_1_POSITION,
                    self.OPPONENT_2_POSITION,
                ],
                Target.from_showdown_message("randomNormal"): [
                    self.EMPTY_TARGET_POSITION
                ],
                Target.from_showdown_message("scripted"): [self.EMPTY_TARGET_POSITION],
                Target.from_showdown_message("self"): [self.EMPTY_TARGET_POSITION],
                self.EMPTY_TARGET_POSITION: [self.EMPTY_TARGET_POSITION],
                None: [self.OPPONENT_1_POSITION, self.OPPONENT_2_POSITION],
            }[move.deduced_target]

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
        targets_to_keep.add(self.EMPTY_TARGET_POSITION)
        targets = [target for target in targets if target in targets_to_keep]

        return targets

    def to_showdown_target(self, move: Move, target_mon: Optional[Pokemon]) -> int:
        """Returns the correct Showdown target of the Pokemon to be targeted.
        It will return 0 if no target is needed or if the target_mon is not
        an active pokemon; this is meaningless in showdown

        :param move: the move to be used against the target_mon
        :type move: Move
        :param target_mon: the Pokemon that is to be targeted
        :type target_mon: as implemented in poke-env
        :return: The corresponding showdown target if needed, otherwise 0
        :rtype: int
        """

        if (
            move.target
            and move.target in (Target.ANY, Target.NORMAL, Target.ADJACENT_FOE)
            and target_mon is not None
        ):
            if target_mon == self.active_pokemon[0]:
                return self.POKEMON_1_POSITION
            elif target_mon == self.active_pokemon[1]:
                return self.POKEMON_2_POSITION
            elif target_mon == self.opponent_active_pokemon[0]:
                return self.OPPONENT_1_POSITION
            else:
                return self.OPPONENT_2_POSITION

        # No need to return a target for each of the other target types
        else:
            return self.EMPTY_TARGET_POSITION

    @property
    def active_pokemon(self) -> List[Optional[Pokemon]]:
        """
        :return: The active pokemon, always at least one is not None
        :rtype: List[Optional[Pokemon]]
        """
        if self.player_role is None:
            raise ValueError("Unable to get active_pokemon, player_role is None")
        return self._get_active_pokemon(self._active_pokemon, self.player_role)

    @property
    def all_active_pokemons(self) -> List[Optional[Pokemon]]:
        """
        :return: A list containing all active pokemons and/or Nones.
        :rtype: List[Optional[Pokemon]]
        """
        return [*self.active_pokemon, *self.opponent_active_pokemon]

    @property
    def available_moves(self) -> List[List[Move]]:
        """
        :return: A list of two lists of moves the player can use during the current
            move request for each Pokemon.
        :rtype: List[List[Move]]
        """
        return self._available_moves

    @property
    def available_switches(self) -> List[List[Pokemon]]:
        """
        :return: The list of two lists of switches the player can do during the
            current move request for each active pokemon
        :rtype: List[List[Pokemon]]
        """
        return self._available_switches

    @property
    def can_dynamax(self) -> List[bool]:
        """
        :return: Whether or not the current active pokemon can dynamax
        :rtype: List[bool]
        """
        return self._can_dynamax

    @property
    def can_mega_evolve(self) -> List[bool]:
        """
        :return: Whether or not either current active pokemon can mega evolve.
        :rtype: List[bool]
        """
        return self._can_mega_evolve

    @property
    def can_tera(self) -> List[bool]:
        """
        :return: Whether or not the current active pokemon can terastallize. If yes, will be a PokemonType.
        :rtype: List[Union[bool, PokemonType]]
        """
        return self._can_tera

    @property
    def can_z_move(self) -> List[bool]:
        """
        :return: Whether or not the current active pokemon can z-move.
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
    def grounded(self) -> List[bool]:
        """
        :return: A boolean indicating whether the active pokemon are grounded
        :rtype: List[bool]
        """
        return [self.is_grounded(mon) if mon else True for mon in self.active_pokemon]

    @property
    def maybe_trapped(self) -> List[bool]:
        """
        :return: A boolean indicating whether either active pokemon is maybe trapped
            by the opponent.
        :rtype: List[bool]
        """
        return self._maybe_trapped

    @property
    def opponent_active_pokemon(self) -> List[Optional[Pokemon]]:
        """
        :return: The opponent active pokemon, always at least one is not None
        :rtype: List[Optional[Pokemon]]
        """
        if self.opponent_role is None:
            raise ValueError(
                "Unable to get opponent_active_pokemon, opponent_role is None"
            )
        return self._get_active_pokemon(
            self._opponent_active_pokemon, self.opponent_role
        )

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

    @property
    def valid_orders(self) -> List[List[SingleBattleOrder]]:
        orders: List[List[SingleBattleOrder]] = [[], []]
        if self._wait:
            return [[DefaultBattleOrder()], [DefaultBattleOrder()]]
        for i in range(2):
            if any(self.force_switch) and not self.force_switch[i]:
                orders[i] += [PassBattleOrder()]
                continue
            if not self.trapped[i]:
                orders[i] += [
                    SingleBattleOrder(mon) for mon in self.available_switches[i]
                ]
            if all(self.force_switch) and len(self.available_switches[0]) == 1:
                orders[i] += [PassBattleOrder()]
                continue
            active_mon = self.active_pokemon[i]
            if active_mon is not None and not self.force_switch[i]:
                orders[i] += [
                    SingleBattleOrder(move, move_target=target)
                    for move in self.available_moves[i]
                    for target in self.get_possible_showdown_targets(move, active_mon)
                ]
                if self.can_mega_evolve[i]:
                    orders[i] += [
                        SingleBattleOrder(move, move_target=target, mega=True)
                        for move in self.available_moves[i]
                        for target in self.get_possible_showdown_targets(
                            move, active_mon
                        )
                    ]
                if self.can_z_move[i]:
                    orders[i] += [
                        SingleBattleOrder(move, move_target=target, z_move=True)
                        for move in self.available_moves[i]
                        for target in self.get_possible_showdown_targets(
                            move, active_mon
                        )
                        if move in active_mon.available_z_moves
                    ]
                if self.can_dynamax[i]:
                    orders[i] += [
                        SingleBattleOrder(move, move_target=target, dynamax=True)
                        for move in self.available_moves[i]
                        for target in self.get_possible_showdown_targets(
                            move, active_mon, dynamax=True
                        )
                    ]
                if self.can_tera[i]:
                    orders[i] += [
                        SingleBattleOrder(move, move_target=target, terastallize=True)
                        for move in self.available_moves[i]
                        for target in self.get_possible_showdown_targets(
                            move, active_mon
                        )
                    ]
            if not orders[i]:
                orders[i] += [PassBattleOrder()]
        return orders

    @property
    def reviving(self) -> bool:
        """
        :return: Whether or not any of the player's Pokemon is reviving.
        :rtype: bool
        """
        return self._reviving
