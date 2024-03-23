import asyncio

import numpy as np

from poke_env.player import RandomPlayer
from poke_env.teambuilder import Teambuilder


class RandomTeamFromPool(Teambuilder):
    def __init__(self, teams):
        self.teams = [self.join_team(self.parse_showdown_team(team)) for team in teams]

    def yield_team(self):
        return np.random.choice(self.teams)


team_1 = """
Goodra (M) @ Assault Vest
Ability: Sap Sipper
EVs: 248 HP / 252 SpA / 8 Spe
Modest Nature
IVs: 0 Atk
- Dragon Pulse
- Flamethrower
- Sludge Wave
- Thunderbolt

Sylveon (M) @ Leftovers
Ability: Pixilate
EVs: 248 HP / 244 Def / 16 SpD
Calm Nature
IVs: 0 Atk
- Hyper Voice
- Mystical Fire
- Protect
- Wish

Excadrill (M) @ Life Orb
Ability: Sand Rush
EVs: 252 Atk / 4 SpD / 252 Spe
Jolly Nature
- Earthquake
- Iron Head
- Rock Slide
- Rapid Spin

Toxtricity (M) @ Throat Spray
Ability: Punk Rock
EVs: 4 Atk / 252 SpA / 252 Spe
Rash Nature
- Overdrive
- Boomburst
- Shift Gear
- Fire Punch

Seismitoad (M) @ Leftovers
Ability: Water Absorb
EVs: 252 HP / 252 Def / 4 SpD
Relaxed Nature
- Stealth Rock
- Scald
- Earthquake
- Toxic

Corviknight (M) @ Leftovers
Ability: Pressure
EVs: 248 HP / 80 SpD / 180 Spe
Impish Nature
- Defog
- Brave Bird
- Roost
- U-turn
"""

team_2 = """
Togekiss @ Leftovers
Ability: Serene Grace
EVs: 248 HP / 8 SpA / 252 Spe
Timid Nature
IVs: 0 Atk
- Air Slash
- Nasty Plot
- Substitute
- Thunder Wave

Galvantula @ Focus Sash
Ability: Compound Eyes
EVs: 252 SpA / 4 SpD / 252 Spe
Timid Nature
IVs: 0 Atk
- Sticky Web
- Thunder Wave
- Thunder
- Energy Ball

Cloyster @ Focus Sash
Ability: Skill Link
EVs: 252 Atk / 4 SpD / 252 Spe
Adamant Nature
- Icicle Spear
- Rock Blast
- Ice Shard
- Shell Smash

Sandaconda @ Focus Sash
Ability: Sand Spit
EVs: 252 Atk / 4 SpD / 252 Spe
Jolly Nature
- Stealth Rock
- Glare
- Earthquake
- Rock Tomb

Excadrill @ Focus Sash
Ability: Sand Rush
EVs: 252 Atk / 4 SpD / 252 Spe
Adamant Nature
- Iron Head
- Rock Slide
- Earthquake
- Rapid Spin

Cinccino @ Life Orb
Ability: Skill Link
EVs: 252 Atk / 4 Def / 252 Spe
Jolly Nature
- Bullet Seed
- Knock Off
- Rock Blast
- Tail Slap
"""

custom_builder = RandomTeamFromPool([team_1, team_2])


async def main():
    # We create two players
    player_1 = RandomPlayer(
        battle_format="gen8ou", team=custom_builder, max_concurrent_battles=10
    )
    player_2 = RandomPlayer(
        battle_format="gen8ou", team=custom_builder, max_concurrent_battles=10
    )

    await player_1.battle_against(player_2, n_battles=5)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
