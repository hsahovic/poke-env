# -*- coding: utf-8 -*-
"""This script can be used to run anything goes gen 7 battles with random teams.
This is especially useful for debugging / testing purposes.

usage:
python diagnostic_tools/anything_goes_gen_7_battles_and_teams.py <n_battle> <log_level>\
    <batch_size>
"""
import asyncio
import orjson
import numpy as np
import sys

from poke_env.data import POKEDEX
from poke_env.player.random_player import RandomPlayer
from poke_env.player_configuration import PlayerConfiguration
from poke_env.server_configuration import LocalhostServerConfiguration
from poke_env.teambuilder.teambuilder import Teambuilder
from poke_env.teambuilder.teambuilder_pokemon import TeambuilderPokemon
from poke_env.utils import to_id_str

from tqdm import tqdm

with open("src/poke_env/data/learnset.json") as f:
    movesets = orjson.load(f)

print("-" * 20, "\n")
mons = [mon for mon in POKEDEX]


def random_evs():
    evs = np.random.randint(0, 252, size=6)
    if sum(evs) > 510:
        evs = evs / sum(evs) * 510
    evs = evs.astype(np.int16)
    return evs


def random_mon():
    mon = np.random.choice(mons)

    if POKEDEX[mon]["num"] <= 0 or POKEDEX[mon]["num"] > 807:
        return random_mon()

    if "baseSpecies" in POKEDEX[mon]:
        mon = POKEDEX[mon]["baseSpecies"]
    else:
        mon = POKEDEX[mon]["species"]

    mon = to_id_str(mon)
    mon = mon.replace("é", "e")

    if mon in movesets and "learnset" in movesets[mon]:
        moveset = movesets[mon]["learnset"]
        learnset = []
        for move in moveset:
            for entry in moveset[move]:
                if entry.startswith("7L") or entry.startswith("7T"):
                    learnset.append(move)
                    break

        if not len(learnset):
            return random_mon()
        elif len(learnset) > 4:
            moves = list(np.random.choice(learnset, size=4, replace=False))
        else:
            moves = learnset
        return TeambuilderPokemon(species=mon, moves=moves, evs=random_evs())
    else:
        print("Problematic mon:", mon)
        if mon in movesets:
            print("is in moveset")
        else:
            print("not in moveset")
        return random_mon()


class RandomTeambuilder(Teambuilder):
    def yield_team(self):
        team = []
        while len(team) < 6:
            mon = random_mon()
            for m in team:
                if m.species == mon.species:
                    break
            else:
                team.append(mon)
        return self.join_team(team)


async def main():
    player_1_configuration = PlayerConfiguration("Player 1", None)
    player_2_configuration = PlayerConfiguration("Player 2", None)

    p1 = RandomPlayer(
        player_configuration=player_1_configuration,
        battle_format="gen7anythinggoes",
        server_configuration=LocalhostServerConfiguration,
        team=RandomTeambuilder(),
        max_concurrent_battles=int(sys.argv[3]),
        log_level=int(sys.argv[2]),
    )
    p2 = RandomPlayer(
        player_configuration=player_2_configuration,
        battle_format="gen7anythinggoes",
        server_configuration=LocalhostServerConfiguration,
        team=RandomTeambuilder(),
        max_concurrent_battles=int(sys.argv[3]),
        log_level=int(sys.argv[2]),
    )

    await asyncio.gather(
        p1.send_challenges(
            opponent=to_id_str(p2.username),
            n_challenges=int(sys.argv[1]) % int(sys.argv[3]),
            to_wait=p2.logged_in,
        ),
        p2.accept_challenges(
            opponent=to_id_str(p1.username),
            n_challenges=int(sys.argv[1]) % int(sys.argv[3]),
        ),
    )

    for _ in tqdm(range(int(sys.argv[1]) // int(sys.argv[3]))):
        await asyncio.gather(
            p1.send_challenges(
                opponent=to_id_str(p2.username),
                n_challenges=int(sys.argv[3]),
                to_wait=p2.logged_in,
            ),
            p2.accept_challenges(
                opponent=to_id_str(p1.username), n_challenges=int(sys.argv[3])
            ),
        )


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
