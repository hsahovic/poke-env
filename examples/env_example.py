import numpy as np
import numpy.typing as npt
from gymnasium.spaces import Box
from pettingzoo.test.parallel_test import parallel_api_test
from typing import Any, Dict, Tuple, TypeVar

from poke_env.environment.abstract_battle import AbstractBattle
from poke_env.player import SinglesEnv

ObsType = TypeVar("ObsType")
ActionType = TypeVar("ActionType")



class TestEnv(SinglesEnv[npt.NDArray[np.float32]]):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.observation_spaces = {
            agent: Box(np.array([0, 0]), np.array([6, 6]), dtype=np.float32)
            for agent in self.possible_agents
        }

    def calc_reward(self, battle) -> float:
        return self.reward_computing_helper(battle)

    def step(self, actions: Dict[str, ActionType]) -> Tuple[
        Dict[str, ObsType],
        Dict[str, float],
        Dict[str, bool],
        Dict[str, bool],
        Dict[str, Dict[str, Any]],
    ]:
        assert self.battle1 is not None
        assert self.battle2 is not None
        assert not self.battle1.finished
        assert not self.battle2.finished
        if self.agent1_to_move:
            self.agent1_to_move = False
            order1 = self.action_to_order(
                actions[self.agents[0]],
                self.battle1,
                fake=self.fake,
                strict=False,
            )
            self.agent1.order_queue.put(order1)
        if self.agent2_to_move:
            self.agent2_to_move = False
            order2 = self.action_to_order(
                actions[self.agents[1]],
                self.battle2,
                fake=self.fake,
                strict=False,
            )
            self.agent2.order_queue.put(order2)
        battle1 = self.agent1.battle_queue.race_get(
            self.agent1._waiting, self.agent2._trying_again
        )
        battle2 = self.agent2.battle_queue.race_get(
            self.agent2._waiting, self.agent1._trying_again
        )
        self.agent1_to_move = battle1 is not None
        self.agent2_to_move = battle2 is not None
        self.agent1._waiting.clear()
        self.agent2._waiting.clear()
        if battle1 is None:
            self.agent2._trying_again.clear()
            battle1 = self.battle1
        if battle2 is None:
            self.agent1._trying_again.clear()
            battle2 = self.battle2
        observations = {
            self.agents[0]: self.embed_battle(battle1),
            self.agents[1]: self.embed_battle(battle2),
        }
        reward = {
            self.agents[0]: self.calc_reward(battle1),
            self.agents[1]: self.calc_reward(battle2),
        }
        term1, trunc1 = self.calc_term_trunc(battle1)
        term2, trunc2 = self.calc_term_trunc(battle2)
        terminated = {self.agents[0]: term1, self.agents[1]: term2}
        truncated = {self.agents[0]: trunc1, self.agents[1]: trunc2}
        if battle1.finished:
            self.agents = []
        return observations, reward, terminated, truncated, self.get_additional_info()

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
        battle_format="gen9randombattle",
        start_challenging=True,
    )
    parallel_api_test(gymnasium_env)
    gymnasium_env.close()
