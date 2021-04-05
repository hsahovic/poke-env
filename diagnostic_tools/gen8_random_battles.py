# -*- coding: utf-8 -*-
"""This script can be used to run gen 8 random battles.

usage:
python diagnostic_tools/gen8_random_battles.py <n_battle> <log_level>\
    <batch_size>
"""
import asyncio
import sys

from poke_env.player.random_player import RandomPlayer

from tqdm import tqdm

print("-" * 20, "\n")


async def main():
    p1 = RandomPlayer(
        max_concurrent_battles=int(sys.argv[3]), log_level=int(sys.argv[2])
    )
    p2 = RandomPlayer(
        max_concurrent_battles=int(sys.argv[3]), log_level=int(sys.argv[2])
    )

    await p1.battle_against(p2, n_battles=int(sys.argv[1]) % int(sys.argv[3]))

    for _ in tqdm(range(int(sys.argv[1]) // int(sys.argv[3]))):
        await p1.battle_against(p2, n_battles=int(sys.argv[3]))


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
