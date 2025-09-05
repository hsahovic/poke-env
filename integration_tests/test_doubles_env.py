import numpy as np
import pytest
from gymnasium.spaces import Box
from gymnasium.utils.env_checker import check_env
from pettingzoo.test.parallel_test import parallel_api_test

from poke_env.environment import DoublesEnv, SingleAgentWrapper
from poke_env.player import Player, RandomPlayer


class DoublesTestEnv(DoublesEnv):
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
        # TODO: when Zoroark isn't a problem anymore this can be removed
        if "illusion" in [
            p.ability
            for p in list(env.battle1.team.values()) + list(env.battle2.team.values())
        ]:
            continue
        while not done:
            actions = {
                name: (
                    env.order_to_action(Player.choose_random_move(battle), battle)
                    if env.strict
                    else env.action_space(name).sample()
                )
                for name, battle in zip(env.agents, [env.battle1, env.battle2])
            }
            _, _, terminated, truncated, _ = env.step(actions)
            done = any(terminated.values()) or any(truncated.values())


@pytest.mark.timeout(120)
def test_env_run():
    for gen in range(8, 10):
        env = DoublesTestEnv(
            battle_format=f"gen{gen}randomdoublesbattle",
            log_level=25,
            strict_battle_tracking=True,
        )
        play_function(env, 10)
        env.strict = False
        play_function(env, 10)
        env.close()


def single_agent_play_function(env: SingleAgentWrapper, n_battles: int):
    for _ in range(n_battles):
        done = False
        env.reset()
        # TODO: when Zoroark isn't a problem anymore this can be removed
        if "illusion" in [
            p.ability
            for p in list(env.env.battle1.team.values())
            + list(env.env.battle2.team.values())
        ]:
            continue
        while not done:
            action = (
                env.env.order_to_action(
                    Player.choose_random_move(env.env.battle1), env.env.battle1
                )
                if env.env.strict
                else env.action_space.sample()
            )
            _, _, terminated, truncated, _ = env.step(action)
            done = terminated or truncated


@pytest.mark.timeout(120)
def test_single_agent_env_run():
    for gen in range(8, 10):
        env = DoublesTestEnv(
            battle_format=f"gen{gen}randomdoublesbattle",
            log_level=25,
            strict_battle_tracking=True,
        )
        env = SingleAgentWrapper(env, RandomPlayer())
        single_agent_play_function(env, 10)
        env.env.strict = False
        single_agent_play_function(env, 10)
        env.close()


@pytest.mark.timeout(60)
def test_repeated_runs():
    env = DoublesTestEnv(
        battle_format="gen8randomdoublesbattle",
        log_level=25,
        strict=False,
        strict_battle_tracking=True,
    )
    play_function(env, 2)
    play_function(env, 2)
    env.close()
    env = DoublesTestEnv(
        battle_format="gen9randomdoublesbattle",
        log_level=25,
        strict=False,
        strict_battle_tracking=True,
    )
    play_function(env, 2)
    play_function(env, 2)
    env.close()


@pytest.mark.timeout(60)
def test_env_api():
    for gen in range(8, 10):
        env = DoublesTestEnv(
            battle_format=f"gen{gen}randomdoublesbattle", log_level=25, strict=False
        )
        parallel_api_test(env)
        env.close()


@pytest.mark.timeout(60)
def test_single_agent_env_api():
    for gen in range(8, 10):
        env = DoublesTestEnv(
            battle_format=f"gen{gen}randomdoublesbattle", log_level=25, strict=False
        )
        env = SingleAgentWrapper(env, RandomPlayer())
        check_env(env, skip_render_check=True)
        env.close()
