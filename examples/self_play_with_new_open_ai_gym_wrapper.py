# -*- coding: utf-8 -*-

import asyncio
from threading import Thread

import numpy as np
from gym.spaces import Box, Space
from poke_env.player.env_player import Gen8EnvSinglePlayer
from poke_env.player_configuration import PlayerConfiguration


class SimpleRLPlayer(Gen8EnvSinglePlayer):
    def __init__(self, *args, **kwargs):
        super(SimpleRLPlayer, self).__init__(*args, **kwargs)
        self.done_training = False

    def calc_reward(self, last_battle, current_battle) -> float:
        return self.reward_computing_helper(
            current_battle, fainted_value=2.0, hp_value=1.0, victory_value=30.0
        )

    def describe_embedding(self) -> Space:
        low = [-1, -1, -1, -1, 0, 0, 0, 0, 0, 0]
        high = [3, 3, 3, 3, 4, 4, 4, 4, 1, 1]
        return Box(
            np.array(low, dtype=np.float32),
            np.array(high, dtype=np.float32),
            dtype=np.float32,
        )

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


async def battle_handler(player1, player2, num_challenges):
    await asyncio.gather(
        player1.agent.accept_challenges(player2.username, num_challenges),
        player2.agent.send_challenges(player1.username, num_challenges),
    )


def training_function(player, opponent, kwargs):
    state = player.reset()
    for i in range(kwargs["num_steps"]):
        action = np.random.randint(player.action_space.n)
        next_state, reward, done, _ = player.step(action)
        if done:
            state = player.reset()
        else:
            state = next_state
    player.done_training = True
    # Play out the remaining battles so both fit() functions complete
    # We use 99 to give the agent an invalid option so it's forced
    # to take a random legal action
    while not opponent.done_training:
        _, _, done, _ = player.step(99)
        if done and not opponent.done_training:
            _ = player.reset()
            done = False
    
    # Forfeit any ongoing battles
    while player.current_battle and not player.current_battle.finished:
        _ = player.step(-1)


if __name__ == "__main__":
    # Set random seed
    np.random.seed(42)

    player1 = SimpleRLPlayer(
        battle_format="gen8randombattle",
        player_configuration=PlayerConfiguration("Player 1", None),
        opponent="placeholder",
        start_challenging=False,
    )
    player2 = SimpleRLPlayer(
        battle_format="gen8randombattle",
        player_configuration=PlayerConfiguration("Player 2", None),
        opponent="placeholder",
        start_challenging=False,
    )

    # Setup arguments to pass to the training function
    p1_env_kwargs = {"num_steps": 1000}
    p2_env_kwargs = {"num_steps": 1000}

    # Self-Play bits
    player1.done_training = False
    player2.done_training = False

    loop = asyncio.get_event_loop()
    # Make Two Threads; one per player and train
    t1 = Thread(target=lambda: training_function(player1, player2, p1_env_kwargs))
    t1.start()

    t2 = Thread(target=lambda: training_function(player2, player1, p2_env_kwargs))
    t2.start()

    # On the network side, keep sending & accepting battles
    while not player1.done_training or not player2.done_training:
        loop.run_until_complete(battle_handler(player1, player2, 1))

    # Wait for thread completion
    t1.join()
    t2.join()

    player1.close(purge=False)
    player2.close(purge=False)
