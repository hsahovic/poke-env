from typing import Any, Awaitable, Dict, Optional, Tuple

from gymnasium import Env

from poke_env.player.env import ActionType, ObsType, PokeEnv
from poke_env.player.player import Player


class SingleAgentWrapper(Env[ObsType, ActionType]):
    def __init__(self, env: PokeEnv[ObsType, ActionType], opponent: Player):
        self.env = env
        self.opponent = opponent
        self.observation_space = list(env.observation_spaces.values())[0]
        self.action_space = list(env.action_spaces.values())[0]

    def step(
        self, action: ActionType
    ) -> Tuple[ObsType, float, bool, bool, Dict[str, Any]]:
        assert self.env.agent2.battle is not None
        opp_order = self.opponent.choose_move(self.env.agent2.battle)
        assert not isinstance(opp_order, Awaitable)
        opp_action = self.env.order_to_action(
            opp_order,
            self.env.agent2.battle,
            fake=self.env._fake,
            strict=self.env._strict,
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
    ) -> Tuple[ObsType, Dict[str, Any]]:
        obs, infos = self.env.reset(seed, options)
        self._np_random = self.env._np_random
        return obs[self.env.agent1.username], infos[self.env.agent1.username]

    def render(self, mode="human"):
        return self.env.render(mode)

    def close(self):
        self.env.close()
