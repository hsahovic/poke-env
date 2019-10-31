# -*- coding: utf-8 -*-
import asyncio
import time

from poke_env.player.random_player import RandomPlayer
from poke_env.player.utils import cross_evaluate
from poke_env.player_configuration import PlayerConfiguration
from poke_env.server_configuration import LocalhostServerConfiguration


class MaxDamagePlayer(RandomPlayer):
    def choose_move(self, battle):
        # If the player can attack, it will
        if battle.available_moves:
            # Initialize move with the first available one
            best_move = battle.available_moves[0]
            max_base_power = best_move.base_power

            for move in battle.available_moves:
                # Keep the maximum damage move
                if move.base_power >= max_base_power:
                    max_base_power, best_move = move.base_power, move
            return self.create_order(best_move)

        # If no attack is available, a random switch will be made
        else:
            return self.choose_random_move(battle)


async def main():
    start = time.time()

    # We define two player configurations.
    player_1_configuration = PlayerConfiguration("Random player", None)
    player_2_configuration = PlayerConfiguration("Max damage player", None)

    # We create the corresponding players.
    random_player = RandomPlayer(
        player_configuration=player_1_configuration,
        battle_format="gen7randombattle",
        server_configuration=LocalhostServerConfiguration,
    )
    max_damage_player = MaxDamagePlayer(
        player_configuration=player_2_configuration,
        battle_format="gen7randombattle",
        server_configuration=LocalhostServerConfiguration,
    )

    # Now, let's evaluate our player
    cross_evaluation = await cross_evaluate(
        [random_player, max_damage_player], n_challenges=100
    )

    print(
        "Max damage player won %d / 100 battles [this took %f seconds]"
        % (
            cross_evaluation[max_damage_player.username][random_player.username] * 100,
            time.time() - start,
        )
    )


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
