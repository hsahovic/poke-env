import numpy as np

from gym.spaces import Box
from gym.utils.env_checker import check_env

from poke_env.player.openai_player import OpenAIPlayer, stop_loop
from poke_env.player.random_player import RandomPlayer
from poke_env.server_configuration import LocalhostServerConfiguration


class TestEnv(OpenAIPlayer):

    def __init__(self, **kwargs):
        self.opponent = RandomPlayer(battle_format='gen8randombattle',
                                     server_configuration=LocalhostServerConfiguration)
        super().__init__(**kwargs)

    def action_space_size(self):
        return 21

    def embed_battle(self, battle):
        return np.array([1.0, 2.0, 3.0], dtype=np.float64)

    def describe_embedding(self):
        return Box(low=np.array([1, 1, float('-inf')]), high=np.array([2, 4, float('+inf')]), dtype=np.float64)

    def action_to_move(self, action, battle):
        return self.agent.choose_random_move(battle)

    def calc_reward(self, last_battle, current_battle):
        return 0.25

    def get_opponent(self):
        return self.opponent


if __name__ == '__main__':
    env = TestEnv(battle_format='gen8randombattle', server_configuration=LocalhostServerConfiguration)
    check_env(env)
    env.close()
    stop_loop()
