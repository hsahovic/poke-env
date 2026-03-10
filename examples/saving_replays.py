import asyncio

from poke_env.player import RandomPlayer


async def main():
    player_1 = RandomPlayer(log_level=25, max_concurrent_battles=1)
    player_2 = RandomPlayer(log_level=25, max_concurrent_battles=1)

    await player_1.battle_against(player_2, n_battles=1)

    battle_tag = next(iter(player_1.battles))

    player_1.save_replay(battle_tag, "replays/player_export.html")
    player_2.battles[battle_tag].save_replay("replays/battle_export.html")


if __name__ == "__main__":
    asyncio.run(main())
