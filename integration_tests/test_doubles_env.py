import random

import gymnasium.spaces as spaces
import numpy as np
import pytest
from gymnasium.utils.env_checker import check_env

from poke_env.environment import DoublesEnv, SingleAgentWrapper
from poke_env.player import RandomPlayer


class DoublesTestEnv(DoublesEnv):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.observation_spaces = {
            agent: spaces.Dict(
                {
                    "observation": spaces.Box(
                        np.array([0]), np.array([1]), dtype=np.int64
                    ),
                    "action_mask": spaces.Box(
                        0, 1, shape=(2 * self.action_space_size,), dtype=np.int64
                    ),
                }
            )
            for agent in self.possible_agents
        }

    def calc_reward(self, battle) -> float:
        return 0.0

    def embed_battle(self, battle):
        return np.array([0])


def play_function(env, n_battles):
    for _ in range(n_battles):
        done = False
        obs_dict, _ = env.reset()
        # TODO: when Zoroark isn't a problem anymore this can be removed
        if "illusion" in [
            p.ability
            for p in list(env.battle1.team.values()) + list(env.battle2.team.values())
        ]:
            continue
        while not done:
            actions = {
                name: (
                    sample_action(obs_dict[name]["action_mask"])
                    if env.strict
                    else env.action_space(name).sample()
                )
                for name in env.agents
            }
            obs_dict, _, terminated, truncated, _ = env.step(actions)
            done = any(terminated.values()) or any(truncated.values())


@pytest.mark.timeout(120)
def test_env_run():
    for gen in range(8, 10):
        env = DoublesTestEnv(battle_format=f"gen{gen}randomdoublesbattle", log_level=25)
        play_function(env, 10)
        env.strict = False
        play_function(env, 10)
        env.close()


def single_agent_play_function(env: SingleAgentWrapper, n_battles: int):
    for _ in range(n_battles):
        done = False
        obs, _ = env.reset()
        # TODO: when Zoroark isn't a problem anymore this can be removed
        if "illusion" in [
            p.ability
            for p in list(env.env.battle1.team.values())
            + list(env.env.battle2.team.values())
        ]:
            continue
        while not done:
            action = (
                sample_action(obs["action_mask"])
                if env.env.strict
                else env.action_space.sample()
            )
            obs, _, terminated, truncated, _ = env.step(action)
            done = terminated or truncated


@pytest.mark.timeout(120)
def test_single_agent_env_run():
    for gen in range(8, 10):
        env = DoublesTestEnv(battle_format=f"gen{gen}randomdoublesbattle", log_level=25)
        env = SingleAgentWrapper(env, RandomPlayer())
        single_agent_play_function(env, 10)
        env.env.strict = False
        single_agent_play_function(env, 10)
        env.close()


def sample_action(action_mask):
    n = len(action_mask)
    action_mask1 = action_mask[: n // 2]
    action_mask2 = action_mask[n // 2 :]
    available_actions1 = [i for i, m in enumerate(action_mask1) if m == 1]
    available_actions2 = [i for i, m in enumerate(action_mask2) if m == 1]
    action1 = random.choice(available_actions1)
    available_actions2 = [
        i
        for i in available_actions2
        if not (1 <= action1 <= 6 and action1 == i)
        and not (26 < action1 <= 46 and 26 < i <= 46)
        and not (46 < action1 <= 66 and 46 < i <= 66)
        and not (66 < action1 <= 86 and 66 < i <= 86)
        and not (86 < action1 <= 106 and 86 < i <= 106)
    ]
    action2 = random.choice(available_actions2)
    return np.array([action1, action2])


@pytest.mark.timeout(60)
def test_repeated_runs():
    env = DoublesTestEnv(
        battle_format="gen8randomdoublesbattle",
        log_level=25,
        strict=False,
    )
    play_function(env, 2)
    play_function(env, 2)
    env.close()
    env = DoublesTestEnv(
        battle_format="gen9randomdoublesbattle",
        log_level=25,
        strict=False,
    )
    play_function(env, 2)
    play_function(env, 2)
    env.close()


@pytest.mark.timeout(60)
def test_single_agent_env_api():
    for gen in range(8, 10):
        env = DoublesTestEnv(
            battle_format=f"gen{gen}randomdoublesbattle", log_level=25, strict=False
        )
        env = SingleAgentWrapper(env, RandomPlayer())
        check_env(env)
        env.close()
