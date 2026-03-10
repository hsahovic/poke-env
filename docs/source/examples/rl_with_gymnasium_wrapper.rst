.. _rl_with_gymnasium_wrapper:

Reinforcement learning with the Gymnasium wrapper
=================================================

A complete, up-to-date example is available in
`examples/reinforcement_learning.py <https://github.com/hsahovic/poke-env/blob/master/examples/reinforcement_learning.py>`__.

This example uses the current environment API:

- ``SinglesEnv`` for a PettingZoo-compatible multi-agent environment.
- ``SingleAgentWrapper`` to expose a standard Gymnasium single-agent interface.

Defining observations and rewards
*********************************

Create a custom environment by subclassing ``SinglesEnv`` and implementing:

- ``embed_battle``: convert a battle state into a numeric observation.
- ``calc_reward``: return a scalar reward for the current battle state.

.. code-block:: python

    import numpy as np
    import numpy.typing as npt
    from gymnasium.spaces import Box

    from poke_env.battle import AbstractBattle, Battle
    from poke_env.data import GenData
    from poke_env.environment import SinglesEnv


    class ExampleEnv(SinglesEnv[npt.NDArray[np.float32]]):
        LOW = [-1, -1, -1, -1, 0, 0, 0, 0, 0, 0]
        HIGH = [3, 3, 3, 3, 4, 4, 4, 4, 1, 1]

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.observation_spaces = {
                agent: Box(
                    np.array(self.LOW, dtype=np.float32),
                    np.array(self.HIGH, dtype=np.float32),
                    dtype=np.float32,
                )
                for agent in self.possible_agents
            }

        def calc_reward(self, battle: AbstractBattle) -> float:
            return self.reward_computing_helper(
                battle, fainted_value=2.0, hp_value=1.0, victory_value=30.0
            )

        def embed_battle(self, battle: AbstractBattle) -> npt.NDArray[np.float32]:
            assert isinstance(battle, Battle)
            data = GenData.from_gen(battle.gen)

            moves_base_power = -np.ones(4, dtype=np.float32)
            moves_dmg_multiplier = np.ones(4, dtype=np.float32)

            for i, move in enumerate(battle.available_moves):
                moves_base_power[i] = np.float32(move.base_power / 100)
                if battle.opponent_active_pokemon is not None:
                    moves_dmg_multiplier[i] = np.float32(
                        move.type.damage_multiplier(
                            battle.opponent_active_pokemon.type_1,
                            battle.opponent_active_pokemon.type_2,
                            type_chart=data.type_chart,
                        )
                    )

            fainted_mon_team = np.float32(
                len([mon for mon in battle.team.values() if mon.fainted]) / 6
            )
            fainted_mon_opponent = np.float32(
                len([mon for mon in battle.opponent_team.values() if mon.fainted]) / 6
            )

            return np.concatenate(
                [
                    moves_base_power,
                    moves_dmg_multiplier,
                    np.array([fainted_mon_team, fainted_mon_opponent], dtype=np.float32),
                ]
            )

Single-agent training
*********************

For single-agent training, wrap the environment with ``SingleAgentWrapper`` and provide
an opponent ``Player`` implementation.

.. code-block:: python

    from poke_env.environment import SingleAgentWrapper
    from poke_env.player import RandomPlayer

    env = ExampleEnv(battle_format="gen9randombattle", strict=False)
    opponent = RandomPlayer(start_listening=False)
    train_env = SingleAgentWrapper(env, opponent)

Multi-agent training
********************

For multi-agent training, use ``ExampleEnv`` directly and plug it into a PettingZoo-compatible
trainer. ``examples/reinforcement_learning.py`` demonstrates this with RLlib.

Notes
*****

- Prefer ``strict=False`` while prototyping action encoders/decoders.
- Call ``env.close()`` to cleanly stop battles and release resources.
- For complete runnable training loops (single-agent and multi-agent), see
  ``examples/reinforcement_learning.py``.
