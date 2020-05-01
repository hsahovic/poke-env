.. _using_custom_teambuilder:

Creating a custom teambuilder
=============================

The corresponding complete source code can be found `here <https://github.com/hsahovic/poke-env/blob/master/examples/custom_teambuilder.py>`__.

In :ref:`ou_max_player`, we chose a team by passing a `str` containing the team we want to use as a showdown format team.

However, we might want to use different teams with a given agent, or using more complex mechanisms to create teams. ``Teambuilder`` objects are meant for specifying teams in such a custom fashion. This example demonstrates how to build a simple custom ``Teambuilder``: we will specify a pool of teams, and each game will be played using a team randomly selected from the pool.

Creating a custom ``Teambuilder``
*********************************

Class definition
^^^^^^^^^^^^^^^^

``Teambuilder`` objects need to implement one method, ``yield_team``, which will be called before each battle starts to define the team to use. This method must return a showdown packed-formatted string. In this example, we will use built-in helper functions to simplify this process.

Our custom ``Teambuilder`` will be initialized with a list of showdown formatted teams, and will use one of these team randomly for each battle.

We therefore need to convert showdown formatted teams to the packed-formatted string required by showdown's protocol. We can do that in two steps:

- Convert showdown formatted teams to list of ``TeambuilderPokemon`` objects. These objects are used internally by ``poke-env`` to describe pokemons used in a team in a flexible way. You can read more about them in :ref:`teambuilder`. This can be accomplished with ``Teambuilder``'s ``parse_showdown_team`` method.
- Convert this list of ``TeambuilderPokemon`` object into the required formatted string. This can be achieved with ``Teambuilder``'s ``join_team`` method.

All in all, we get the following ``Teambuilder``:

.. code-block:: python

    import numpy as np

    from poke_env.teambuilder.teambuilder import Teambuilder


    class RandomTeamFromPool(Teambuilder):
        def __init__(self, teams):
            self.teams = [self.join_team(self.parse_showdown_team(team)) for team in teams]

        def yield_team(self):
            return np.random.choice(self.teams)

Instanciation
^^^^^^^^^^^^^

We can instantiate it as follows:

.. code-block:: python

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

Our ``custom_builder`` can now be used! To use a ``Teambuilder`` with a given ``Player``, just pass it in its constructor, with the ``team`` keyword.

.. code-block:: python

    from poke_env.player.random_player import RandomPlayer
    from poke_env.player_configuration import PlayerConfiguration
    from poke_env.server_configuration import LocalhostServerConfiguration


    player_1_configuration = PlayerConfiguration("Random player 1", None)
    player_2_configuration = PlayerConfiguration("Random player 2", None)

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

Launching battles
^^^^^^^^^^^^^^^^^

Now that we have two players with custom teambuilders, we can make them battle!

.. code-block:: python

    await cross_evaluate([player_1, player_2], n_challenges=5)

The complete example looks like that:

.. code-block:: python

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

