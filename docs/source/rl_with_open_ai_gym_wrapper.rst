.. _rl_with_open_ai_gym_wrapper:

Reinforcement learning with the OpenAI Gym wrapper
==================================================

The corresponding complete source code can be found `here <https://github.com/hsahovic/poke-env/blob/master/examples/rl_with_open_ai_gym_wrapper.py>`__.

.. note::
    A similar example using gen 7 mechanics is available `here <https://github.com/hsahovic/poke-env/blob/master/examples/gen7/rl_with_open_ai_gym_wrapper.py>`__.

The goal of this example is to demonstrate how to use the `open ai gym <https://gym.openai.com/>`__ interface proposed by ``EnvPlayer``, and to train a simple deep reinforcement learning agent comparable in performance to the ``MaxDamagePlayer`` we created in :ref:`max_damage_player`.

.. note:: This example necessitates `keras-rl <https://github.com/keras-rl/keras-rl>`__ (compatible with Tensorflow 1.X) or `keras-rl2 <https://github.com/wau/keras-rl2>`__ (Tensorflow 2.X), which implement numerous reinforcement learning algorithms and offer a simple API fully compatible with the Open AI Gym API. You can install them by running ``pip install keras-rl`` or ``pip install keras-rl2``. If you are unsure, ``pip install keras-rl2`` is recommended.

.. warning:: ``keras-rl2`` version 1.0.4 seems to be causing problems with this example. While we are trying to find a workaround, please try using version 1.0.3 with python version 3.6.


Implementing rewards and observations
*************************************

The open ai gym API provides *rewards* and *observations* for each step of each episode. In our case, each step corresponds to one decision in a battle and battles correspond to episodes.

Defining observations
^^^^^^^^^^^^^^^^^^^^^

Observations are embeddings of the current state of the battle. They can be an arbitrarily precise description of battle states, or a very simple representation. In this example, we will create embedding vectors containing:

- the base power of each available move
- the damage multiplier of each available move against the current active opponent pokemon
- the number of non fainted pokemons in our team
- the number of non fainted pokemons in the opponent's team

To define our observations, we will create a custom ``embed_battle`` method. It takes one argument, a ``Battle`` object, and returns our embedding.

Defining rewards
^^^^^^^^^^^^^^^^

Rewards are signals that the agent will use in its optimization process (a common objective is optimizing a discounted total reward). ``EnvPlayer`` objects provide a helper method, ``reward_computing_helper``, that can help defining simple symmetric rewards that take into account fainted pokemons, remaining hp, status conditions and victory.

We will use this method to define the following reward:

- Winning corresponds to a positive reward of 30
- Making an opponent's pokemon faint corresponds to a positive reward of 1
- Making an opponent lose % hp corresponds to a positive reward of %
- Other status conditions are ignored

Conversly, negative actions lead to symettrically negative rewards: losing is a reward of -30 points, etc.

To define our rewards, we will create a custom ``compute_reward`` method. It takes one argument, a ``Battle`` object, and returns the reward.

Defining our custom class
^^^^^^^^^^^^^^^^^^^^^^^^^

Our player will play the ``gen8randombattle`` format. We can therefore inheritate from ``Gen8EnvSinglePlayer``.

.. code-block:: python

    # -*- coding: utf-8 -*-
    from poke_env.player.env_player import Gen8EnvSinglePlayer

    class SimpleRLPlayer(Gen8EnvSinglePlayer):
        def embed_battle(self, battle):
            # -1 indicates that the move does not have a base power
            # or is not available
            moves_base_power = -np.ones(4)
            moves_dmg_multiplier = np.ones(4)
            for i, move in enumerate(battle.available_moves):
                moves_base_power[i] = move.base_power / 100 # Simple rescaling to facilitate learning
                if move.type:
                    moves_dmg_multiplier[i] = move.type.damage_multiplier(
                        battle.opponent_active_pokemon.type_1,
                        battle.opponent_active_pokemon.type_2,
                    )

            # We count how many pokemons have not fainted in each team
            remaining_mon_team = len([mon for mon in battle.team.values() if mon.fainted]) / 6
            remaining_mon_opponent = (
                len([mon for mon in battle.opponent_team.values() if mon.fainted]) / 6
            )

            # Final vector with 10 components
            return np.concatenate(
                [moves_base_power, moves_dmg_multiplier, [remaining_mon_team, remaining_mon_opponent]]
            )

        def compute_reward(self, battle) -> float:
            return self.reward_computing_helper(
                battle,
                fainted_value=2,
                hp_value=1,
                victory_value=30,
            )

    ...

