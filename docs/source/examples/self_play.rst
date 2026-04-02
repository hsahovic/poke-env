.. _self_play:

Self-play reinforcement learning with SuperSuit
================================================

The corresponding complete source code can be found `here <https://github.com/hsahovic/poke-env/blob/master/examples/self_play.py>`__.

The goal of this example is to demonstrate how to train an agent via **self-play** using `SuperSuit <https://github.com/Farama-Foundation/SuperSuit>`__ and `Stable-Baselines3 <https://stable-baselines3.readthedocs.io/>`__. Both sides of every battle are controlled by the same policy, so the agent continuously improves against itself.

.. note:: This example requires `stable-baselines3 <https://github.com/DLR-RM/stable-baselines3>`__, `SuperSuit <https://github.com/Farama-Foundation/SuperSuit>`__, and `PyTorch <https://pytorch.org/>`__. You can install them by running ``pip install stable-baselines3 supersuit``.

How it differs from the single-agent example
*********************************************

The :doc:`reinforcement_learning` example wraps the two-agent ``PokeEnv`` with ``SingleAgentWrapper``, which pairs the learning agent against a fixed opponent (e.g. ``SimpleHeuristicsPlayer``). In self-play, **both agents are controlled by the same policy**:

+---------------------------------------+---------------------------------------------+
| Single-agent RL                       | Self-play RL                                |
+=======================================+=============================================+
| ``SingleAgentWrapper(env, opponent)`` | ``ss.pettingzoo_env_to_vec_env(env)``       |
+---------------------------------------+---------------------------------------------+
| Fixed opponent (scripted bot)         | Both sides share the learning policy        |
+---------------------------------------+---------------------------------------------+
| Agent only sees its own perspective   | Both perspectives contribute to training    |
+---------------------------------------+---------------------------------------------+

Because ``PokeEnv`` implements PettingZoo's ``ParallelEnv`` API, SuperSuit can convert it directly into an SB3-compatible vectorized environment — no wrapper needed.

Prerequisites
*************

- A local Pokemon Showdown server is strongly recommended for training runs.
- Install ``stable-baselines3``, ``supersuit``, and PyTorch before running the full example.
- If you are new to ``poke-env``, read :doc:`quickstart` first.

Defining the environment
************************

The environment is identical to the single-agent example: we subclass ``SinglesEnv`` and define the observation space, embedding, and reward. The only difference is that we do **not** need a ``create_env`` classmethod since there is no ``SingleAgentWrapper`` or fixed opponent.

.. code-block:: python

    BATTLE_FORMAT = "gen9randombattle"
    N_FEATURES = 12

    class SelfPlayEnv(SinglesEnv):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.observation_spaces = {
                agent: Box(-1, 4, shape=(N_FEATURES,), dtype=np.float32)
                for agent in self.possible_agents
            }

        def calc_reward(self, battle) -> float:
            return self.reward_computing_helper(
                battle,
                fainted_value=2.0,
                hp_value=1.0,
                status_value=0.5,
                victory_value=30.0,
            )

        def embed_battle(self, battle: AbstractBattle):
            return PolicyPlayer.embed_battle(battle)

Each agent in the ``PokeEnv`` gets its own battle object with the correct perspective — "team" is always the agent's own team and "opponent_team" is the other side. This means the same ``embed_battle`` and ``calc_reward`` work symmetrically for both agents without any extra logic.

Converting with SuperSuit
*************************

SuperSuit converts the two-agent PettingZoo ``ParallelEnv`` into an SB3-compatible ``VecEnv``:

.. code-block:: python

    import supersuit as ss

    num_envs = 2
    env = SelfPlayEnv(battle_format=BATTLE_FORMAT, log_level=40, open_timeout=None)
    vec_env = ss.pettingzoo_env_to_vec_env(env)
    vec_env = ss.concat_vec_envs_v1(
        vec_env, num_vec_envs=num_envs, num_cpus=0, base_class="stable_baselines3"
    )

``pettingzoo_env_to_vec_env`` turns each agent into a sub-environment in a vectorized env. ``concat_vec_envs_v1`` stacks ``num_envs`` copies and wraps the result in an SB3-compatible ``VecEnv``, giving a total of ``num_envs * 2`` sub-environments (two agents per env). Setting ``num_cpus=0`` keeps everything in a single process.

Because both sub-environments feed into the same PPO policy, every battle generates training data from **both** perspectives — the agent learns from its wins and its losses simultaneously.

Training
********

Training proceeds exactly as in the single-agent example, using the same action masking policy:

.. code-block:: python

    ppo = PPO(
        MaskedActorCriticPolicy,
        vec_env,
        learning_rate=3e-4,
        n_steps=3072 // (2 * num_envs),
        batch_size=128,
        gamma=0.99,
        ent_coef=0.01,
        device="cpu",
    )

    ppo.learn(98_304)
    vec_env.close()

Evaluation
**********

After training, we evaluate the self-play agent against the same baselines as the single-agent example:

.. code-block:: python

    agent = PolicyPlayer(
        policy=ppo.policy, battle_format=BATTLE_FORMAT, max_concurrent_battles=10
    )
    opponents = [
        c(battle_format=BATTLE_FORMAT, max_concurrent_battles=10)
        for c in [RandomPlayer, MaxBasePowerPlayer, SimpleHeuristicsPlayer]
    ]
    asyncio.run(agent.battle_against(*opponents, n_battles=100))
    print("--- Win rates vs bots ---")
    for opp in opponents:
        win_rate = round(100 * opp.n_lost_battles / opp.n_finished_battles)
        print(f"{opp.username}: {win_rate}%")

Running the `complete example <https://github.com/hsahovic/poke-env/blob/master/examples/self_play.py>`__ should take a few minutes and print win rates against each opponent.
