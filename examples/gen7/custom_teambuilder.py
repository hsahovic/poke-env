# -*- coding: utf-8 -*-
import asyncio
import numpy as np

from poke_env.player.random_player import RandomPlayer
from poke_env.player.utils import cross_evaluate
from poke_env.player_configuration import PlayerConfiguration
from poke_env.server_configuration import LocalhostServerConfiguration
from poke_env.teambuilder.teambuilder import Teambuilder


class RandomTeamFromPool(Teambuilder):
    def __init__(self, teams):
        self.teams = [self.join_team(self.parse_showdown_team(team)) for team in teams]

    def yield_team(self):
        return np.random.choice(self.teams)


team_1 = """
Zapdos @ Leftovers
Ability: Pressure
EVs: 252 SpA / 4 SpD / 252 Spe
Timid Nature
IVs: 0 Atk
- Discharge
- Heat Wave
- Hidden Power [Ice]
- Roost

Mew @ Leftovers
Ability: Synchronize
EVs: 240 HP / 56 Def / 8 SpA / 140 SpD / 64 Spe
Bold Nature
IVs: 0 Atk
- Stealth Rock
- Will-O-Wisp
- Soft-Boiled
- Psychic

Scizor-Mega (M) @ Scizorite
Ability: Light Metal
EVs: 248 HP / 120 Def / 124 SpD / 16 Spe
Impish Nature
- Bullet Punch
- U-turn
- Roost
- Defog

Garchomp (M) @ Choice Scarf
Ability: Rough Skin
EVs: 252 Atk / 4 SpD / 252 Spe
Jolly Nature
- Outrage
- Earthquake
- Toxic
- Dragon Claw

Amoonguss (F) @ Black Sludge
Ability: Regenerator
EVs: 248 HP / 44 Def / 216 SpD
Calm Nature
IVs: 0 Atk
- Spore
- Giga Drain
- Hidden Power [Fire]
- Toxic

Greninja-Ash @ Choice Specs
Ability: Battle Bond
EVs: 252 SpA / 4 SpD / 252 Spe
Timid Nature
- Water Shuriken
- Hydro Pump
- Dark Pulse
- Spikes
"""

team_2 = """
Gliscor @ Toxic Orb
Ability: Poison Heal
EVs: 244 HP / 44 Def / 68 SpD / 152 Spe
Jolly Nature
- Swords Dance
- Earthquake
- Facade
- Roost

Clefable @ Leftovers
Ability: Magic Guard
EVs: 252 HP / 252 Def / 4 Spe
Bold Nature
IVs: 0 Atk
- Stealth Rock
- Moonblast
- Wish
- Soft-Boiled

Toxapex @ Payapa Berry
Ability: Regenerator
EVs: 252 HP / 92 Def / 164 SpD
Calm Nature
IVs: 0 Atk
- Toxic
- Scald
- Haze
- Recover

Latias @ Latiasite
Ability: Levitate
EVs: 248 HP / 8 Def / 252 Spe
Timid Nature
IVs: 0 Atk
- Surf
- Ice Beam
- Hidden Power [Fire]
- Recover

Ferrothorn @ Leftovers
Ability: Iron Barbs
EVs: 252 HP / 92 Def / 164 SpD
Sassy Nature
IVs: 0 Spe
- Spikes
- Leech Seed
- Power Whip
- Gyro Ball

Tyranitar @ Choice Scarf
Ability: Sand Stream
EVs: 252 Atk / 4 SpD / 252 Spe
Jolly Nature
- Stone Edge
- Crunch
- Pursuit
- Earthquake
"""

custom_builder = RandomTeamFromPool([team_1, team_2])


async def main():

    # We define two player configurations.
    player_1_configuration = PlayerConfiguration("Random player 1", None)
    player_2_configuration = PlayerConfiguration("Random player 2", None)

    # We create the corresponding players.
    player_1 = RandomPlayer(
        player_configuration=player_1_configuration,
        battle_format="gen7ou",
        server_configuration=LocalhostServerConfiguration,
        team=custom_builder,
        max_concurrent_battles=10,
    )
    player_2 = RandomPlayer(
        player_configuration=player_2_configuration,
        battle_format="gen7ou",
        server_configuration=LocalhostServerConfiguration,
        team=custom_builder,
        max_concurrent_battles=10,
    )

    await cross_evaluate([player_1, player_2], n_challenges=5)

    for battle in player_1.battles:
        print(battle)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
