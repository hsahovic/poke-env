# -*- coding: utf-8 -*-
from poke_env.teambuilder.teambuilder import Teambuilder


def test_join_team(showdown_format_teams, packed_format_teams):
    for format_, teams in showdown_format_teams.items():
        for showdown_team, packed_team in zip(teams, packed_format_teams[format_]):
            joined_team = Teambuilder.join_team(
                Teambuilder.parse_showdown_team(showdown_team)
            )
            assert joined_team == packed_team


def test_parse_showdown_team(showdown_format_teams):
    for format_, teams in showdown_format_teams.items():
        for team in teams:
            parsed_team = Teambuilder.parse_showdown_team(team)
            assert len(parsed_team) == 6
