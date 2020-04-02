# -*- coding: utf-8 -*-
"""This module defines the Teambuilder abstract class, which represents objects yielding
Pokemon Showdown teams in the context of communicating with Pokemon Showdown.
"""
from abc import ABC, abstractmethod
from poke_env.teambuilder.teambuilder_pokemon import TeambuilderPokemon
from typing import List


class Teambuilder(ABC):
    @abstractmethod
    def yield_team(self):
        pass

    @staticmethod
    def join_team(team: List[TeambuilderPokemon]) -> str:
        """Converts a list of TeambuilderPokemon objects into the corresponding packed
        showdown team format.

        :param team: The list of TeambuilderPokemon objects that form the team.
        :type team: list
        :return: The formatted team string.
        :type: str"""
        return "]".join([mon.formatted for mon in team])
