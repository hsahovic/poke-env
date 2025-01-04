import numpy as np
import pytest
from gymnasium.spaces import Box
from pettingzoo.test.parallel_test import parallel_api_test

from poke_env.player import PokeEnv


class CIEnv(PokeEnv):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.observation_spaces = {
            agent: Box(np.array([0]), np.array([1]), dtype=np.int64)
            for agent in self.possible_agents
        }

    def calc_reward(self, battle) -> float:
        return 0.0

    def embed_battle(self, battle):
        return np.array([0])


def play_function(env, n_battles):
    for _ in range(n_battles):
        done = False
        env.reset()
        while not done:
            actions = {name: env.action_space(name).sample() for name in env.agents}
            _, _, terminated, truncated, _ = env.step(actions)
            done = any(terminated.values()) or any(truncated.values())


@pytest.mark.timeout(30)
def test_random_gymnasium_players_gen4():
    env = CIEnv(battle_format="gen4randombattle", log_level=25, start_challenging=False)
    env.start_challenging(3)
    play_function(env, 3)


@pytest.mark.timeout(30)
def test_random_gymnasium_players_gen5():
    env = CIEnv(battle_format="gen5randombattle", log_level=25, start_challenging=False)
    env.start_challenging(3)
    play_function(env, 3)


@pytest.mark.timeout(30)
def test_random_gymnasium_players_gen6():
    env = CIEnv(battle_format="gen6randombattle", log_level=25, start_challenging=False)
    env.start_challenging(3)
    play_function(env, 3)


@pytest.mark.timeout(30)
def test_random_gymnasium_players_gen7():
    env = CIEnv(battle_format="gen7randombattle", log_level=25, start_challenging=False)
    env.start_challenging(3)
    play_function(env, 3)


@pytest.mark.timeout(30)
def test_random_gymnasium_players_gen8():
    env = CIEnv(battle_format="gen8randombattle", log_level=25, start_challenging=False)
    env.start_challenging(3)
    play_function(env, 3)


@pytest.mark.timeout(30)
def test_random_gymnasium_players_gen9():
    env = CIEnv(battle_format="gen9randombattle", log_level=25, start_challenging=False)
    env.start_challenging(3)
    play_function(env, 3)


@pytest.mark.timeout(30)
def test_random_gymnasium_player_vgc():
    env = CIEnv(battle_format="gen9vgc2024regh", log_level=25, start_challenging=False)
    env.start_challenging(3)
    play_function(env, 3)


@pytest.mark.timeout(60)
def test_two_successive_calls_gen8():
    env = CIEnv(battle_format="gen8randombattle", log_level=25, start_challenging=False)
    env.start_challenging(2)
    play_function(env, 2)
    env.start_challenging(2)
    play_function(env, 2)


@pytest.mark.timeout(60)
def test_two_successive_calls_gen9():
    env = CIEnv(battle_format="gen9randombattle", log_level=25, start_challenging=False)
    env.start_challenging(2)
    play_function(env, 2)
    env.start_challenging(2)
    play_function(env, 2)


@pytest.mark.timeout(60)
def test_check_envs():
    env_gen4 = CIEnv(
        battle_format="gen4randombattle", log_level=25, start_challenging=True
    )
    parallel_api_test(env_gen4)
    env_gen4.close()
    env_gen5 = CIEnv(
        battle_format="gen5randombattle", log_level=25, start_challenging=True
    )
    parallel_api_test(env_gen5)
    env_gen5.close()
    env_gen6 = CIEnv(
        battle_format="gen6randombattle", log_level=25, start_challenging=True
    )
    parallel_api_test(env_gen6)
    env_gen6.close()
    env_gen7 = CIEnv(
        battle_format="gen7randombattle", log_level=25, start_challenging=True
    )
    parallel_api_test(env_gen7)
    env_gen7.close()
    env_gen8 = CIEnv(
        battle_format="gen8randombattle", log_level=25, start_challenging=True
    )
    parallel_api_test(env_gen8)
    env_gen8.close()
    env_gen9 = CIEnv(
        battle_format="gen9randombattle", log_level=25, start_challenging=True
    )
    parallel_api_test(env_gen9)
    env_gen9.close()
    env_vgc = CIEnv(
        battle_format="gen9vgc2024regh", log_level=25, start_challenging=True
    )
    parallel_api_test(env_vgc)
    env_vgc.close()
