from poke_env.environment import Move, Pokemon, PokemonType


def test_pokemon_moves():
    mon = Pokemon(species="charizard", gen=8)

    mon.moved("flamethrower")
    assert "flamethrower" in mon.moves

    mon.moved("struggle")
    assert "struggle" not in mon.moves

    assert not mon.preparing
    assert not mon.must_recharge


def test_pokemon_types():
    # single type
    mon = Pokemon(species="pikachu", gen=8)
    assert mon.type_1 == PokemonType.ELECTRIC
    assert mon.type_2 is None

    # dual type
    mon = Pokemon(species="garchomp", gen=8)
    assert mon.type_1 == PokemonType.DRAGON
    assert mon.type_2 == PokemonType.GROUND

    # alolan forms
    mon = Pokemon(species="raichualola", gen=8)
    assert mon.type_1 == PokemonType.ELECTRIC
    assert mon.type_2 == PokemonType.PSYCHIC

    # megas
    mon = Pokemon(species="altaria", gen=8)
    assert mon.type_1 == PokemonType.DRAGON
    assert mon.type_2 == PokemonType.FLYING

    mon.mega_evolve("altariaite")
    assert mon.type_1 == PokemonType.DRAGON
    assert mon.type_2 == PokemonType.FAIRY

    mon = Pokemon(species="charizard", gen=8)
    mon.mega_evolve("charizarditex")
    assert mon.type_1 == PokemonType.FIRE
    assert mon.type_2 == PokemonType.DRAGON

    # primals
    mon = Pokemon(species="groudon", gen=8)
    assert mon.type_1 == PokemonType.GROUND
    assert mon.type_2 is None

    mon.primal()
    assert mon.type_1 == PokemonType.GROUND
    assert mon.type_2 == PokemonType.FIRE


def test_pokemon_damage_multiplier():
    mon = Pokemon(species="pikachu", gen=8)
    assert mon.damage_multiplier(PokemonType.GROUND) == 2
    assert mon.damage_multiplier(PokemonType.ELECTRIC) == 0.5

    mon = Pokemon(species="garchomp", gen=8)
    assert mon.damage_multiplier(Move("icebeam", gen=8)) == 4
    assert mon.damage_multiplier(Move("dracometeor", gen=8)) == 2

    mon = Pokemon(species="linoone", gen=8)
    assert mon.damage_multiplier(Move("closecombat", gen=8)) == 2
    assert mon.damage_multiplier(PokemonType.GHOST) == 0

    mon = Pokemon(species="linoone", gen=8)
    assert mon.damage_multiplier(Move("recharge", gen=8)) == 1


def test_powerherb_ends_move_preparation():
    mon = Pokemon(species="roserade", gen=8)
    mon.item = "powerherb"

    mon.prepare("solarbeam", "talonflame")
    assert mon.preparing

    mon.end_item("powerherb")
    assert not mon.preparing


def test_protect_counter_interactions():
    mon = Pokemon(species="xerneas", gen=8)
    mon.moved("protect", failed=False)

    assert mon.protect_counter == 1

    mon.start_effect("feint")
    assert mon.protect_counter == 0

    mon.moved("protect", failed=False)
    mon.moved("protect", failed=False)
    assert mon.protect_counter == 2

    mon.moved("geomancy", failed=False)
    assert mon.protect_counter == 0


def test_pokemon_as_strs():
    mon = Pokemon(species="charizard", gen=8)
    assert str(mon) == mon.__str__() == mon.__repr__()
    assert str(mon) == "charizard (pokemon object) [Active: False, Status: None]"

    mon._active = True
    assert str(mon) == "charizard (pokemon object) [Active: True, Status: None]"

    mon.set_hp_status("100/100 slp")
    assert str(mon) == "charizard (pokemon object) [Active: True, Status: SLP]"

    mon.cure_status()
    assert mon.status is None

    mon.cure_status()
    assert mon.status is None


def test_pokemon_boosts():
    mon = Pokemon(species="blastoise", gen=8)
    assert set(mon.boosts.values()) == {0}

    mon.boost("accuracy", 1)
    assert set(mon.boosts.values()) == {0, 1}
    assert mon.boosts["accuracy"] == 1

    mon.boost("accuracy", 2)
    assert mon.boosts["accuracy"] == 3

    mon.boost("accuracy", 2)
    assert mon.boosts["accuracy"] == 5

    mon.boost("accuracy", 1)
    assert mon.boosts["accuracy"] == 6

    mon.boost("accuracy", -1)
    assert mon.boosts["accuracy"] == 5

    mon.boost("accuracy", 5)
    assert mon.boosts["accuracy"] == 6

    mon.boost("accuracy", -10)
    assert mon.boosts["accuracy"] == -4

    mon.boost("accuracy", -10)
    assert mon.boosts["accuracy"] == -6

    mon.boost("spd", 2)
    mon.clear_negative_boosts()
    assert mon.boosts["accuracy"] == 0
    assert mon.boosts["spd"] == 2


def test_pokemon_base_species():
    charizard = Pokemon(species="charizard", gen=8)
    mega_charizard_x = Pokemon(species="charizardmegax", gen=8)
    mega_charizard_y = Pokemon(species="charizardmegay", gen=8)

    assert charizard.base_species == "charizard"
    assert mega_charizard_x.base_species == "charizard"
    assert mega_charizard_y.base_species == "charizard"

    arceus = Pokemon(species="arceus", gen=8)
    acreus_bug = Pokemon(species="arceusbug", gen=8)

    assert arceus.base_species == "arceus"
    assert acreus_bug.base_species == "arceus"
