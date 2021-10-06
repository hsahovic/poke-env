import gym

from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.vec_env.base_vec_env import VecEnv
from stable_baselines3.common.vec_env.subproc_vec_env import SubprocVecEnv
import battler # registers gym env
import battler.players
from poke_env.player.baselines import MaxBasePowerPlayer
#from poke_env.player.env_player import LOOP
import asyncio
import numpy as np
from icecream import ic

def train():
    env = make_vec_env(
        'Pokemon-v8', 
        n_envs=4,
        env_kwargs={
            "battler_embedder": lambda _: np.array([0., 0.1, 2., 0.1])
        },
        vec_env_cls=SubprocVecEnv
    )

    model = PPO('MlpPolicy', env, verbose=1)
    model.learn(total_timesteps=10000)

    obs = env.reset()
    for i in range(1000):
        action, _state = model.predict(obs, deterministic=True)
        obs, reward, done, info = env.step(action)
        env.render()
        if done:
            obs = env.reset()

if __name__ == '__main__':
    train()