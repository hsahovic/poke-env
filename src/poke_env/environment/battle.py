# -*- coding: utf-8 -*-

from aiologger import Logger  # pyre-ignore
from typing import Dict
from typing import List
from typing import Optional

from poke_env.environment.move import Move
from poke_env.environment.pokemon import Pokemon
from poke_env.environment.abstract_battle import AbstractBattle
from poke_env.environment.move import SPECIAL_MOVES


class Battle(AbstractBattle):
    def __init__(self, battle_tag: str, username: str, logger: Logger):  # pyre-ignore
        super(Battle, self).__init__(battle_tag, username, logger)

        # Turn choice attributes
        self._available_moves: List[Move] = []
        self._available_switches: List[Pokemon] = []
        self._can_mega_evolve: bool = False
        self._can_z_move: bool = False
        self._can_dynamax: bool = False
        self._opponent_can_dynamax = True
        self._force_switch: bool = False
        self._maybe_trapped: bool = False
        self._trapped: bool = False

    def _clear_all_boosts(self):
        self.active_pokemon._clear_boosts()
        if self.opponent_active_pokemon is not None:
            self.opponent_active_pokemon._clear_boosts()

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
        pokemon._switch_in(details=details)
        pokemon.status = active.status

    def _parse_request(self, request: Dict) -> None:
        """
        Update the object from a request.
        The player's pokemon are all updated, as well as available moves, switches and
        other related information (z move, mega evolution, forced switch...).
        Args:
            request (dict): parsed json request object
        """
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

            if active_pokemon:
                for move in active_request["moves"]:
                    if not move.get("disabled", False):
                        if move["id"] in active_pokemon.moves:
                            self._available_moves.append(
                                active_pokemon.moves[move["id"]]
                            )
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
                                }.intersection(active_pokemon.moves.keys()):
                                    self.logger.warning(
                                        "An error occured in battle %s while adding "
                                        "available moves. The move '%s' was either "
                                        "unknown or not available for the active "
                                        "pokemon: %s",
                                        self.battle_tag,
                                        move["id"],
                                        active_pokemon.species,
                                    )
                                else:
                                    self.logger.info(
                                        "The move '%s' was received in battle %s for "
                                        "your active pokemon %s. This move could not "
                                        "be added, but it might come from a special "
                                        "move such as copycat or me first. If that is "
                                        "not the case, please make sure there is an "
                                        "explanation for this behavior or report it if "
                                        "it is an error.",
                                        move["id"],
                                        self.battle_tag,
                                        active_pokemon.species,
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

    def _switch(self, pokemon, details, hp_status):
        identifier = pokemon.split(":")[0][:2]

        if identifier == self._player_role:
            if self.active_pokemon:
                self.active_pokemon._switch_out()
        else:
            if self.opponent_active_pokemon:
                self.opponent_active_pokemon._switch_out()

        pokemon = self.get_pokemon(pokemon, details=details)

        pokemon._switch_in(details=details)
        pokemon._set_hp_status(hp_status)

    @property
    def active_pokemon(self) -> Optional[Pokemon]:
        """
        :return: The active pokemon
        :rtype: Optional[Pokemon]
        """
        for pokemon in self.team.values():
            if pokemon.active:
                return pokemon

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
    def force_switch(self) -> bool:
        """
        :return: A boolean indicating whether the active pokemon is forced to switch
            out.
        :rtype: Optional[bool]
        """
        return self._force_switch

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

    @opponent_can_dynamax.setter
    def opponent_can_dynamax(self, value: bool) -> None:
        self._opponent_can_dynamax = value

    @property
    def trapped(self) -> bool:
        """
        :return: A boolean indicating whether the active pokemon is trapped, either by
            the opponent or as a side effect of one your moves.
        :rtype: bool
        """
        return self._trapped

    @trapped.setter
    def trapped(self, value):
        self._trapped = value
