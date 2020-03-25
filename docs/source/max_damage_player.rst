.. _max_damage_player:

Creating a simple max damage player
===================================

The corresponding complete source code can be found `here <https://github.com/hsahovic/poke-env/blob/master/examples/max_damage_player.py>`__.

The goal of this example is to explain how to create a first custom agent. This agent will follow simple rules:

- If the active pokemon can attack, it will attack and use the move with the highest base power
- Otherwise, it will perform a random switch

Creating a player
*****************

The player that we are going to implement does not need to be trained: we can therefore directly inherit from the ``Player`` class.

Let's create the base class:

.. code-block:: python

    # -*- coding: utf-8 -*-
    from poke_env.player.player import Player

    class MaxDamagePlayer(Player):
        pass

``Player``'s ``choose_move`` method is abstract: it needs to be implemented if we want to instantiate our player.

Creating a ``choose_move`` method
*********************************

Method signature
****************

The signature of ``choose_move`` is ``choose_move(self, battle: Battle) -> str``.

We therefore have to take care of two things: first, we have to use the ``battle`` parameter properly. Second, we have to return a properly formatted string.

Selecting a move
****************

The ``battle`` parameter is an object of type ``Battle`` representing the agent's current knowledge of the game state. In particular, it offers serveral properties that can help easily accessing the information it contains. Some of the most useful properties are ``active_pokemon``, ``available_moves``, ``available_switches``, ``opponent_active_pokemon``, ``opponent_team`` and ``team``.

In this example, we are going to use ``available_moves``. It returns a list of ``Move`` objects which can be used this turn.

We can therefore test if any move can be used with ``if battle.available_moves:``. We are interested in the base power of available_moves, so if we can use moves, we are going to select the move with the highest base power:

.. code-block:: python

    class MaxDamagePlayer(Player):
        def choose_move(self, battle):
            # If the player can attack, it will
            if battle.available_moves:
                # Finds the best move among available ones
                best_move = max(battle.available_moves, key=lambda move: move.base_power)

Returning a choice
******************

Now that we have selected a move, we have to return a string corresponding to this choice. Fortunately, ``Player`` provides a method designed to craft such strings: ``create_order``. It takes a ``Pokemon`` (for switches) or ``Move`` object, and returns a string corresponding to the order. Additionally, you can use its ``mega`` and ``z_move`` parameters to mega evolve or use a z-move, if this is possible.

We also have to return an order corresponding to a random switch if the player can not attack: if that is the case, we can use ``Player``'s ``choose_random_move`` method.

.. code-block:: python

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

Running and testing our agent
*****************************

We can now test our agent by crossing evaluating with a random agent. The final code is:

.. code-block:: python

    # -*- coding: utf-8 -*-
    import asyncio
    import time

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


    async def main():
        start = time.time()

        # We define two player configurations.
        player_1_configuration = PlayerConfiguration("Random player", None)
        player_2_configuration = PlayerConfiguration("Max damage player", None)

        # We create the corresponding players.
        random_player = RandomPlayer(
            player_configuration=player_1_configuration,
            battle_format="gen7randombattle",
            server_configuration=LocalhostServerConfiguration,
        )
        max_damage_player = MaxDamagePlayer(
            player_configuration=player_2_configuration,
            battle_format="gen7randombattle",
            server_configuration=LocalhostServerConfiguration,
        )

        # Now, let's evaluate our player
        cross_evaluation = await cross_evaluate(
            [random_player, max_damage_player], n_challenges=100
        )

        print(
            "Max damage player won %d / 100 battles [this took %f seconds]"
            % (
                cross_evaluation[max_damage_player.username][random_player.username] * 100,
                time.time() - start,
            )
        )


    if __name__ == "__main__":
        asyncio.get_event_loop().run_until_complete(main())

Running it should take a couple of seconds and print something similar to this:

.. code-block:: python

    Max damage player won 92 / 100 battles [this took 6.320682 seconds]

If you want to use Reinforcement Learning, take a look at the :ref:`rl_with_open_ai_gym_wrapper` example.