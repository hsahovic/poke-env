from typing import Dict, List

from poke_env.teambuilder import ConstantTeambuilder, TeambuilderPokemon


def test_constant_teambuilder_yields_packed(packed_format_teams):
    for format_, teams in packed_format_teams.items():
        for team in teams:
            tb = ConstantTeambuilder(team)
            for _ in range(10):
                assert tb.yield_team() == team


def test_constant_teambuilder_yields_showdown(
    showdown_format_teams: Dict[str, List[str]],
    packed_format_teams: Dict[str, List[str]],
):
    for format_ in packed_format_teams:
        for showdown_team, packed_team in zip(
            showdown_format_teams[format_], packed_format_teams[format_]
        ):
            ps_tb = ConstantTeambuilder(showdown_team)
            packed_tb = ConstantTeambuilder(packed_team)

            for _ in range(10):
                assert ps_tb.yield_team() == packed_team
                assert packed_tb.yield_team() == packed_team

            assert ps_tb.join_team(ps_tb.team) == packed_tb.join_team(packed_tb.team)


def test_showdown_team_parsing_works_without_items():
    team = """
Flareon
Ability: Flash Fire
EVs: 252 HP / 126 Def / 126 SpD / 4 Spe
Hardy Nature
- Flare Blitz
- Superpower
- Double-Edge
- Iron Tail

Ninetales
Ability: Flash Fire
EVs: 252 HP / 126 Def / 126 SpD / 4 Spe
IVs: 0 Atk
- Flamethrower
- Extrasensory
- Calm Mind
- Dark Pulse

Arcanine
Ability: Flash Fire
EVs: 252 HP / 126 Def / 126 SpD / 4 Spe
- Flare Blitz
- Wild Charge
- Facade
- Crunch

Heatmor
Ability: Flash Fire
EVs: 252 HP / 126 Def / 126 SpD / 4 Spe
- Flare Blitz
- Body Slam
- Night Slash
- Stomping Tantrum

Typhlosion
Ability: Flash Fire
EVs: 252 HP / 126 Def / 126 SpD / 4 Spe
- Flamethrower
- Extrasensory
- Flare Blitz
- Earthquake

Rapidash
Ability: Flash Fire
EVs: 252 HP / 126 Def / 126 SpD / 4 Spe
- Flare Blitz
- Wild Charge
- Drill Run
- Poison Jab
"""

    packed_team = "Flareon|||flashfire|flareblitz,superpower,doubleedge,irontail|Hardy|252,,126,,126,4|||||]Ninetales|||flashfire|flamethrower,extrasensory,calmmind,darkpulse||252,,126,,126,4||,0,,,,|||]Arcanine|||flashfire|flareblitz,wildcharge,facade,crunch||252,,126,,126,4|||||]Heatmor|||flashfire|flareblitz,bodyslam,nightslash,stompingtantrum||252,,126,,126,4|||||]Typhlosion|||flashfire|flamethrower,extrasensory,flareblitz,earthquake||252,,126,,126,4|||||]Rapidash|||flashfire|flareblitz,wildcharge,drillrun,poisonjab||252,,126,,126,4|||||"

    assert ConstantTeambuilder(team).yield_team() == packed_team

    team = ConstantTeambuilder(team).team
    assert isinstance(team[0], TeambuilderPokemon)
    for i, formatted_mon in enumerate(packed_team.split("]")):
        assert team[i].packed == formatted_mon
