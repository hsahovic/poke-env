.. _rl_with_gymnasium_wrapper:

Reinforcement learning with the Gymnasium wrapper
==================================================

The corresponding complete source code can be found `here <https://github.com/hsahovic/poke-env/blob/master/examples/rl_with_new_gymnasium_wrapper.py>`__.

The goal of this example is to demonstrate how to use the `farama gymnasium <https://gymnasium.farama.org/>`__ interface proposed by ``PokeEnv``, and to train a simple deep reinforcement learning agent.

.. note:: This example necessitates `keras-rl <https://github.com/keras-rl/keras-rl>`__ (compatible with Tensorflow 1.X) or `keras-rl2 <https://github.com/wau/keras-rl2>`__ (Tensorflow 2.X), which implement numerous reinforcement learning algorithms and offer a simple API fully compatible with the Gymnasium API. You can install them by running ``pip install keras-rl`` or ``pip install keras-rl2``. If you are unsure, ``pip install keras-rl2`` is recommended.

Implementing rewards and observations
*************************************

The Gymnasium API provides *rewards* and *observations* for each step of each episode. In our case, each step corresponds to one decision in a battle and battles correspond to episodes.

Defining observations
^^^^^^^^^^^^^^^^^^^^^

Observations are embeddings of the current state of the battle. They can be an arbitrarily precise description of battle states, or a very simple representation. In this example, we will create embedding vectors containing:

- the base power of each available move
- the damage multiplier of each available move against the current active opponent pokemon
- the number of non fainted pokemons in our team
- the number of non fainted pokemons in the opponent's team

To define our observations, we will create a custom ``embed_battle`` method. It takes one argument, a ``Battle`` object, and returns our embedding.

In addition to this, we also need to describe the embedding to the gymnasium interface.
To achieve this, we need to initialize the ``observation_spaces`` field in the ``__init__`` method where we specify the low bound and the high bound
for each component of the embedding vector and return them as a ``gymnasium.Space`` object.

Defining rewards
^^^^^^^^^^^^^^^^

Rewards are signals that the agent will use in its optimization process (a common objective is optimizing a discounted total reward). ``PokeEnv`` objects provide a helper method, ``reward_computing_helper``, that can help defining simple symmetric rewards that take into account fainted pokemons, remaining hp, status conditions and victory.

We will use this method to define the following reward:

- Winning corresponds to a positive reward of 30
- Making an opponent's pokemon faint corresponds to a positive reward of 1
- Making an opponent lose % hp corresponds to a positive reward of %
- Other status conditions are ignored

Conversely, negative actions lead to symmetrically negative rewards: losing is a reward of -30 points, etc.

To define our rewards, we will create a custom ``compute_reward`` method. It takes one argument, a ``Battle`` object, and returns the reward.

Defining our custom class
^^^^^^^^^^^^^^^^^^^^^^^^^

Our player will play the ``gen8randombattle`` format. We can therefore inherit from ``Gen8EnvSinglePlayer``.

.. code-block:: python

        import numpy as np
    from gymnasium.spaces import Space, Box
    from poke_env.player import Gen8EnvSinglePlayer

    class SimpleRLPlayer(Gen8EnvSinglePlayer):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            low = [-1, -1, -1, -1, 0, 0, 0, 0, 0, 0]
            high = [3, 3, 3, 3, 4, 4, 4, 4, 1, 1]
            self.observation_spaces = {
                agent: Box(
                    np.array(low, dtype=np.float32),
                    np.array(high, dtype=np.float32),
                    dtype=np.float32,
                )
                for agent in self.possible_agents
            }

        def calc_reward(self, battle) -> float:
            return self.reward_computing_helper(
                battle, fainted_value=2.0, hp_value=1.0, victory_value=30.0
            )

        def embed_battle(self, battle: AbstractBattle) -> ObservationType:
            # -1 indicates that the move does not have a base power
            # or is not available
            moves_base_power = -np.ones(4)
            moves_dmg_multiplier = np.ones(4)
            for i, move in enumerate(battle.available_moves):
                moves_base_power[i] = (
                    move.base_power / 100
                )  # Simple rescaling to facilitate learning
                if move.type:
                    moves_dmg_multiplier[i] = move.type.damage_multiplier(
                        battle.opponent_active_pokemon.type_1,
                        battle.opponent_active_pokemon.type_2,
                    )

            # We count how many pokemons have fainted in each team
            fainted_mon_team = len([mon for mon in battle.team.values() if mon.fainted]) / 6
            fainted_mon_opponent = (
                len([mon for mon in battle.opponent_team.values() if mon.fainted]) / 6
            )

            # Final vector with 10 components
            final_vector = np.concatenate(
                [
                    moves_base_power,
                    moves_dmg_multiplier,
                    [fainted_mon_team, fainted_mon_opponent],
                ]
            )
            return np.float32(final_vector)

    ...

