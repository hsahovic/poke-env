# self-play training is a planned feature for poke-env
# This script illustrates a very rough approach that can currently be used to train using self-play
# Don't hesitate to open an issue if things seem not to be working

import numpy as np
from gym.spaces import Space, Box
from poke_env.environment import AbstractBattle
from poke_env.player import Gen8EnvSinglePlayer
from threading import Thread


class RandomGen8EnvPlayer(Gen8EnvSinglePlayer):
    def embed_battle(self, battle):
        return np.array([0])

    def calc_reward(
        self, last_battle: AbstractBattle, current_battle: AbstractBattle
    ) -> float:
        return self.reward_computing_helper(current_battle, fainted_value=1.0, hp_value=0.1, victory_value=10.0)

    def describe_embedding(self) -> Space:
        return Box(low=0, high=1, shape=(1,))


def train_function(player, opponent, battles):
    for _ in range(battles):
        done = False
        player.reset()
        while not done:
            action = player.action_space.sample()
            step, reward, terminated, truncated, info = player.step(action)
            done = terminated or truncated
        player.finish_training = True
    while not opponent.finish_training or not player.agent.current_battle.finished:
        if player.current_battle.finished and not player.agent.current_battle.finished:
            player.reset()
        done = False
        while not done:
            action = player.action_space.sample()
            step, reward, terminated, truncated, info = player.step(action)
            done = terminated or truncated


N_CHALLENGES = 5

p1 = RandomGen8EnvPlayer(log_level=25, opponent=None)
p2 = RandomGen8EnvPlayer(log_level=25, opponent=None)
p1.set_opponent(p2.agent)
p2.set_opponent(p1.agent)
p1.start_challenging()
p1.finish_training = False
p2.finish_training = False

t1 = Thread(target=lambda: train_function(p1, p2, N_CHALLENGES))
t1.start()

t2 = Thread(target=lambda: train_function(p2, p1, N_CHALLENGES))
t2.start()

t1.join()
t2.join()

p1.close()
p2.close()
