from typing import Any, Awaitable, Dict, Optional, Tuple

from gymnasium import Env

from poke_env.environment.env import ActionType, ObsType, PokeEnv
from poke_env.player.player import Player


class SingleAgentWrapper(Env[Dict[str, ObsType], ActionType]):
    def __init__(self, env: PokeEnv[ObsType, ActionType], opponent: Player):
        self.env = env
        self.opponent = opponent
        self.observation_space = env.observation_spaces[env.possible_agents[0]]
        self.action_space = env.action_spaces[env.possible_agents[0]]

    def step(
        self, action: ActionType
    ) -> Tuple[Dict[str, ObsType], float, bool, bool, Dict[str, Any]]:
        assert self.env.battle2 is not None
        opp_order = self.opponent.choose_move(self.env.battle2)
        assert not isinstance(opp_order, Awaitable)
        opp_action = self.env.order_to_action(
            opp_order, self.env.battle2, fake=self.env.fake, strict=self.env.strict
        )
        actions = {
            self.env.agent1.username: action,
            self.env.agent2.username: opp_action,
        }
        obs, rewards, terms, truncs, infos = self.env.step(actions)
        return (
            obs[self.env.agent1.username],
            rewards[self.env.agent1.username],
            terms[self.env.agent1.username],
            truncs[self.env.agent1.username],
            infos[self.env.agent1.username],
        )

    def reset(
        self,
        *,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, ObsType], Dict[str, Any]]:
        obs, infos = self.env.reset(seed, options)
        self._np_random = self.env._np_random
        return (
            obs[self.env.agent1.username],
            infos[self.env.agent1.username],
        )

    def render(self, mode="human"):
        return self.env.render(mode)

    def close(self):
        self.env.close()
