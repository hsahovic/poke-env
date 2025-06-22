import numpy as np
import numpy.typing as npt
from gymnasium.spaces import Box
from pettingzoo.test.parallel_test import parallel_api_test

from poke_env.environment.abstract_battle import AbstractBattle
from poke_env.player import SinglesEnv


class TestEnv(SinglesEnv[npt.NDArray[np.float32]]):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.observation_spaces = {
            agent: Box(np.array([0, 0]), np.array([6, 6]), dtype=np.float32)
            for agent in self.possible_agents
        }

    def calc_reward(self, battle) -> float:
        return self.reward_computing_helper(battle)

    def embed_battle(self, battle: AbstractBattle):
        to_embed = []
        fainted_mons = 0
        for mon in battle.team.values():
            if mon.fainted:
                fainted_mons += 1
        to_embed.append(fainted_mons)
        fainted_enemy_mons = 0
        for mon in battle.opponent_team.values():
            if mon.fainted:
                fainted_enemy_mons += 1
        to_embed.append(fainted_enemy_mons)
        return np.array(to_embed)


if __name__ == "__main__":
    gymnasium_env = TestEnv(
        battle_format="gen8randombattle",
    )
    parallel_api_test(gymnasium_env)
    gymnasium_env.close()
