from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import Dense, Input, Concatenate

import matplotlib.pyplot as plt
import gym

import huskarl as hk

if __name__ == "__main__":
    
    # Setup gym environment
    create_env = lambda: gym.make('Pendulum-v0')
    dummy_env = create_env()
    action_size = dummy_env.action_space.shape[0]
    state_shape = dummy_env.observation_space.shape
    
    # Build a simple actor model
    actor = Sequential([
                        Dense(16, activation='relu', input_shape=state_shape),
                        Dense(16, activation='relu'),
                        Dense(16, activation='relu'),
                        Dense(action_size, activation='linear')
                        ])
        
    # Build a simple critic model
    action_input = Input(shape=(action_size,), name='action_input')
    state_input = Input(shape=state_shape, name='state_input')
    x = Concatenate()([action_input, state_input])
    x = Dense(32, activation='relu')(x)
    x = Dense(32, activation='relu')(x)
    x = Dense(32, activation='relu')(x)
    x = Dense(1, activation='linear')(x)
    critic = Model(inputs=[action_input, state_input], outputs=x)
    
    # Create Deep Deterministic Policy Gradient agent
    agent = hk.agent.DDPG(actor=actor, critic=critic, nsteps=2)
    
    def plot_rewards(episode_rewards, episode_steps, done=False):
        plt.clf()
        plt.xlabel('Step')
        plt.ylabel('Reward')
        for ed, steps in zip(episode_rewards, episode_steps):
            plt.plot(steps, ed)
            plt.show() if done else plt.pause(0.001) # Pause a bit so that the graph is updated

# Create simulation, train and then test
sim = hk.Simulation(create_env, agent)
sim.train(max_steps=30_000, visualize=True, plot=plot_rewards)
sim.test(max_steps=5_000)
