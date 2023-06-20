# -*- coding: utf-8 -*-
"""This module defines the ConstantTeambuilder class, which is a subclass of
ShowdownTeamBuilder that yields a constant team.
"""
from poke_env.teambuilder.teambuilder import Teambuilder


class ConstantTeambuilder(Teambuilder):
    def __init__(self, team: str):
        if "|" in team:
            self.converted_team = team
        else:
            mons = self.parse_showdown_team(team)
            self.converted_team = self.join_team(mons)

    def yield_team(self) -> str:
        return self.converted_team
