import random
import time

import numpy as np
import pytest
from gymnasium.spaces import Box

from poke_env.environment import SinglesEnv
from poke_env.player import RandomPlayer


class BenchEnv(SinglesEnv):
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


def sample_action(action_mask):
    available_actions = [i for i, m in enumerate(action_mask) if m == 1]
    return np.int64(random.choice(available_actions))


def run_battles(env, n_battles):
    steps = 0
    for _ in range(n_battles):
        done = False
        obs, _ = env.reset()
        while not done:
            actions = {
                name: sample_action(obs[name]["action_mask"]) for name in env.agents
            }
            obs, _, terminated, truncated, _ = env.step(actions)
            steps += 1
            done = any(terminated.values()) or any(truncated.values())
    return steps


@pytest.mark.timeout(120)
def test_env_benchmark():
    min_rate = 150
    env = BenchEnv(battle_format="gen9randombattle", log_level=40)
    # Warm up
    run_battles(env, 2)
    # Benchmark
    start = time.perf_counter()
    steps = run_battles(env, 100)
    elapsed = time.perf_counter() - start
    env.close()
    steps_per_second = steps / elapsed
    print(f"\n{steps} steps in {elapsed:.2f}s ({steps_per_second:.1f} steps/s)")
    assert steps_per_second > min_rate, (
        f"Environment too slow: {steps_per_second:.1f} steps/s "
        f"(minimum {min_rate} steps/s)"
    )


@pytest.mark.asyncio
@pytest.mark.timeout(120)
async def test_random_player_benchmark():
    min_rate = 150
    p1 = RandomPlayer(battle_format="gen9randombattle", log_level=40)
    p2 = RandomPlayer(battle_format="gen9randombattle", log_level=40)
    start = time.perf_counter()
    await p1.battle_against(p2, n_battles=100)
    elapsed = time.perf_counter() - start
    total_turns = sum(b.turn for b in p1.battles.values())
    await p1.ps_client.stop_listening()
    await p2.ps_client.stop_listening()
    steps_per_second = total_turns / elapsed
    print(f"\n{total_turns} steps in {elapsed:.2f}s ({steps_per_second:.1f} steps/s)")
    assert steps_per_second > min_rate, (
        f"RandomPlayer too slow: {steps_per_second:.1f} steps/s "
        f"(minimum {min_rate} steps/s)"
    )
