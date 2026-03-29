.. _reinforcement_learning:

Reinforcement learning with Stable-Baselines3
==============================================

The corresponding complete source code can be found `here <https://github.com/hsahovic/poke-env/blob/master/examples/reinforcement_learning.py>`__.

The goal of this example is to demonstrate how to use the ``PokeEnv`` environment with `Stable-Baselines3 <https://stable-baselines3.readthedocs.io/>`__ to train a reinforcement learning agent that plays ``gen9randombattle`` with action masking.

.. note:: This example requires `stable-baselines3 <https://github.com/DLR-RM/stable-baselines3>`__ and `PyTorch <https://pytorch.org/>`__. You can install them by running ``pip install stable-baselines3``.

Prerequisites
*************

- A local Pokémon Showdown server is strongly recommended for training runs.
- Install ``stable-baselines3`` and PyTorch before running the full example.
- If you are new to ``poke-env``, read :doc:`quickstart` first.

Defining the environment
************************

The environment is built by subclassing ``SinglesEnv``. We need to define three things: the observation space, the observation embedding, and the reward function.

``SinglesEnv`` automatically provides action masking via ``get_action_mask``, action-to-order conversion via ``action_to_order``, and the action space. We only need to define how we observe and reward battles.

Defining observations
^^^^^^^^^^^^^^^^^^^^^

Observations are embeddings of the current battle state. In this example, we create a 12-component vector containing:

- the base power of each available move (4 values)
- the damage multiplier of each available move against the opponent's active pokemon (4 values)
- the fraction of fainted pokemon in each team (2 values)
- the current HP fraction of each active pokemon (2 values)

We define a static ``embed_battle`` method on a ``PolicyPlayer`` class so it can be shared between the environment and the evaluation player.

.. code-block:: python

    N_FEATURES = 12

    class PolicyPlayer(Player):
        @staticmethod
        def embed_battle(battle: AbstractBattle):
            moves_base_power = -np.ones(4)
            moves_dmg_multiplier = np.ones(4)
            for i, move in enumerate(battle.available_moves):
                moves_base_power[i] = move.base_power / 100
                if battle.opponent_active_pokemon is not None:
                    moves_dmg_multiplier[i] = move.type.damage_multiplier(
                        battle.opponent_active_pokemon.type_1,
                        battle.opponent_active_pokemon.type_2,
                        type_chart=GenData.from_gen(battle.gen).type_chart,
                    )
            fainted_mon_team = len([mon for mon in battle.team.values() if mon.fainted]) / 6
            fainted_mon_opponent = (
                len([mon for mon in battle.opponent_team.values() if mon.fainted]) / 6
            )
            our_hp = (
                battle.active_pokemon.current_hp_fraction if battle.active_pokemon else 0.0
            )
            opp_hp = (
                battle.opponent_active_pokemon.current_hp_fraction
                if battle.opponent_active_pokemon
                else 0.0
            )
            return np.concatenate(
                [
                    moves_base_power,
                    moves_dmg_multiplier,
                    [fainted_mon_team, fainted_mon_opponent],
                    [our_hp, opp_hp],
                ],
                dtype=np.float32,
            )

Defining rewards
^^^^^^^^^^^^^^^^

Rewards are signals that the agent uses during optimization. ``PokeEnv`` provides a ``reward_computing_helper`` method that computes symmetric rewards based on fainted pokemon, remaining HP, status conditions, and victory.

We define the following reward scheme:

- Winning: +30
- Opponent pokemon fainting: +2
- Opponent losing HP: proportional positive reward
- Status conditions on opponents: +0.5

Negative actions lead to symmetrically negative rewards.

Defining the environment class
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Our environment subclasses ``SinglesEnv`` and defines the observation space, reward, and embedding:

.. code-block:: python

    BATTLE_FORMAT = "gen9randombattle"

    class ExampleEnv(SinglesEnv):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.observation_spaces = {
                agent: Box(-1, 4, shape=(N_FEATURES,), dtype=np.float32)
                for agent in self.possible_agents
            }

        @classmethod
        def create_env(cls) -> Monitor:
            env = cls(battle_format=BATTLE_FORMAT, log_level=40, open_timeout=None)
            opponent = SimpleHeuristicsPlayer(start_listening=False)
            return Monitor(SingleAgentWrapper(env, opponent))

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

