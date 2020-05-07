# -*- coding: utf-8 -*-
import asyncio
import numpy as np

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

    def teampreview(self, battle):
        mon_performance = {}

        # For each of our pokemons
        for i, mon in enumerate(battle.team.values()):
            # We store their average performance against the opponent team
            mon_performance[i] = np.mean(
                [
                    teampreview_performance(mon, opp)
                    for opp in battle.opponent_team.values()
                ]
            )

        # We sort our mons by performance
        ordered_mons = sorted(mon_performance, key=lambda k: -mon_performance[k])

        # We start with the one we consider best overall
        # We use i + 1 as python indexes start from 0
        #  but showdown's indexes start from 1
        return "/team " + "".join([str(i + 1) for i in ordered_mons])


def teampreview_performance(mon_a, mon_b):
    # We evaluate the performance on mon_a against mon_b as its type advantage
    a_on_b = b_on_a = -np.inf
    for type_ in mon_a.types:
        if type_:
            a_on_b = max(a_on_b, type_.damage_multiplier(*mon_b.types))
    # We do the same for mon_b over mon_a
    for type_ in mon_b.types:
        if type_:
            b_on_a = max(b_on_a, type_.damage_multiplier(*mon_a.types))
    # Our performance metric is the different between the two
    return a_on_b - b_on_a


async def main():
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

    # We define two player configurations.
    player_1_configuration = PlayerConfiguration("Random player", None)
    player_2_configuration = PlayerConfiguration("Max damage player", None)

    # We create the corresponding players.
    random_player = RandomPlayer(
        player_configuration=player_1_configuration,
        battle_format="gen7ou",
        server_configuration=LocalhostServerConfiguration,
        team=team_1,
        max_concurrent_battles=10,
    )
    max_damage_player = MaxDamagePlayer(
        player_configuration=player_2_configuration,
        battle_format="gen7ou",
        server_configuration=LocalhostServerConfiguration,
        team=team_2,
        max_concurrent_battles=10,
    )

    # Now, let's evaluate our player
    cross_evaluation = await cross_evaluate(
        [random_player, max_damage_player], n_challenges=50
    )

    print(
        "Max damage player won %d / 100 battles"
        % (cross_evaluation[max_damage_player.username][random_player.username] * 100)
    )


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