Instanciating a player
^^^^^^^^^^^^^^^^^^^^^^^

Now that our custom class is defined, we can instantiate our RL player.

.. code-block:: python

    ...
    env_player = SimpleRLPlayer(battle_format="gen8randombattle")
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

    # Output dimension
    n_action = len(env_player.action_space)

    model = Sequential()
    model.add(Dense(128, activation="elu", input_shape=(1, 10,)))

    # Our embedding have shape (1, 10), which affects our hidden layer dimension and output dimension
    # Flattening resolve potential issues that would arise otherwise
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

    memory = SequentialMemory(limit=10000, window_length=1)

    # Simple epsilon greedy
    policy = LinearAnnealedPolicy(
        EpsGreedyQPolicy(),
        attr="eps",
        value_max=1.0,
        value_min=0.05,
        value_test=0,
        nb_steps=10000,
    )

    # Defining our DQN
    dqn = DQNAgent(
        model=model,
        nb_actions=18,
        policy=policy,
        memory=memory,
        nb_steps_warmup=1000,
        gamma=0.5,
        target_model_update=1,
        delta_clip=0.01,
        enable_double_dqn=True,
    )

    dqn.compile(Adam(lr=0.00025), metrics=["mae"])
    ...


Training the model
******************

Accessing the open AI Gym environment interface requires interacting with env players in the main thread without preventing other asynchronous operations from happening. The easiest way to do that is to use the ``play_against`` method of ``EnvPlayer`` instances.

This method accepts three arguments:

- ``env_algorithm``: the function that will control the player. It must accept a first ``player`` argument, and can optionally take other arguments
- ``opponent``: another ``Player`` that will be faced by the ``env_player``
- ``env_algorithm_kwargs``: a dictionary containing other objects that will be passed to ``env_algorithm``

To train our agent, we will create a custom ``dqn_training`` function. In addition to the player, it will accept two additional arguments: ``dqn`` and ``nb_steps``. We can pass it in a call to ``play_against`` as the ``env_algorithm`` argument.

.. code-block:: python

    ...
    from poke_env.player.random_player import RandomPlayer

    def dqn_training(player, dqn, nb_steps):
        dqn.fit(player, nb_steps=nb_steps)

        # This call will finished eventual unfinshed battles before returning
        player.complete_current_battle()

    opponent = RandomPlayer(battle_format="gen8randombattle")

    # Training
    env_player.play_against(
        env_algorithm=dqn_training,
        opponent=opponent,
        env_algorithm_kwargs={"dqn": dqn, "nb_steps": 100000},
    )
    ...


Evaluating the model
********************

Similarly to the training function above, we can define an evaluation function.

.. code-block:: python

    ...
    def dqn_evaluation(player, dqn, nb_episodes):
        # Reset battle statistics
        player.reset_battles()
        dqn.test(player, nb_episodes=nb_episodes, visualize=False, verbose=False)

        print(
            "DQN Evaluation: %d victories out of %d episodes"
            % (player.n_won_battles, nb_episodes)
        )

    # Ths code of MaxDamagePlayer is not reproduced for brevity and legibility
    # It can be found in the complete code linked above, or in the max damage example
    second_opponent = MaxDamagePlayer(battle_format="gen8randombattle")

    # Evaluation
    print("Results against random player:")
    env_player.play_against(
        env_algorithm=dqn_evaluation,
        opponent=opponent,
        env_algorithm_kwargs={"dqn": dqn, "nb_episodes": 100},
    )

    print("\nResults against max player:")
    env_player.play_against(
        env_algorithm=dqn_evaluation,
        opponent=second_opponent,
        env_algorithm_kwargs={"dqn": dqn, "nb_episodes": 100},
    )
    ...


Running the `whole file <https://github.com/hsahovic/poke-env/blob/master/examples/rl_with_open_ai_gym_wrapper.py>`__ should take a couple of minutes and print something similar to this:

.. code-block:: python

    Training for 10000 steps ...
    Interval 1 (0 steps performed)
    10000/10000 [==============================] - 96s 10ms/step - reward: 0.6307
    done, took 96.233 seconds
    Results against random player:
    DQN Evaluation: 97 victories out of 100 episodes

    Results against max player:
    DQN Evaluation: 65 victories out of 100 episodes
