import asyncio

from unittest.mock import MagicMock

from poke_env.environment.battle import Battle
from poke_env.environment.pokemon import Pokemon


def test_dynamax():
	logger = MagicMock()
	battle = Battle("tag", "username", logger)
	battle._player_role = "p1"

	hydreigon = Pokemon(species="hydreigon")
	max_hp_before_dynamax = 326
	current_hp_before_dynamax = 100
	hydreigon._max_hp = max_hp_before_dynamax
	hydreigon._current_hp = current_hp_before_dynamax
	hydreigon._active = True
	battle._team = {'p1: Hydreigon': hydreigon}
	assert battle.active_pokemon.is_dynamaxed is not True

	loop = asyncio.get_event_loop()
	loop.run_until_complete(
		asyncio.wait([
			battle._parse_message([
				'',
				'-start',
				'p1: Hydreigon',
				'dynamax'
			])
		])
	)

	assert battle.active_pokemon.is_dynamaxed
	assert battle.active_pokemon._max_hp == max_hp_before_dynamax * 2
	assert battle.active_pokemon._current_hp == current_hp_before_dynamax * 2
	assert battle.dynamax_turns_left == 3

	loop.run_until_complete(
		asyncio.wait([
			battle._parse_message([
				'',
				'-end',
				'p1: Hydreigon',
				'dynamax'
			])
		])
	)

	assert not battle.active_pokemon.is_dynamaxed
	assert battle.active_pokemon._max_hp == max_hp_before_dynamax
	assert battle.active_pokemon._current_hp == current_hp_before_dynamax
	assert battle.dynamax_turns_left is None
	assert not battle.can_dynamax
