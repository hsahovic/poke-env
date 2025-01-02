import asyncio
import sys
import unittest
from io import StringIO
from typing import List
from unittest.mock import PropertyMock, patch

from gymnasium.spaces import Box, Discrete
from pettingzoo.utils.env import ActionType

from poke_env.concurrency import POKE_LOOP
from poke_env.environment import AbstractBattle, Battle, Move, Pokemon, Status
from poke_env.player import ForfeitBattleOrder, GymnasiumEnv
from poke_env.player.gymnasium_api import _AsyncQueue, _EnvPlayer
from poke_env.ps_client import AccountConfiguration, ServerConfiguration

account_configuration1 = AccountConfiguration("username1", "password1")
account_configuration2 = AccountConfiguration("username2", "password2")
server_configuration = ServerConfiguration("server.url", "auth.url")


class CustomEnv(GymnasiumEnv):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.observation_spaces = {agent: Box(-1, 1) for agent in self.possible_agents}

    def calc_reward(self, battle) -> float:
        return 0.0

    def embed_battle(self, battle):
        return []


def test_init():
    gymnasium_env = CustomEnv(
        account_configuration1=account_configuration1,
        account_configuration2=account_configuration2,
        server_configuration=server_configuration,
        start_listening=False,
        battle_format="gen7randombattles",
    )
    player = gymnasium_env.agent1
    assert isinstance(gymnasium_env, CustomEnv)
    assert isinstance(player, _EnvPlayer)