The ``create_env`` classmethod wraps the environment with ``SingleAgentWrapper`` (which converts the two-agent ``PokeEnv`` into a single-agent Gymnasium environment) and ``Monitor`` (for SB3 logging). The opponent is a ``SimpleHeuristicsPlayer`` that doesn't need its own server connection.

Action masking with Stable-Baselines3
*************************************

``PokeEnv`` environments automatically provide observations as dicts with ``"observation"`` and ``"action_mask"`` keys. To use the action mask during training, we need a custom policy that applies the mask to the action distribution.

Features extractor
^^^^^^^^^^^^^^^^^^

SB3 uses a features extractor to preprocess observations before passing them to the policy network. Since the observation space is a dict, we need a custom extractor that pulls out the ``"observation"`` tensor and declares the correct ``features_dim``:

.. code-block:: python

    class FeaturesExtractor(BaseFeaturesExtractor):
        """Extracts the observation tensor from the dict obs and declares
        features_dim so SB3 builds the MLP with the right input size.
        """

        def __init__(self, observation_space):
            super().__init__(observation_space, features_dim=N_FEATURES)

        def forward(self, obs):
            return obs["observation"]

Masked policy
^^^^^^^^^^^^^

We subclass ``ActorCriticPolicy`` to intercept the action mask from the observation dict and apply it as ``-inf`` masking on the action logits, ensuring the agent never selects illegal actions:

.. code-block:: python

    class MaskedActorCriticPolicy(ActorCriticPolicy):
        def __init__(self, *args, **kwargs):
            super().__init__(
                *args,
                **kwargs,
                net_arch=[64, 64],
                features_extractor_class=FeaturesExtractor,
            )

        def forward(self, obs, deterministic=False):
            self._mask = obs["action_mask"]
            return super().forward(obs, deterministic)

        def evaluate_actions(self, obs, actions):
            self._mask = obs["action_mask"]
            return super().evaluate_actions(obs, actions)

        def _get_action_dist_from_latent(self, latent_pi):
            action_logits = self.action_net(latent_pi)
            mask = torch.where(self._mask == 1, 0, float("-inf"))
            return self.action_dist.proba_distribution(action_logits + mask)

The ``forward`` and ``evaluate_actions`` overrides stash the mask before delegating to the parent. Then ``_get_action_dist_from_latent`` applies it: legal actions (mask == 1) keep their logits, illegal actions get ``-inf``, making their probability zero.

Training
********

We use ``SubprocVecEnv`` to run multiple environments in parallel for faster data collection, and train with PPO:

.. code-block:: python

    def train():
        num_envs = 2
        env = SubprocVecEnv([ExampleEnv.create_env for _ in range(num_envs)])
        ppo = PPO(
            MaskedActorCriticPolicy,
            env,
            learning_rate=3e-4,
            n_steps=3072 // num_envs,
            batch_size=128,
            gamma=0.99,
            ent_coef=0.01,
            device="cpu",
        )

        ppo.learn(98_304)
        env.close()

Evaluation
**********

After training, we wrap the learned policy in a ``PolicyPlayer`` — a standard ``Player`` subclass that uses the trained policy to select actions. It constructs the same observation dict the policy expects and calls ``SinglesEnv.action_to_order`` to convert the chosen action index back into a battle order:

.. code-block:: python

    class PolicyPlayer(Player):
        def choose_move(self, battle):
            if battle.wait:
                return DefaultBattleOrder()
            obs = self.embed_battle(battle)
            mask = np.array(SinglesEnv.get_action_mask(battle))
            with torch.no_grad():
                obs_dict = {
                    "observation": torch.as_tensor(
                        obs, device=self.policy.device
                    ).unsqueeze(0),
                    "action_mask": torch.as_tensor(
                        mask, device=self.policy.device
                    ).unsqueeze(0),
                }
                action, _, _ = self.policy.forward(obs_dict)
            action = action.cpu().numpy()[0]
            return SinglesEnv.action_to_order(action, battle)

Note that ``SinglesEnv.get_action_mask`` and ``SinglesEnv.action_to_order`` are static methods — they can be called without an environment instance, using only the battle state.

We then evaluate against three baseline opponents:

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

Running the `complete example <https://github.com/hsahovic/poke-env/blob/master/examples/reinforcement_learning.py>`__ should take a few minutes and print win rates against each opponent.
