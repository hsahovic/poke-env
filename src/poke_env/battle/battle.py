from logging import Logger
from typing import Any, Dict, List, Optional, Union

from poke_env.battle.abstract_battle import AbstractBattle
from poke_env.battle.move import Move
from poke_env.battle.pokemon import Pokemon
from poke_env.player.battle_order import DefaultBattleOrder, SingleBattleOrder


class Battle(AbstractBattle):
    def __init__(
        self,
        battle_tag: str,
        username: str,
        logger: Logger,
        gen: int,
        save_replays: Union[str, bool] = False,
    ):
        super(Battle, self).__init__(battle_tag, username, logger, save_replays, gen)

        # Turn choice attributes
        self._available_moves: List[Move] = []
        self._available_switches: List[Pokemon] = []
        self._can_mega_evolve = False
        self._can_z_move = False
        self._can_dynamax = False
        self._can_tera = False
        self._force_switch = False
        self._maybe_trapped = False
        self._trapped = False

    def clear_all_boosts(self):
        if self.active_pokemon is not None:
            self.active_pokemon.clear_boosts()
        if self.opponent_active_pokemon is not None:
            self.opponent_active_pokemon.clear_boosts()

    def end_illusion(self, pokemon_name: str, details: str):
        if pokemon_name[:2] == self._player_role:
            active = self.active_pokemon
        else:
            active = self.opponent_active_pokemon

        if active is None:
            raise ValueError("Cannot end illusion without an active pokemon.")

        self._end_illusion_on(
            illusioned=active, illusionist=pokemon_name, details=details
        )

    def _get_target_mon(
        self, pokemon: str, target_type: str, target_str: str | None
    ) -> Pokemon | None:
        if target_type != "all" and target_str is not None:
            return self.get_pokemon(target_str)
        elif self.player_role == pokemon[:2]:
            return self.opponent_active_pokemon
        else:
            return self.active_pokemon

    def parse_request(
        self, request: Dict[str, Any], strict_battle_tracking: bool = False
    ):
        """
        Update the object from a request.
        The player's pokemon are all updated, as well as available moves, switches and
        other related information (z move, mega evolution, forced switch...).

        :param request: Parsed JSON request object.
        :type request: dict
        """
        if "wait" in request and request["wait"]:
            self._wait = True
        else:
            self._wait = False

        side = request["side"]

        self._available_moves = []
        self._available_switches = []
        self._can_mega_evolve = False
        self._can_z_move = False
        self._can_dynamax = False
        self._can_tera = False
        self._maybe_trapped = False
        self._reviving = any(
            [m["reviving"] for m in side.get("pokemon", []) if "reviving" in m]
        )
        self._trapped = False
        self._force_switch = request.get("forceSwitch", [False])[0]

        self._last_request = request

        if request.get("teamPreview", False):
            self._teampreview = True
            number_of_mons = len(request["side"]["pokemon"])
            self._max_team_size = request.get("maxTeamSize", number_of_mons)
        else:
            self._teampreview = False
        self._update_team_from_request(request["side"], strict_battle_tracking)

        if "active" in request:
            active_request = request["active"][0]

            if active_request.get("trapped"):
                self._trapped = True

            if self.active_pokemon is not None:
                if strict_battle_tracking:
                    self.active_pokemon.check_move_consistency(active_request)
                # TODO: the illusion handling here works around Zoroark's
                # difficulties. This should be properly handled at some point.
                try:
                    self._available_moves.extend(
                        self.active_pokemon.available_moves_from_request(active_request)
                    )
                except AssertionError as e:
                    if "illusion" not in [p.ability for p in self.team.values()]:
                        raise e
            if active_request.get("canMegaEvo", False):
                self._can_mega_evolve = True
            if active_request.get("canZMove", False):
                self._can_z_move = True
            if active_request.get("canDynamax", False):
                self._can_dynamax = True
            if active_request.get("canTerastallize", False):
                self._can_tera = True
            if active_request.get("maybeTrapped", False):
                self._maybe_trapped = True

        if side["pokemon"]:
            self._player_role = side["pokemon"][0]["ident"][:2]

        if not self.trapped:
            for pkmn_json in side["pokemon"]:
                pokemon = self.team[pkmn_json["ident"]]
                if self.reviving:
                    if pokemon.fainted:
                        self._available_switches.append(pokemon)
                elif not pokemon.active and not pokemon.fainted:
                    self._available_switches.append(pokemon)

    def switch(self, pokemon_str: str, details: str, hp_status: str):
        identifier = pokemon_str.split(":")[0][:2]

        if identifier == self._player_role:
            if self.active_pokemon:
                self.active_pokemon.switch_out(self.fields)
        else:
            if self.opponent_active_pokemon:
                self.opponent_active_pokemon.switch_out(self.fields)

        pokemon = self.get_pokemon(pokemon_str, details=details)

        pokemon.switch_in(details=details)
        pokemon.set_hp_status(hp_status)

    @property
    def active_pokemon(self) -> Optional[Pokemon]:
        """
        :return: The active pokemon
        :rtype: Optional[Pokemon]
        """
        for pokemon in self.team.values():
            if pokemon.active:
                return pokemon
        return None

    @property
    def all_active_pokemons(self) -> List[Optional[Pokemon]]:
        """
        :return: A list containing all active pokemons and/or Nones.
        :rtype: List[Optional[Pokemon]]
        """
        return [self.active_pokemon, self.opponent_active_pokemon]

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
    def can_dynamax(self) -> bool:
        """
        :return: Whether or not the current active pokemon can dynamax
        :rtype: bool
        """
        return self._can_dynamax

    @property
    def can_mega_evolve(self) -> bool:
        """
        :return: Whether or not the current active pokemon can mega evolve.
        :rtype: bool
        """
        return self._can_mega_evolve

    @property
    def can_tera(self) -> bool:
        """
        :return: Whether or not the current active pokemon can terastallize
        :rtype: bool
        """
        return self._can_tera

    @property
    def can_z_move(self) -> bool:
        """
        :return: Whether or not the current active pokemon can z-move.
        :rtype: bool
        """
        return self._can_z_move

    @property
    def force_switch(self) -> bool:
        """
        :return: A boolean indicating whether the active pokemon is forced to switch
            out.
        :rtype: Optional[bool]
        """
        return self._force_switch

    @property
    def grounded(self) -> bool:
        """
        :return: A boolean indicating whether the active pokemon is grounded
        :rtype: bool
        """
        return self.is_grounded(self.active_pokemon) if self.active_pokemon else True

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
    def trapped(self) -> bool:
        """
        :return: A boolean indicating whether the active pokemon is trapped, either by
            the opponent or as a side effect of one your moves.
        :rtype: bool
        """
        return self._trapped

    @trapped.setter
    def trapped(self, value: bool):
        self._trapped = value

    @property
    def valid_orders(self) -> List[SingleBattleOrder]:
        orders: List[SingleBattleOrder] = []
        if self._wait:
            return [DefaultBattleOrder()]
        if not self.trapped:
            orders += [SingleBattleOrder(mon) for mon in self.available_switches]
        if self.active_pokemon is None or self.force_switch:
            return orders
        orders += [SingleBattleOrder(move) for move in self.available_moves]
        if self.can_mega_evolve:
            orders += [
                SingleBattleOrder(move, mega=True) for move in self.available_moves
            ]
        if self.can_z_move:
            orders += [
                SingleBattleOrder(move, z_move=True)
                for move in self.available_moves
                if move in self.active_pokemon.available_z_moves
            ]
        if self.can_dynamax:
            orders += [
                SingleBattleOrder(move, dynamax=True) for move in self.available_moves
            ]
        if self.can_tera:
            orders += [
                SingleBattleOrder(move, terastallize=True)
                for move in self.available_moves
            ]
        return orders
