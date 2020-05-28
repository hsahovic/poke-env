# -*- coding: utf-8 -*-

from aiologger import Logger  # pyre-ignore
from typing import Dict

from poke_env.environment.abstract_battle import AbstractBattle


class DoubleBattle(AbstractBattle):
    def __init__(self, battle_tag: str, username: str, logger: Logger):  # pyre-ignore
        super(DoubleBattle, self).__init__(battle_tag, username, logger)

    def _parse_request(self, request: Dict) -> None:
        """
        Update the object from a request.
        The player's pokemon are all updated, as well as available moves, switches and
        other related information (z move, mega evolution, forced switch...).
        Args:
            request (dict): parsed json request object
        """
        pass

    @property
    def active_pokemon(self):
        """
        :return: The active pokemon
        """
        raise NotImplementedError

    @property
    def available_moves(self):
        """
        :return: The list of moves the player can use during the current move request.
        """
        raise NotImplementedError

    @property
    def can_mega_evolve(self):
        """
        :return: Wheter of not the current active pokemon can mega evolve.
        """
        raise NotImplementedError

    @property
    def can_z_move(self):
        """
        :return: Wheter of not the current active pokemon can z-move.
        """
        raise NotImplementedError

    @property
    def force_switch(self):
        """
        :return: A boolean indicating whether the active pokemon is forced to switch
            out.
        """
        raise NotImplementedError

    @property
    def maybe_trapped(self):
        """
        :return: A boolean indicating whether the active pokemon is maybe trapped by the
            opponent.
        """
        raise NotImplementedError

    @property
    def opponent_active_pokemon(self):
        """
        :return: The opponent active pokemon
        """
        raise NotImplementedError

    @property
    def trapped(self):
        """
        :return: A boolean indicating whether the active pokemon is trapped by the
            opponent.
        """
        raise NotImplementedError

    @trapped.setter
    def trapped(self, value):
        raise NotImplementedError
