from typing import Any, Awaitable, Dict, Optional, Tuple

from gymnasium import Env

from poke_env.environment.abstract_battle import AbstractBattle
from poke_env.player.battle_order import BattleOrder
from poke_env.player.env import ActionType, ObsType, PokeEnv, _EnvPlayer
from poke_env.player.player import Player


class _EnvPlayerWrapper(_EnvPlayer):
    def __init__(self, agent: _EnvPlayer, player: Player):
        self.agent = agent
        self.agent._env_move = self._env_move  # type: ignore [method-assign]
        self.player = player

    def __getattr__(self, name: str):
        return getattr(self.agent, name)

    async def _env_move(self, battle: AbstractBattle) -> BattleOrder:
        await _EnvPlayer._env_move(self.agent, battle)
        order = self.player.choose_move(battle)
        if isinstance(order, Awaitable):
            order = await order
        return order


class SingleAgentWrapper(Env[ObsType, ActionType]):
    def __init__(self, env: PokeEnv[ObsType, ActionType], opponent: Player):
        self.env = env
        self.env.agent2 = _EnvPlayerWrapper(self.env.agent2, opponent)
        self.observation_space = list(env.observation_spaces.values())[0]
        self.action_space = list(env.action_spaces.values())[0]

    def step(
        self, action: ActionType
    ) -> Tuple[ObsType, float, bool, bool, Dict[str, Any]]:
        actions = {
            self.env.agent1.username: action,
            self.env.agent2.username: self.action_space.sample(),
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
