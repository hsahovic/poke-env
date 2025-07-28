from poke_env.teambuilder import TeambuilderPokemon


def test_teambuilder_pokemon_formatting():
    tp = TeambuilderPokemon(
        nickname="testy",
        species="Dragonair",
        item="choiceband",
        ability="shedskin",
        moves=["tackle", "watergun", "hiddenpower"],
        nature="Adamant",
        evs=[0] * 6,
        gender="M",
        ivs=[31] * 6,
        shiny=True,
        level=84,
        happiness=134,
        hiddenpowertype="water",
        gmax=True,
    )
    assert (
        tp.packed
        == "testy|dragonair|choiceband|shedskin|tackle,watergun,hiddenpower|Adamant||M|\
|S|84|134,water,,G"
    )

    assert (
        str(tp)
        == "testy|dragonair|choiceband|shedskin|tackle,watergun,hiddenpower|Adamant"
        "||M||S|84|134,water,,G"
    )
    assert (
        repr(tp)
        == "testy|dragonair|choiceband|shedskin|tackle,watergun,hiddenpower|Adamant||M"
        "||S|84|134,water,,G"
    )


def test_teambuilder_pokemon_from_packed(packed_format_teams):
    for _, teams in packed_format_teams.items():
        for team in teams:
            for packed_mon in team.split("]"):
                assert TeambuilderPokemon.from_packed(packed_mon).packed == packed_mon


def test_teambuilder_pokemon_from_showdown(showdown_format_teams, packed_format_teams):
    for format_, teams in showdown_format_teams.items():
        for showdown_team, packed_team in zip(
            showdown_format_teams[format_], packed_format_teams[format_]
        ):
            showdown_mons = showdown_team.split("\n\n")
            packed_mons = packed_team.split("]")

            for showdown_mon, packed_mon in zip(showdown_mons, packed_mons):
                assert (
                    TeambuilderPokemon.from_showdown(showdown_mon).packed == packed_mon
                )
