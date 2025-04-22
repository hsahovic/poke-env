"""This module defines the ConstantTeambuilder class, which is a subclass of
ShowdownTeamBuilder that yields a constant team.
"""

from typing import List

from poke_env.teambuilder.teambuilder import Teambuilder
from poke_env.teambuilder.teambuilder_pokemon import TeambuilderPokemon


class ConstantTeambuilder(Teambuilder):
    def __init__(self, team: str):
        if "|" in team:
            self._mons = self.parse_packed_team(team)
        else:
            self._mons = self.parse_showdown_team(team)

        self.packed_team = self.join_team(self._mons)

    def yield_team(self) -> str:
        return self.packed_team

    @property
    def team(self) -> List[TeambuilderPokemon]:
        return self._mons
