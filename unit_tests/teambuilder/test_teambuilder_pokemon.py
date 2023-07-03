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
        tp.formatted
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
