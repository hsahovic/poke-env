import asyncio

from poke_env import AccountConfiguration, ShowdownServerConfiguration
from poke_env.player import RandomPlayer


async def main():
    # We create a random player
    player = RandomPlayer(
        account_configuration=AccountConfiguration("bot_username", "bot_password"),
        server_configuration=ShowdownServerConfiguration,
    )

    # Sending challenges to 'your_username'
    await player.send_challenges("your_username", n_challenges=1)

    # Accepting one challenge from any user
    # await player.accept_challenges(None, 1)

    # Accepting three challenges from 'your_username'
    # await player.accept_challenges('your_username', 3)

    # Playing 5 games on the ladder
    # await player.ladder(5)

    # Print the rating of the player and its opponent after each battle
    # for battle in player.battles.values():
    #     print(battle.rating, battle.opponent_rating)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
