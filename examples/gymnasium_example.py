import numpy as np
from gymnasium import Space
from gymnasium.spaces import Box
from gymnasium.utils.env_checker import check_env

from poke_env import LocalhostServerConfiguration
from poke_env.environment.abstract_battle import AbstractBattle
from poke_env.player import (
    Gen8EnvSinglePlayer,
    GymnasiumEnv,
    ObservationType,
    RandomPlayer,
)


class TestEnv(GymnasiumEnv):
    def __init__(self, **kwargs):
        self.opponent = RandomPlayer(
            battle_format="gen8randombattle",
            server_configuration=LocalhostServerConfiguration,
        )
        super().__init__(**kwargs)

    def action_space_size(self):
        return 21

    def embed_battle(self, battle):
        return np.array([1.0, 2.0, 3.0], dtype=np.float64)

    def describe_embedding(self):
        return Box(
            low=np.array([1, 1, float("-inf")]),
            high=np.array([2, 4, float("+inf")]),
            dtype=np.float64,
        )

    def action_to_move(self, action, battle):
        return self.agent.choose_random_move(battle)

    def calc_reward(self, battle):
        return 0.25

    def get_opponent(self):
        return self.opponent


class Gen8(Gen8EnvSinglePlayer):
    def calc_reward(self, battle) -> float:
        return self.reward_computing_helper(battle)

    def embed_battle(self, battle: AbstractBattle) -> ObservationType:
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

    def describe_embedding(self) -> Space:
        return Box(np.array([0, 0]), np.array([6, 6]), dtype=int)


def gymnasium_api():
    gymnasium_env = TestEnv(
        battle_format="gen8randombattle",
        server_configuration=LocalhostServerConfiguration,
        start_challenging=True,
    )
    check_env(gymnasium_env)
    gymnasium_env.close()


def env_player():
    opponent = RandomPlayer(
        battle_format="gen8randombattle",
        server_configuration=LocalhostServerConfiguration,
    )
    gymnasium_env = Gen8(
        battle_format="gen8randombattle",
        server_configuration=LocalhostServerConfiguration,
        start_challenging=True,
        opponent=opponent,
    )
    check_env(gymnasium_env)
    gymnasium_env.close()


if __name__ == "__main__":
    gymnasium_api()
    env_player()
