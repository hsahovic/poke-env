# -*- coding: utf-8 -*-

#this file is not yet functional
import numpy as np
import tensorflow as tf
from poke_env.player_configuration import PlayerConfiguration
from poke_env.player.env_player import Gen7EnvSinglePlayer
from poke_env.player.random_player import RandomPlayer
from poke_env.server_configuration import LocalhostServerConfiguration

from rl.agents.dqn import DQNAgent
from rl.agents.ddpg import DDPGAgent
from rl.policy import LinearAnnealedPolicy, EpsGreedyQPolicy
from rl.random import OrnsteinUhlenbeckProcess
from rl.memory import SequentialMemory
from tensorflow.keras.layers import Dense, Flatten, Activation, Input, Concatenate
from tensorflow.keras.models import Sequential, Model
from tf.optimizers import RMSprop



# We define our RL player
# It needs a state embedder and a reward computer, hence these two methods
class SimpleRLPlayer(Gen7EnvSinglePlayer):
    def embed_battle(self, battle):
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

        # We count how many pokemons have not fainted in each team
        remaining_mon_team = (
            len([mon for mon in battle.team.values() if mon.fainted]) / 6
        )
        remaining_mon_opponent = (
            len([mon for mon in battle.opponent_team.values() if mon.fainted]) / 6
        )

        # Final vector with 10 components
        return np.concatenate(
            [
                moves_base_power,
                moves_dmg_multiplier,
                [remaining_mon_team, remaining_mon_opponent],
            ]
        )

    def compute_reward(self, battle) -> float:
        return self.reward_computing_helper(
            battle, fainted_value=2, hp_value=1, victory_value=30
        )


class MaxDamagePlayer(RandomPlayer):
    def choose_move(self, battle):
        # If the player can attack, it will
        if battle.available_moves:
            # Finds the best move among available ones
            best_move = max(battle.available_moves, key=lambda move: move.base_power)
            return self.create_order(best_move)

        # If no attack is available, a random switch will be made
        else:
            return self.choose_random_move(battle)


NB_TRAINING_STEPS = 10000
NB_EVALUATION_EPISODES = 100

tf.random.set_seed(0)
np.random.seed(0)


# This is the function that will be used to train the dqn
def dqn_training(player, dqn, nb_steps):
    dqn.fit(player, nb_steps=nb_steps)
    player.complete_current_battle()


def dqn_evaluation(player, dqn, nb_episodes):
    # Reset battle statistics
    player.reset_battles()
    dqn.test(player, nb_episodes=nb_episodes, visualize=False, verbose=False)

    print(
        "DQN Evaluation: %d victories out of %d episodes"
        % (player.n_won_battles, nb_episodes)
    )


if __name__ == "__main__":
    env_player = SimpleRLPlayer(
        player_configuration=PlayerConfiguration("satunicarina", "L.M.Montgomery7"),
        battle_format="gen7randombattle",
        server_configuration=LocalhostServerConfiguration,
    )

    opponent = RandomPlayer(
        player_configuration=PlayerConfiguration("duanicarina", "L.M.Montgomery7"),
        battle_format="gen7randombattle",
        server_configuration=LocalhostServerConfiguration,
    )

    second_opponent = MaxDamagePlayer(
        player_configuration=PlayerConfiguration("tiganicarina", "L.M.Montgomery7"),
        battle_format="gen7randombattle",
        server_configuration=LocalhostServerConfiguration,
    )

    # Output dimension
    n_action = len(env_player.action_space)

    model = Sequential()
    model.add(Dense(128, activation="elu", input_shape=(1, 10)))

    # Our embedding have shape (1, 10), which affects our hidden layer
    # dimension and output dimension
    # Flattening resolve potential issues that would arise otherwise
    model.add(Flatten())
    model.add(Dense(64, activation="elu"))
    model.add(Dense(n_action, activation="linear"))

    memory = SequentialMemory(limit=10000, window_length=1)

    # Ssimple epsilon greedy
    policy = LinearAnnealedPolicy(
        EpsGreedyQPolicy(),
        attr="eps",
        value_max=1.0,
        value_min=0.05,
        value_test=0,
        nb_steps=10000,
    )
    
    actor = Sequential()
    actor.add(Dense(128, activation="elu", input_shape=(1, 10)))
    actor.add(Flatten())
    actor.add(Dense(16))
    actor.add(Activation('relu'))
    actor.add(Dense(16))
    actor.add(Activation('relu'))
    actor.add(Dense(16))
    actor.add(Activation('relu'))
    actor.add(Dense(n_action))
    actor.add(Activation('linear'))

    action_input = Input(shape=(n_action,), name='action_input')
    observation_input = Input(shape=(1, 10), name='observation_input')
    flattened_observation = Flatten()(observation_input)
    x = Concatenate()([action_input, flattened_observation])
    x = Dense(32)(x)
    x = Activation('relu')(x)
    x = Dense(32)(x)
    x = Activation('relu')(x)
    x = Dense(32)(x)
    x = Activation('relu')(x)
    x = Dense(1)(x)
    x = Activation('linear')(x)
    critic = Model(inputs=[action_input, observation_input], outputs=x)

    # Defining our DDPG
    memory = SequentialMemory(limit=100000, window_length=1)
    random_process = OrnsteinUhlenbeckProcess(size=n_action, theta=.15, mu=0., sigma=.3)
    dqn = DDPGAgent(nb_actions=n_action, actor=actor, critic=critic, critic_action_input=action_input,
                memory=memory, nb_steps_warmup_critic=100, nb_steps_warmup_actor=100,
                random_process=random_process, gamma=.99, target_model_update=1e-3)

#def q_loss(data, qvals):
#    """Computes the MSE between the Q-values of the actions that were taken and    the cumulative discounted
#        rewards obtained after taking those actions. Updates trace priorities if using PrioritizedExperienceReplay.
#        """
#    target_qvals = data[:, 0, np.newaxis]
#    if isinstance(self.memory, memory.PrioritizedExperienceReplay):
#        def update_priorities(_qvals, _target_qvals, _traces_idxs):
#            """Computes the TD error and updates memory priorities."""
#            td_error = np.abs((_target_qvals - _qvals).numpy())[:, 0]
#            _traces_idxs = (tf.cast(_traces_idxs, tf.int32)).numpy()
#            self.memory.update_priorities(_traces_idxs, td_error)
#            return _qvals
#        qvals = tf.py_function(func=update_priorities, inp=[qvals, target_qvals, data[:, 1]], Tout=tf.float32)
#    return MSE(target_qvals, qvals)
    dqn.compile(optimizer=RMSprop(), metrics=['mae'])

    # Training
    env_player.play_against(
        env_algorithm=dqn_training,
        opponent=opponent,
        env_algorithm_kwargs={"dqn": dqn, "nb_steps": NB_TRAINING_STEPS},
    )
    model.save("model_%d" % NB_TRAINING_STEPS)

    # Evaluation
    print("Results against random player:")
    env_player.play_against(
        env_algorithm=dqn_evaluation,
        opponent=opponent,
        env_algorithm_kwargs={"dqn": dqn, "nb_episodes": NB_EVALUATION_EPISODES},
    )

    print("\nResults against max player:")
    env_player.play_against(
        env_algorithm=dqn_evaluation,
        opponent=second_opponent,
        env_algorithm_kwargs={"dqn": dqn, "nb_episodes": NB_EVALUATION_EPISODES},
    )
