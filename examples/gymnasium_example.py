import numpy as np
from gymnasium.spaces import Box
from pettingzoo.test.parallel_test import parallel_api_test

from poke_env import LocalhostServerConfiguration
from poke_env.player import RandomPlayer, SinglesEnv


class ExampleEnv(SinglesEnv):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.observation_spaces = {
            agent: Box(
                low=np.array([1, 1, float("-inf")]),
                high=np.array([2, 4, float("+inf")]),
                dtype=np.float64,
            )
            for agent in self.possible_agents
        }

    def embed_battle(self, battle):
        return np.array([1.0, 2.0, 3.0], dtype=np.float64)

    def calc_reward(self, battle):
        return 0.25


def gymnasium_api():
    gymnasium_env = ExampleEnv(
        battle_format="gen8randombattle",
        server_configuration=LocalhostServerConfiguration,
        start_challenging=True,
    )
    parallel_api_test(gymnasium_env)
    gymnasium_env.close()


def against_random_player():
    env = ExampleEnv(
        battle_format="gen8randombattle",
        server_configuration=LocalhostServerConfiguration,
        start_challenging=True,
    )
    random_player = RandomPlayer(battle_format="gen8randombattle")
    for _ in range(3):
        done = False
        env.reset()
        while not done:
            assert env.battle2 is not None
            actions = {
                env.agents[0]: env.action_space(env.agents[0]).sample(),
                env.agents[1]: env.order_to_action(
                    random_player.choose_move(env.battle2), env.battle2
                ),
            }
            _, _, terminated, truncated, _ = env.step(actions)
            done = any(terminated.values()) or any(truncated.values())


if __name__ == "__main__":
    gymnasium_api()