Instantiating and testing a player
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Now that our custom class is defined, we can instantiate our RL player and test if it's compliant with the Gymnasium API.

.. code-block:: python

    ...
    from gymnasium.utils.env_checker import check_env
    from poke_env.player import RandomPlayer

    opponent = RandomPlayer(battle_format="gen8randombattle")
    test_env = SimpleRLPlayer(
        battle_format="gen8randombattle", opponent=opponent
    )
    check_env(test_env)
    test_env.close()
    ...

The ``close`` method of ``test_env`` closes all underlying processes and clears from memory all objects related to the environment.
After an environment is closed, no further actions should be taken on that environment.

Instantiating train environment and evaluation environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Normally, to ensure isolation between training and testing, two different environments are created.

.. code-block:: python

    ...
    from poke_env.player import RandomPlayer

    opponent = RandomPlayer(battle_format="gen8randombattle")
    train_env = SimpleRLPlayer(
        battle_format="gen8randombattle", opponent=opponent
    )
    opponent = RandomPlayer(battle_format="gen8randombattle")
    eval_env = SimpleRLPlayer(
        battle_format="gen8randombattle", opponent=opponent
    )
    ...

Creating a DQN with keras-rl
****************************

We have defined observations and rewards. We can now build a model that will control our player. In this section, we will implement the `DQN algorithm <https://web.stanford.edu/class/psych209/Readings/MnihEtAlHassibis15NatureControlDeepRL.pdf>`__ using `keras-rl <https://github.com/keras-rl/keras-rl>`__.

Defining a base model
^^^^^^^^^^^^^^^^^^^^^

We build a simple keras sequential model. Our observation vectors have 10 components; our model will therefore accept inputs of dimension 10.

The output of the model must map to the environment's action space. The action space can be accessed through the ``action_space`` property. Each action correspond to one order: a switch or an attack, with additional options for dynamaxing, mega-evolving and using z-moves.

.. code-block:: python

    ...
    from tensorflow.keras.layers import Dense, Flatten
    from tensorflow.keras.models import Sequential

    # Compute dimensions
    n_action = train_env.action_space.n
    input_shape = (1,) + train_env.observation_space.shape # (1,) is the batch size that the model expects in input.

    # Create model
    model = Sequential()
    model.add(Dense(128, activation="elu", input_shape=input_shape))
    model.add(Flatten())
    model.add(Dense(64, activation="elu"))
    model.add(Dense(n_action, activation="linear"))
    ...

Defining the DQN
^^^^^^^^^^^^^^^^

Now that we have a model, we can build the DQN agent. This agent combines our model with a *policy* and a *memory*. The *memory* is an object that will store past actions and define samples used during learning. The *policy* describes how actions are chosen during learning.

We will use a simple memory containing 10000 steps, and an epsilon greedy policy.

For more information regarding keras-rl, please refer to their `documentation <https://keras-rl.readthedocs.io/en/latest/>`__.

.. code-block:: python

    ...
    from rl.agents.dqn import DQNAgent
    from rl.memory import SequentialMemory
    from rl.policy import LinearAnnealedPolicy, EpsGreedyQPolicy
    from tensorflow.keras.optimizers import Adam

    # Defining the DQN
    memory = SequentialMemory(limit=10000, window_length=1)

    policy = LinearAnnealedPolicy(
        EpsGreedyQPolicy(),
        attr="eps",
        value_max=1.0,
        value_min=0.05,
        value_test=0.0,
        nb_steps=10000,
    )

    dqn = DQNAgent(
        model=model,
        nb_actions=n_action,
        policy=policy,
        memory=memory,
        nb_steps_warmup=1000,
        gamma=0.5,
        target_model_update=1,
        delta_clip=0.01,
        enable_double_dqn=True,
    )
    dqn.compile(Adam(learning_rate=0.00025), metrics=["mae"])
    ...


Training the model
******************

Training the model is as simple as

.. code-block:: python

    ...
    dqn.fit(train_env, nb_steps=10000)
    train_env.close()
    ...


Evaluating the model
********************

We have trained our agent. Now we can use different strategies to evaluate the result.

Simple win rate evaluation
^^^^^^^^^^^^^^^^^^^^^^^^^^

A first way to evaluate the result is having it play against different agents and printing the won battles.
This can be done with the following code:

