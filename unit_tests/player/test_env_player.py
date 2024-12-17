import asyncio
import unittest
from unittest.mock import patch

from gymnasium.spaces import Space

from poke_env.concurrency import POKE_LOOP
from poke_env import AccountConfiguration, ServerConfiguration
from poke_env.environment import AbstractBattle, Battle, Move, Pokemon
from poke_env.player import (
    BattleOrder,
    Gen4EnvSinglePlayer,
    Gen5EnvSinglePlayer,
    Gen6EnvSinglePlayer,
    Gen7EnvSinglePlayer,
    Gen8EnvSinglePlayer,
    Gen9EnvSinglePlayer,
    PokeEnv,
)
from poke_env.player.openai_api import _EnvPlayer

acct_config1 = AccountConfiguration("username1", "password1")
acct_config2 = AccountConfiguration("username2", "password2")
server_configuration = ServerConfiguration("server.url", "auth.url")


class CustomEnvPlayer(PokeEnv):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def calc_reward(self, battle) -> float:
        pass

    def action_to_move(self, action: int, battle: AbstractBattle) -> BattleOrder:
        return Gen7EnvSinglePlayer.action_to_move(self, action, battle)

    def describe_embedding(self) -> Space:
        pass

    _ACTION_SPACE = Gen7EnvSinglePlayer._ACTION_SPACE

    def embed_battle(self, battle):
        return None


def test_init():
    gym_env = CustomEnvPlayer(
        acct_config1=acct_config1,
        acct_config2=acct_config2,
        server_configuration=server_configuration,
        start_listening=False,
        battle_format="gen7randombattles",
    )
    player = gym_env.agent1
    opponent = gym_env.agent2
    assert isinstance(gym_env, CustomEnvPlayer)
    assert isinstance(player, _EnvPlayer)
    assert isinstance(opponent, _EnvPlayer)


def test_choose_move():
    # Run the test code within POKE_LOOP
    async def run_test():
        player = CustomEnvPlayer(
            acct_config1=acct_config1,
            acct_config2=acct_config2,
            server_configuration=server_configuration,
            start_listening=False,
            battle_format="gen7randombattles",
            start_challenging=False,
        )

        # Create a mock battle and moves
        battle = Battle("bat1", player.agent1.username, player.agent1.logger, gen=8)
        battle._available_moves = [Move("flamethrower", gen=8)]

        # Test choosing a move
        message = await player.agent1.choose_move(battle)
        order = player.action_to_move(0, battle)
        player.agent1.order_queue.put(order)

        assert message.message == "/choose move flamethrower"

        # Test switching Pokémon
        battle._available_switches = [Pokemon(species="charizard", gen=8)]
        message = await player.agent1.choose_move(battle)
        order = player.action_to_move(4, battle)
        player.agent1.order_queue.put(order)

        assert message.message == "/choose switch charizard"

    # Run everything in POKE_LOOP
    asyncio.run_coroutine_threadsafe(run_test(), POKE_LOOP)


@patch(
    "poke_env.environment.Pokemon.available_z_moves",
    new_callable=unittest.mock.PropertyMock,
)
def test_action_to_move(z_moves_mock):
    for PlayerClass, (has_megas, has_z_moves, has_dynamax, has_tera) in zip(
        [
            Gen4EnvSinglePlayer,
            Gen5EnvSinglePlayer,
            Gen6EnvSinglePlayer,
            Gen7EnvSinglePlayer,
            Gen8EnvSinglePlayer,
            Gen9EnvSinglePlayer,
        ],
        [
            (False, False, False, False),
            (False, False, False, False),
            (True, False, False, False),
            (True, True, False, False),
            (True, True, True, False),
            (True, True, True, True),
        ],
    ):

        class CustomEnvClass(PlayerClass):
            def embed_battle(self, *args, **kwargs):
                return []

            def calc_reward(self, last_battle, current_battle):
                return 0.0

            def describe_embedding(self):
                return None

            def get_opponent(self):
                return None

        p = CustomEnvClass(None, start_listening=False, start_challenging=False)
        battle = Battle("bat1", p.agent1.username, p.agent1.logger, gen=8)
        assert p.action_to_move(-1, battle).message == "/forfeit"
        battle._available_moves = [Move("flamethrower", gen=8)]
        assert p.action_to_move(0, battle).message == "/choose move flamethrower"
        battle._available_switches = [Pokemon(species="charizard", gen=8)]
        assert (
            p.action_to_move(
                4
                + (4 * int(has_megas))
                + (4 * int(has_z_moves))
                + (4 * int(has_dynamax))
                + (4 * int(has_tera)),
                battle,
            ).message
            == "/choose switch charizard"
        )
        battle._available_switches = []
        assert p.action_to_move(3, battle).message == "/choose move flamethrower"
        if has_megas:
            battle._can_mega_evolve = True
            assert (
                p.action_to_move(4 + (4 * int(has_z_moves)), battle).message
                == "/choose move flamethrower mega"
            )
        if has_z_moves:
            battle._can_z_move = True
            active_pokemon = Pokemon(species="charizard", gen=8)
            active_pokemon._active = True
            battle._team = {"charizard": active_pokemon}
            z_moves_mock.return_value = [Move("flamethrower", gen=8)]
            assert (
                p.action_to_move(4, battle).message == "/choose move flamethrower zmove"
            )
            battle._team = {}
        if has_dynamax:
            battle._can_dynamax = True
            assert (
                p.action_to_move(12, battle).message
                == "/choose move flamethrower dynamax"
            )
        if has_tera:
            battle._can_tera = True
            assert (
                p.action_to_move(16, battle).message
                == "/choose move flamethrower terastallize"
            )
