from types import SimpleNamespace
from unittest.mock import MagicMock

import numpy as np
import pytest
from gymnasium.spaces import Box, Discrete

from poke_env.environment import SingleAgentWrapper
from poke_env.player import DefaultBattleOrder, SingleBattleOrder


def _battle(*, wait=False, teampreview=False, format_="gen9randombattle"):
    return SimpleNamespace(
        wait=wait,
        teampreview=teampreview,
        format=format_,
        battle_tag="battle-tag",
        team={i: SimpleNamespace(_selected_in_teampreview=False) for i in range(1, 7)},
    )


def _env(battle2=None):
    agent1 = SimpleNamespace(username="agent-1")
    agent2 = SimpleNamespace(username="agent-2")
    env = SimpleNamespace(
        agent1=agent1,
        agent2=agent2,
        observation_spaces={
            agent1.username: Box(0, 1, shape=(2,)),
            agent2.username: Box(0, 1, shape=(2,)),
        },
        action_spaces={agent1.username: Discrete(3), agent2.username: Discrete(3)},
        battle2=battle2 or _battle(),
        _fake=True,
        _strict=False,
        _np_random=MagicMock(),
    )

    def order_to_action(order, battle, *, fake, strict):
        return f"action-for-{order.message}"

    env.order_to_action = MagicMock(side_effect=order_to_action)
    env.step = MagicMock(
        return_value=(
            {
                agent1.username: {"obs": "agent-1-obs"},
                agent2.username: {"obs": "agent-2-obs"},
            },
            {agent1.username: 1.5, agent2.username: -1.5},
            {agent1.username: False, agent2.username: False},
            {agent1.username: False, agent2.username: False},
            {
                agent1.username: {"info": "agent-1-info"},
                agent2.username: {"info": "agent-2-info"},
            },
        )
    )
    env.reset = MagicMock(
        return_value=(
            {
                agent1.username: {"obs": "reset-agent-1"},
                agent2.username: {"obs": "reset-agent-2"},
            },
            {
                agent1.username: {"info": "reset-agent-1"},
                agent2.username: {"info": "reset-agent-2"},
            },
        )
    )
    env.render = MagicMock(side_effect=lambda mode="human": f"rendered-{mode}")
    env.close = MagicMock()
    return env


def test_init_copies_main_agent_spaces_and_sets_spec():
    env = _env()
    opponent = MagicMock()

    wrapper = SingleAgentWrapper(env, opponent)

    assert wrapper.env is env
    assert wrapper.opponent is opponent
    assert wrapper.observation_space is env.observation_spaces[env.agent1.username]
    assert wrapper.action_space is env.action_spaces[env.agent1.username]
    assert wrapper.spec.id == "poke-env-v0"
    assert wrapper.spec.nondeterministic


def test_reset_returns_main_agent_values_and_registers_opponent_battle():
    env = _env()
    opponent = MagicMock()
    opponent._battles = {"old": object()}
    opponent.reset_battles.side_effect = lambda: opponent._battles.clear()
    wrapper = SingleAgentWrapper(env, opponent)

    obs, info = wrapper.reset(seed=123, options={"x": "y"})

    env.reset.assert_called_once_with(123, {"x": "y"})
    assert obs == {"obs": "reset-agent-1"}
    assert info == {"info": "reset-agent-1"}
    opponent.reset_battles.assert_called_once_with()
    assert opponent._battles == {env.battle2.battle_tag: env.battle2}
    assert wrapper._np_random is env._np_random


def test_step_uses_default_order_when_opponent_is_waiting():
    env = _env(_battle(wait=True))
    opponent = MagicMock()
    wrapper = SingleAgentWrapper(env, opponent)

    obs, reward, terminated, truncated, info = wrapper.step(np.int64(2))

    opponent.choose_move.assert_not_called()
    order_to_action_args = env.order_to_action.call_args
    assert isinstance(order_to_action_args.args[0], DefaultBattleOrder)
    assert order_to_action_args.args[1] is env.battle2
    assert order_to_action_args.kwargs == {"fake": True, "strict": False}
    assert env.step.call_args.args[0] == {
        env.agent1.username: np.int64(2),
        env.agent2.username: "action-for-/choose default",
    }
    assert (obs, reward, terminated, truncated, info) == (
        {"obs": "agent-1-obs"},
        1.5,
        False,
        False,
        {"info": "agent-1-info"},
    )


def test_step_uses_opponent_choose_move_on_regular_turn():
    env = _env(_battle(wait=False, teampreview=False))
    opponent = MagicMock()
    opponent.choose_move.return_value = SingleBattleOrder("/choose move 1")
    wrapper = SingleAgentWrapper(env, opponent)

    wrapper.step(1)

    opponent.choose_move.assert_called_once_with(env.battle2)
    assert env.order_to_action.call_args.args[0] == opponent.choose_move.return_value
    assert env.step.call_args.args[0] == {
        env.agent1.username: 1,
        env.agent2.username: "action-for-/choose move 1",
    }


def test_vgc_teampreview_is_split_across_two_steps():
    env = _env(_battle(teampreview=True, format_="gen9vgc2024regg"))
    opponent = MagicMock()
    opponent.teampreview.return_value = "/team 1234"
    wrapper = SingleAgentWrapper(env, opponent)

    wrapper.step(np.array([1, 2]))

    opponent.teampreview.assert_called_once_with(env.battle2)
    np.testing.assert_array_equal(
        env.step.call_args.args[0][env.agent2.username], np.array([1, 2])
    )
    assert wrapper.second_teampreview_action is not None
    np.testing.assert_array_equal(wrapper.second_teampreview_action, np.array([3, 4]))
    assert [mon._selected_in_teampreview for mon in env.battle2.team.values()] == [
        True,
        True,
        False,
        False,
        False,
        False,
    ]

    wrapper.step(np.array([3, 4]))

    np.testing.assert_array_equal(
        env.step.call_args.args[0][env.agent2.username], np.array([3, 4])
    )
    assert wrapper.second_teampreview_action is None
    assert [mon._selected_in_teampreview for mon in env.battle2.team.values()] == [
        True,
        True,
        True,
        True,
        False,
        False,
    ]


def test_non_vgc_teampreview_raises_not_implemented():
    env = _env(_battle(teampreview=True, format_="gen9ou"))
    opponent = MagicMock()
    wrapper = SingleAgentWrapper(env, opponent)

    with pytest.raises(NotImplementedError, match="Teampreview is only supported"):
        wrapper.step(0)


def test_render_and_close_delegate_to_wrapped_env():
    env = _env()
    wrapper = SingleAgentWrapper(env, MagicMock())

    assert wrapper.render("ansi") == "rendered-ansi"
    wrapper.close()
    env.render.assert_called_once_with("ansi")
    env.close.assert_called_once_with()