.. code-block:: python

    ...
    print("Results against random player:")
    dqn.test(eval_env, nb_episodes=100, verbose=False, visualize=False)
    print(
        f"DQN Evaluation: {eval_env.n_won_battles} victories out of {eval_env.n_finished_battles} episodes"
    )
    second_opponent = MaxBasePowerPlayer(battle_format="gen8randombattle")
    eval_env.reset_env(restart=True, opponent=second_opponent)
    print("Results against max base power player:")
    dqn.test(eval_env, nb_episodes=100, verbose=False, visualize=False)
    print(
        f"DQN Evaluation: {eval_env.n_won_battles} victories out of {eval_env.n_finished_battles} episodes"
    )
    ...

The ``reset_env`` method of the ``PokeEnv`` class allows you to reset the environment
to a clean state, including internal counters for victories, battles, etc.

It takes two optional parameters:

- ``restart``: a boolean that will tell the environment if the challenge loop is to be restarted after the reset;
- ``opponent``: the new opponent to use after the reset in the challenge loop. If empty it will keep old opponent.

Use provided ``evaluate_player`` method
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In order to evaluate the player with the provided method, we need to use a background version.
``background_evaluate_player`` has the same interface as the foreground counterpart, but it will return a
``Future`` object.

.. code-block:: python

    ...
    from poke_env.player import background_evaluate_player

    n_challenges = 250
    placement_battles = 40
    eval_task = background_evaluate_player(
        eval_env.agent, n_challenges, placement_battles
    )
    dqn.test(eval_env, nb_episodes=n_challenges, verbose=False, visualize=False)
    print("Evaluation with included method:", eval_task.result())
    ...

The ``result`` method of the ``Future`` object will block until the task is done and will return the result.

.. warning:: ``background_evaluate_player`` requires the challenge loop to be stopped. To ensure this use method ``reset_env(restart=False)`` of ``PokeEnv``.

.. warning:: If you call ``result`` before the task is finished, the main thread will be blocked. Only do that if the agent is operating on a different thread than the one asking for the result.

Use provided ``cross_evaluate`` method
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To use the ``cross_evaluate`` method, the strategy is the same to the one used for the ``evaluate_player`` method:

.. code-block:: python

    ...
    from poke_env.player import background_cross_evaluate

    n_challenges = 50
    players = [
        eval_env.agent,
        RandomPlayer(battle_format="gen8randombattle"),
        MaxBasePowerPlayer(battle_format="gen8randombattle"),
        SimpleHeuristicsPlayer(battle_format="gen8randombattle"),
    ]
    cross_eval_task = background_cross_evaluate(players, n_challenges)
    dqn.test(
        eval_env,
        nb_episodes=n_challenges * (len(players) - 1),
        verbose=False,
        visualize=False,
    )
    cross_evaluation = cross_eval_task.result()
    table = [["-"] + [p.username for p in players]]
    for p_1, results in cross_evaluation.items():
        table.append([p_1] + [cross_evaluation[p_1][p_2] for p_2 in results])
    print("Cross evaluation of DQN with baselines:")
    print(tabulate(table))
    ...

.. warning:: ``background_cross_evaluate`` requires the challenge loop to be stopped. To ensure this use method ``reset_env(restart=False)`` of ``PokeEnv``.

.. warning:: If you call ``result`` before the task is finished, the main thread will be blocked. Only do that if the agent is operating on a different thread than the one asking for the result.

Final result
************

Running the `whole file <https://github.com/hsahovic/poke-env/blob/master/examples/rl_with_gymnasium_wrapper.py>`__ should take a couple of minutes and print something similar to this:

.. code-block:: console

    Training for 10000 steps ...
    Interval 1 (0 steps performed)
    10000/10000 [==============================] - 194s 19ms/step - reward: 0.6015
    done, took 195.208 seconds
    Results against random player:
    DQN Evaluation: 94 victories out of 100 episodes
    Results against max base power player:
    DQN Evaluation: 65 victories out of 100 episodes
    Evaluation with included method: (16.028896545454547, (11.79801006617441, 22.609978288238203))
    Cross evaluation of DQN with baselines:
    ------------------  ----------------  --------------  ------------------  ------------------
    -                   SimpleRLPlayer 3  RandomPlayer 5  MaxBasePowerPlay 3  SimpleHeuristics 2
    SimpleRLPlayer 3                      0.96            0.76                0.16
    RandomPlayer 5      0.04                              0.12                0.0
    MaxBasePowerPlay 3  0.24              0.88                                0.1
    SimpleHeuristics 2  0.84              1.0             0.9
    ------------------  ----------------  --------------  ------------------  ------------------

.. warning:: Remember to use ``reset_env`` between different evaluations on the same environment or use different environments to avoid interferences between evaluations.