def test_choose_move():
    # Run the test code within POKE_LOOP
    async def run_test():
        player = CustomEnv(
            account_configuration1=account_configuration1,
            account_configuration2=account_configuration2,
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
        order = player.action_to_order(0, battle)
        player.agent1.order_queue.put(order)

        assert message.message == "/choose move flamethrower"

        # Test switching Pokémon
        battle._available_switches = [Pokemon(species="charizard", gen=8)]
        message = await player.agent1.choose_move(battle)
        order = player.action_to_order(4, battle)
        player.agent1.order_queue.put(order)

        assert message.message == "/choose switch charizard"

    # Run everything in POKE_LOOP
    asyncio.run_coroutine_threadsafe(run_test(), POKE_LOOP)


def test_reward_computing_helper():
    player = CustomEnv(
        account_configuration1=account_configuration1,
        account_configuration2=account_configuration2,
        server_configuration=server_configuration,
        start_listening=False,
        battle_format="gen7randombattles",
    )
    battle_1 = Battle("bat1", player.agent1.username, player.agent1.logger, gen=8)
    battle_2 = Battle("bat2", player.agent1.username, player.agent1.logger, gen=8)
    battle_3 = Battle("bat3", player.agent1.username, player.agent1.logger, gen=8)
    battle_4 = Battle("bat4", player.agent1.username, player.agent1.logger, gen=8)

    assert (
        player.reward_computing_helper(
            battle_1,
            fainted_value=0,
            hp_value=0,
            number_of_pokemons=4,
            starting_value=0,
            status_value=0,
            victory_value=1,
        )
        == 0
    )

    battle_1._won = True
    assert (
        player.reward_computing_helper(
            battle_1,
            fainted_value=0,
            hp_value=0,
            number_of_pokemons=4,
            starting_value=0,
            status_value=0,
            victory_value=1,
        )
        == 1
    )

    assert (
        player.reward_computing_helper(
            battle_2,
            fainted_value=0,
            hp_value=0,
            number_of_pokemons=4,
            starting_value=0.5,
            status_value=0,
            victory_value=5,
        )
        == -0.5
    )

    battle_2._won = False
    assert (
        player.reward_computing_helper(
            battle_2,
            fainted_value=0,
            hp_value=0,
            number_of_pokemons=4,
            starting_value=0,
            status_value=0,
            victory_value=5,
        )
        == -5
    )

    battle_3._team = {i: Pokemon(species="slaking", gen=8) for i in range(4)}
    battle_3._opponent_team = {i: Pokemon(species="slowbro", gen=8) for i in range(3)}

    battle_3._team[0].status = Status["FRZ"]
    battle_3._team[1]._current_hp = 100
    battle_3._team[1]._max_hp = 200
    battle_3._opponent_team[0].status = Status["FNT"]
    battle_3._opponent_team[1].status = Status["FNT"]

    # Opponent: two fainted, one full hp opponent
    # You: one half hp mon, one frozen mon
    assert (
        player.reward_computing_helper(
            battle_3,
            fainted_value=2,
            hp_value=3,
            number_of_pokemons=4,
            starting_value=0,
            status_value=0.25,
            victory_value=100,
        )
        == 2.25
    )

    battle_3._won = True
    assert (
        player.reward_computing_helper(
            battle_3,
            fainted_value=2,
            hp_value=3,
            number_of_pokemons=4,
            starting_value=0,
            status_value=0.25,
            victory_value=100,
        )
        == 100
    )

    battle_4._team, battle_4._opponent_team = (
        battle_3._opponent_team,
        battle_3._team,
    )
    assert (
        player.reward_computing_helper(
            battle_4,
            fainted_value=2,
            hp_value=3,
            number_of_pokemons=4,
            starting_value=0,
            status_value=0.25,
            victory_value=100,
        )
        == -2.25
    )


def test_action_space():
    player = CustomEnv(start_listening=False)
    assert player.action_space(player.possible_agents[0]) == Discrete(3 * 4 + 6)

    for battle_format, (has_megas, has_z_moves, has_dynamax) in zip(
        [
            "gen4randombattle",
            "gen5randombattle",
            "gen6randombattle",
            "gen7randombattle",
            "gen8randombattle",
        ],
        [
            (False, False, False),
            (False, False, False),
            (True, False, False),
            (True, True, False),
            (True, True, True),
        ],
    ):

        p = CustomEnv(
            battle_format=battle_format, start_listening=False, start_challenging=False
        )

        assert p.action_space(p.possible_agents[0]) == Discrete(
            4 * sum([1, has_megas, has_z_moves, has_dynamax]) + 6
        )


@patch(
    "poke_env.environment.Pokemon.available_z_moves",
    new_callable=PropertyMock,
)
def test_action_to_move(z_moves_mock):
    for battle_format, (has_megas, has_z_moves, has_dynamax, has_tera) in zip(
        [
            "gen4randombattle",
            "gen5randombattle",
            "gen6randombattle",
            "gen7randombattle",
            "gen8randombattle",
            "gen9randombattle",
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
        p = GymnasiumEnv(
            battle_format=battle_format, start_listening=False, start_challenging=False
        )
        battle = Battle("bat1", p.agent1.username, p.agent1.logger, gen=8)
        assert p.action_to_order(-1, battle).message == "/forfeit"
        battle._available_moves = [Move("flamethrower", gen=8)]
        assert p.action_to_order(0, battle).message == "/choose move flamethrower"
        battle._available_switches = [Pokemon(species="charizard", gen=8)]
        assert (
            p.action_to_order(
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
        assert p.action_to_order(3, battle).message == "/choose move flamethrower"
        if has_megas:
            battle._can_mega_evolve = True
            assert (
                p.action_to_order(4 + (4 * int(has_z_moves)), battle).message
                == "/choose move flamethrower mega"
            )
        if has_z_moves:
            battle._can_z_move = True
            active_pokemon = Pokemon(species="charizard", gen=8)
            active_pokemon._active = True
            battle._team = {"charizard": active_pokemon}
            z_moves_mock.return_value = [Move("flamethrower", gen=8)]
            assert (
                p.action_to_order(4, battle).message
                == "/choose move flamethrower zmove"
            )
            battle._team = {}
        if has_dynamax:
            battle._can_dynamax = True
            assert (
                p.action_to_order(12, battle).message
                == "/choose move flamethrower dynamax"
            )
        if has_tera:
            battle._can_tera = True
            assert (
                p.action_to_order(16, battle).message
                == "/choose move flamethrower terastallize"
            )


class DummyEnv(GymnasiumEnv[List[int], ActionType]):
    _ACTION_SPACE = list(range(10))

    def __init__(self, *args, **kwargs):
        self.opponent = None
        super().__init__(*args, **kwargs)

    def calc_reward(self, battle: AbstractBattle) -> float:
        return 69.42

    def embed_battle(self, battle: AbstractBattle) -> List[int]:
        return [0, 1, 2]


def test_init_queue():
    q = _AsyncQueue(asyncio.Queue())
    assert isinstance(q, _AsyncQueue)


def test_queue():
    q = _AsyncQueue(asyncio.Queue())
    assert q.empty()
    q.put(1)
    assert q.queue.qsize() == 1
    asyncio.get_event_loop().run_until_complete(q.async_put(2))
    assert q.queue.qsize() == 2
    item = q.get()
    q.queue.task_done()
    assert q.queue.qsize() == 1
    assert item == 1
    item = asyncio.get_event_loop().run_until_complete(q.async_get())
    q.queue.task_done()
    assert q.empty()
    assert item == 2
    asyncio.get_event_loop().run_until_complete(q.async_join())
    q.join()


def test_async_player():
    def embed_battle(battle):
        return "battle"

    player = _EnvPlayer(username="usr", start_listening=False)
    battle = Battle("bat1", player.username, player.logger, gen=8)
    player.order_queue.put(ForfeitBattleOrder())
    asyncio.get_event_loop().run_until_complete(player._env_move(battle))
    assert embed_battle(player.battle_queue.get()) == "battle"


def render(battle):
    player = DummyEnv(start_listening=False)
    captured_output = StringIO()
    sys.stdout = captured_output
    player.battle1 = battle
    player.render()
    sys.stdout = sys.__stdout__
    return captured_output.getvalue()


def test_render():
    battle = Battle("bat1", "usr", None, gen=8)
    battle._turn = 3
    active_mon = Pokemon(species="charizard", gen=8)
    active_mon._active = True
    battle._team = {"1": active_mon}
    opponent_mon = Pokemon(species="pikachu", gen=8)
    opponent_mon._active = True
    battle._opponent_team = {"1": opponent_mon}
    expected = "  Turn    3. | [●][  0/  0hp]  charizard -    pikachu [  0%hp][●]\r"
    assert render(battle) == expected
    active_mon._max_hp = 120
    active_mon._current_hp = 60
    expected = "  Turn    3. | [●][ 60/120hp]  charizard -    pikachu [  0%hp][●]\r"
    assert render(battle) == expected
    opponent_mon._current_hp = 20
    expected = "  Turn    3. | [●][ 60/120hp]  charizard -    pikachu [ 20%hp][●]\r"
    assert render(battle) == expected
    other_mon = Pokemon(species="pichu", gen=8)
    battle._team["2"] = other_mon
    expected = "  Turn    3. | [●●][ 60/120hp]  charizard -    pikachu [ 20%hp][●]\r"
    assert render(battle) == expected
