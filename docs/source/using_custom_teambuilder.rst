.. _using_custom_teambuilder:

Creating a custom teambuilder
=============================

The corresponding complete source code can be found `here <https://github.com/hsahovic/poke-env/blob/master/examples/custom_teambuilder.py>`__.

.. note::
    A similar example using gen 7 mechanics is available `here <https://github.com/hsahovic/poke-env/blob/master/examples/gen7/custom_teambuilder.py>`__.

In :ref:`ou_max_player`, we chose a team by passing a `str` containing the team we want to use as a showdown format team.

However, we might want to use different teams in different battles with the same agent, and use more complex mechanisms to generate and select teams. ``Teambuilder`` objects are meant for specifying teams in such a custom fashion. This example demonstrates how to build a simple custom ``Teambuilder``: we will specify a pool of teams, and each game will be played using a team randomly selected from the pool.

Creating a custom ``Teambuilder``
*********************************

Class definition
^^^^^^^^^^^^^^^^

``Teambuilder`` objects need to implement one method, ``yield_team``, which will be called before each battle starts to define the team to use. This method must return a showdown packed-formatted string. In this example, we will use built-in helper functions to simplify this process.

Our custom ``Teambuilder`` will be initialized with a list of showdown formatted teams, and will use one of these team randomly for each battle.

We therefore need to convert showdown formatted teams to the packed-formatted string required by showdown's protocol. We can do that in two steps:

- Convert showdown formatted teams to lists of ``TeambuilderPokemon`` objects. These objects are used internally by ``poke-env`` to describe pokemons used in a team in a flexible way. You can read more about them in :ref:`teambuilder`. This can be accomplished with ``Teambuilder``'s ``parse_showdown_team`` method.
- Convert this list of ``TeambuilderPokemon`` objects into the required formatted string. This can be achieved with ``Teambuilder``'s ``join_team`` method.

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

    Cinderace (M) @ Life Orb
    Ability: Blaze
    EVs: 252 Atk / 4 SpD / 252 Spe
    Jolly Nature
    - Pyro Ball
    - Sucker Punch
    - U-turn
    - High Jump Kick

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

    Cloyster @ King's Rock
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

    Cinccino @ King's Rock
    Ability: Skill Link
    EVs: 252 Atk / 4 Def / 252 Spe
    Jolly Nature
    - Bullet Seed
    - Knock Off
    - Rock Blast
    - Tail Slap
    """

    custom_builder = RandomTeamFromPool([team_1, team_2])

Our ``custom_builder`` can now be used! To use a ``Teambuilder`` with a given ``Player``, just pass it in its constructor, with the ``team`` keyword.

.. code-block:: python

    from poke_env.player.random_player import RandomPlayer

    player_1 = RandomPlayer(
        battle_format="gen8ou",
        team=custom_builder,
        max_concurrent_battles=10,
    )
    player_2 = RandomPlayer(
        battle_format="gen8ou",
        team=custom_builder,
        max_concurrent_battles=10,
    )

Launching battles
^^^^^^^^^^^^^^^^^

Now that we have two players with custom teambuilders, we can make them battle!

.. code-block:: python

    await player_1.battle_against(player_2, n_battles=5)

The complete example looks like that:

.. code-block:: python

    # -*- coding: utf-8 -*-
    import asyncio
    import numpy as np

    from poke_env.player.random_player import RandomPlayer
    from poke_env.teambuilder.teambuilder import Teambuilder


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

    Cinderace (M) @ Life Orb
    Ability: Blaze
    EVs: 252 Atk / 4 SpD / 252 Spe
    Jolly Nature
    - Pyro Ball
    - Sucker Punch
    - U-turn
    - High Jump Kick

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

    Cloyster @ King's Rock
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

    Cinccino @ King's Rock
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
            battle_format="gen8ou",
            team=custom_builder,
            max_concurrent_battles=10,
        )
        player_2 = RandomPlayer(
            battle_format="gen8ou",
            team=custom_builder,
            max_concurrent_battles=10,
        )

        await player_1.battle_against(player_2, n_battles=5)


    if __name__ == "__main__":
        asyncio.get_event_loop().run_until_complete(main())

