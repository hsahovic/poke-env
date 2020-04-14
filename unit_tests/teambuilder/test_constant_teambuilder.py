# -*- coding: utf-8 -*-
from poke_env.teambuilder.constant_teambuilder import ConstantTeambuilder


def test_constant_teambuilder_yields_packed(packed_format_teams):
    for format_, teams in packed_format_teams.items():
        for team in teams:
            tb = ConstantTeambuilder(team)
            for _ in range(10):
                assert tb.yield_team() == team


def test_constant_teambuilder_yields_showdown(
    showdown_format_teams, packed_format_teams
):
    for format_ in packed_format_teams:
        for showdown_team, packed_team in zip(
            showdown_format_teams[format_], packed_format_teams[format_]
        ):
            tb = ConstantTeambuilder(showdown_team)
            for _ in range(10):
                assert tb.yield_team() == packed_team
