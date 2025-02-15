from typing import Any, Awaitable, Dict, Optional, Tuple

from gymnasium import Env

from poke_env.environment.double_battle import DoubleBattle
from poke_env.player.battle_order import BattleOrder
from poke_env.player.env import ActionType, ObsType, PokeEnv, _EnvPlayer
from poke_env.player.player import Player


class SingleAgentWrapper(Env[ObsType, ActionType]):
    def __init__(self, env: PokeEnv[ObsType, ActionType], opponent: Player):
        self.env = env
        self.opponent = opponent
        self.observation_space = list(env.observation_spaces.values())[0]
        self.action_space = list(env.action_spaces.values())[0]
        self.first_teampreview_order: Optional[BattleOrder] = None

    def step(
        self, action: ActionType
    ) -> Tuple[ObsType, float, bool, bool, Dict[str, Any]]:
        assert self.env.agent2.battle is not None
        if not self.env.agent2.battle.teampreview:
            battle = self.env.agent2.battle
            opp_order = self.opponent.choose_move(battle)
            assert not isinstance(opp_order, Awaitable)
        elif self.first_teampreview_order is None:
            battle = self.env.agent2.battle
            opp_order = self.opponent.choose_move(battle)
            assert not isinstance(opp_order, Awaitable)
            self.first_teampreview_order = opp_order
        else:
            assert isinstance(self.env.agent2.battle, DoubleBattle)
            battle = _EnvPlayer._simulate_teampreview_switchin(
                self.first_teampreview_order, self.env.agent2.battle
            )
            opp_order = self.opponent.choose_move(battle)
            assert not isinstance(opp_order, Awaitable)
            self.first_teampreview_order = None
        opp_action = self.env.order_to_action(opp_order, battle)
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

    def set_opp_policy(self, policy):
        self.opponent.set_policy(policy)  # type: ignore
