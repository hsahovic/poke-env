# -*- coding: utf-8 -*-
import asyncio
import time

from poke_env.player.player import Player
from poke_env.player.random_player import RandomPlayer
from poke_env.player.utils import cross_evaluate
from poke_env.player_configuration import PlayerConfiguration
from poke_env.server_configuration import LocalhostServerConfiguration


class MaxDamagePlayer(Player):
    def choose_move(self, battle):
        # If the player can attack, it will
        if battle.available_moves:
            # Finds the best move among available ones
            best_move = max(battle.available_moves, key=lambda move: move.base_power)
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
