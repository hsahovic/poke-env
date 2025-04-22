"""This module defines the Teambuilder abstract class, which represents objects yielding
Pokemon Showdown teams in the context of communicating with Pokemon Showdown.
"""

from abc import ABC, abstractmethod
from typing import List

from poke_env.teambuilder.teambuilder_pokemon import TeambuilderPokemon


class Teambuilder(ABC):
    """Teambuilder objects allow the generation of teams by Player instances.

    They must implement the yield_team method, which must return a valid
    packed-formatted showdown team every time it is called.

    This format is a custom format decribed in Pokemon's showdown protocol
    documentation:
    https://github.com/smogon/pokemon-showdown/blob/master/PROTOCOL.md#team-format

    This class also implements a helper function to convert teams from the classical
    showdown team text format into the packed-format.
    """

    @abstractmethod
    def yield_team(self) -> str:
        """Returns a packed-format team."""

    @staticmethod
    def parse_showdown_team(team: str) -> List[TeambuilderPokemon]:
        """Converts a showdown-formatted team string into a list of TeambuilderPokemon
        objects.

        This method can be used when using teams built in the showdown teambuilder.

        :param team: The showdown-format team to convert.
        :type team: str
        :return: The formatted team.
        :rtype: list of TeambuilderPokemon
        """
        mons = []

        for ps_mon in team.split("\n\n"):
            if ps_mon == "":
                continue
            mons.append(TeambuilderPokemon.from_showdown(ps_mon))

        return mons

    @staticmethod
    def parse_packed_team(team: str) -> List[TeambuilderPokemon]:
        """Converts a packed-format team string into a list of TeambuilderPokemon
        objects.

        :param team: The packed-format team to convert.
        :type team: str
        :return: The formatted team.
        :rtype: list of TeambuilderPokemon
        """
        packed_mons = team.split("]")

        mons = []

        for packed_mon in packed_mons:
            if packed_mon == "":
                continue

            mons.append(TeambuilderPokemon.from_packed(packed_mon))

        return mons

    @staticmethod
    def join_team(team: List[TeambuilderPokemon]) -> str:
        """Converts a list of TeambuilderPokemon objects into the corresponding packed
        showdown team format.

        :param team: The list of TeambuilderPokemon objects that form the team.
        :type team: list of TeambuilderPokemon
        :return: The formatted team string.
        :rtype: str"""
        return "]".join([mon.packed for mon in team])
