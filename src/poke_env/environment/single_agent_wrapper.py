from typing import Any, Awaitable, Dict, Optional, Tuple

import numpy as np
import numpy.typing as npt
from gymnasium import Env

from poke_env.environment.env import ActionType, ObsType, PokeEnv
from poke_env.player.player import Player


class SingleAgentWrapper(Env[ObsType, ActionType]):
    def __init__(self, env: PokeEnv[ObsType, ActionType], opponent: Player):
        self.env = env
        self.opponent = opponent
        self.observation_space = list(env.observation_spaces.values())[0]
        self.action_space = list(env.action_spaces.values())[0]
        self.second_teampreview_action: npt.NDArray[np.int64] | None = None

    def step(
        self, action: ActionType
    ) -> Tuple[ObsType, float, bool, bool, Dict[str, Any]]:
        """Run one timestep of the environment's dynamics.

        Takes an action from the main agent and automatically generates an action
        for the opponent using the opponent's choose_move method.

        :param action: Action from the main agent.
        :type action: ActionType
        :return: Tuple of (observation, reward, terminated, truncated, info) for the main agent.
        :rtype: Tuple[ObsType, float, bool, bool, Dict[str, Any]]
        """
        assert self.env.battle2 is not None
        if not self.env.battle2.teampreview:
            opp_order = self.opponent.choose_move(self.env.battle2)
            assert not isinstance(opp_order, Awaitable)
            opp_action = self.env.order_to_action(
                opp_order, self.env.battle2, fake=self.env.fake, strict=self.env.strict
            )
        elif self.env.battle2.format is None or "vgc" not in self.env.battle2.format:
            raise NotImplementedError(
                "Teampreview is only supported for VGC formats in SingleAgentWrapper."
            )
        elif self.second_teampreview_action is None:
            tp_order = self.opponent.teampreview(self.env.battle2)
            assert not isinstance(tp_order, Awaitable)
            assert len(tp_order) == 10, f"{tp_order} must specify 4 slots in VGC!"
            teampreview_order_list = [int(i) for i in tp_order[-4:]]
            opp_action = np.array(teampreview_order_list[:2])  # type: ignore
            self.second_teampreview_action = np.array(teampreview_order_list[2:])
            # only the first two pokemon are selected in teampreview for now
            for i, pokemon in enumerate(self.env.battle2.team.values(), start=1):
                pokemon._selected_in_teampreview = i in teampreview_order_list[:2]
        else:
            opp_action = self.second_teampreview_action  # type: ignore
            # now the second two pokemon are selected in teampreview
            for i in opp_action:  # type: ignore
                mon = list(self.env.battle2.team.values())[i - 1]
                mon._selected_in_teampreview = True
            self.second_teampreview_action = None
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
        self, *, seed: Optional[int] = None, options: Optional[Dict[str, Any]] = None
    ) -> Tuple[ObsType, Dict[str, Any]]:
        obs, infos = self.env.reset(seed, options)
        self.opponent.reset_battles()
        assert self.env.battle2 is not None
        self.opponent._battles[self.env.battle2.battle_tag] = self.env.battle2
        self._np_random = self.env._np_random
        return obs[self.env.agent1.username], infos[self.env.agent1.username]

    def render(self, mode="human"):
        return self.env.render(mode)

    def close(self):
        self.env.close()
