.. _ou_max_player:

Adapting the max player to gen 8 OU and managing team preview
=============================================================

The corresponding complete source code can be found `here <https://github.com/hsahovic/poke-env/blob/master/examples/ou_max_player.py>`__.

.. note::
    A similar example using gen 7 mechanics is available `here <https://github.com/hsahovic/poke-env/blob/master/examples/gen7/ou_max_player.py>`__.

This example adapts :ref:`max_damage_player` to the gen 8 overused format. In particular, it shows how to specify a team and manage team preview.

Team Preview management
***********************

We start with the ``MaxDamagePlayer`` from :ref:`Creating a simple max damage player<max_damage_player>`, and add a team preview method.

.. code-block:: python

    class MaxDamagePlayer(Player):
        # Same method as in previous examples
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
            ...

``teampreview`` takes a ``Battle`` object as argument, and returns a team preview order. These orders are strings of the form ``/team abcdef``, where ``abcdef`` is a sequence of integers from 1 to 6, which designates the pokemons in your team and determines the order in which they are ordered: in particular, the first integer defines your lead.

You can access your team with ``Battle.team`` and your opponent's team with ``Battle.opponent_team``.

The order of the keys in ``Battle.team`` is the same as the order that showdown is considering: if you want to lead with the second pokemon in your team, returning ``/team 213456`` would work.

Here, we are going to evaluate how good of a lead each pokemon we have is, and return the one we deem to be best. To do that, we are going to need an evaluation function.

We define it as follows: we evaluate the performance of a pokemon against another one as the difference between the effectiveness of the first pokemon and the second's pokemon types. Here is an implementation:

.. code-block:: python

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

We can now use it in our ``teampreview`` method:

.. code-block:: python

    def teampreview(self, battle):
        mon_performance = {}

        # For each of our pokemons
        for i, mon in enumerate(battle.team.values()):
            # We store their average performance against the opponent team
            mon_performance[i] = np.mean([
                teampreview_performance(mon, opp)
                for opp in battle.opponent_team.values()
            ])

        # We sort our mons by performance
        ordered_mons = sorted(mon_performance, key = lambda k: -mon_performance[k])

        # We start with the one we consider best overall
        # We use i + 1 as python indexes start from 0
        #  but showdown's indexes start from 1
        return "/team " + ''.join([str(i + 1) for i in ordered_mons])

This method sends our pokemons ordered by their average estimated performance against the opponent team.

Specifying a team
*****************

To specify a team, you have two main options: you can either provide a ``str`` describing your team, or a ``Teambuilder`` object. This example will focus on the first option; if you want to learn more about using teambuilders, please refer to :ref:`using_custom_teambuilder` and :ref:`teambuilder`.

The easiest way to specify a team in ``poke-env`` is to copy-paste a showdown team. You can use showdown's teambuilder and export it directly.

Alternatively, you can use showdown's packed formats, which correspond to the actual string sent by the showdown client to the server.

Here is an example team, both in showdown and packed formats:

Packed format
^^^^^^^^^^^^^

.. code-block::

    |Timid|,,4,252,,252|||||]Landorus-Therian||leftovers|intimidate|earthquake,uturn,stealthrock,hiddenpowerice|Impish|120,,252,,,136||,30,30,,,|||]Toxapex||shedshell|regenerator|scald,toxicspikes,recover,toxic|Bold|252,,60,,196,||,0,,,,|||]Serperior||leftovers|contrary|leafstorm,leechseed,substitute,hiddenpowerfire|Timid|,,4,252,,252||,0,,,,|||]Celesteela||leftovers|beastboost|heavyslam,protect,earthquake,leechseed|Sassy|252,,28,,228,|||||]Medicham-Mega||medichamite|purepower|fakeout,highjumpkick,zenheadbutt,icepunch|Adamant|,252,,,4,252|||||

Showdown format
^^^^^^^^^^^^^^^

.. code-block::

    Tapu Koko @ Electrium Z
    Ability: Electric Surge
    EVs: 4 Def / 252 SpA / 252 Spe
    Timid Nature
    - Thunderbolt
    - U-turn
    - Hidden Power [Ice]
    - Taunt

    Landorus-Therian @ Leftovers
    Ability: Intimidate
    EVs: 120 HP / 252 Def / 136 Spe
    Impish Nature
    - Earthquake
    - U-turn
    - Stealth Rock
    - Hidden Power [Ice]

    Toxapex @ Shed Shell
    Ability: Regenerator
    EVs: 252 HP / 60 Def / 196 SpD
    Bold Nature
    IVs: 0 Atk
    - Scald
    - Toxic Spikes
    - Recover
    - Toxic

    Serperior @ Leftovers
    Ability: Contrary
    EVs: 4 Def / 252 SpA / 252 Spe
    Timid Nature
    IVs: 0 Atk
    - Leaf Storm
    - Leech Seed
    - Substitute
    - Hidden Power [Fire]

    Celesteela @ Leftovers
    Ability: Beast Boost
    EVs: 252 HP / 28 Def / 228 SpD
    Sassy Nature
    - Heavy Slam
    - Protect
    - Earthquake
    - Leech Seed

    Medicham-Mega @ Medichamite
    Ability: Pure Power
    EVs: 252 Atk / 4 SpD / 252 Spe
    Adamant Nature
    - Fake Out
    - High Jump Kick
    - Zen Headbutt
    - Ice Punch

Attributing a team to an agent
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To attribute a team to an agent, you need to pass a ``team`` argument to the agent's constructor. This argument can either be a ``Teambuilder`` object, or the string describing your team. Here is an example:

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

    # We create two players.
    random_player = RandomPlayer(
        battle_format="gen8ou",
        team=team_1,
        max_concurrent_battles=10,
    )
    max_damage_player = MaxDamagePlayer(
        battle_format="gen8ou",
        team=team_2,
        max_concurrent_battles=10,
    )


.. warning:: Parsing team can be sensitive to case or spaces. If you encounter errors, make sure that the string your are passing does not contain any unexpected characters.

.. warning:: Team parsing is a recent feature, and may contain unexpected bugs. If you encounter one, please do not hesitate to `open an issue <https://github.com/hsahovic/poke-env/issues>`__.

Running and testing our agent
*****************************

We can now test our agent. To do so, we can use the ``cross_evaluate`` function from ``poke_env.player.utils`` or the ``battle_against`` method from ``Player``.

.. code-block:: python

    import asyncio
    import numpy as np

    from poke_env.player.player import Player
    from poke_env.player.random_player import RandomPlayer


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

    # We create two players.
    random_player = RandomPlayer(
        battle_format="gen8ou",
        team=team_1,
        max_concurrent_battles=10,
    )
    max_damage_player = MaxDamagePlayer(
        battle_format="gen8ou",
        team=team_2,
        max_concurrent_battles=10,
    )

    # Now, let's evaluate our player
    await max_damage_player.battle_against(random_player, n_battles = 100)

    print(
        "Max damage player won %d / 100 battles"
        % max_damage_player.n_won_battles
    )


    if __name__ == "__main__":
        asyncio.get_event_loop().run_until_complete(main())


Running it should take a couple of seconds and print something similar to this:

.. code-block:: python

    Max damage player won 99 / 100 battles

If you want to use Reinforcement Learning, take a look at :ref:`rl_with_open_ai_gym_wrapper` example.

If you want to create a custom teambuilder, take a look at :ref:`using_custom_teambuilder`.