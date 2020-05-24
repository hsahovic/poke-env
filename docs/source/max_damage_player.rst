.. _max_damage_player:

Creating a simple max damage player
===================================

The corresponding complete source code can be found `here <https://github.com/hsahovic/poke-env/blob/master/examples/max_damage_player.py>`__.

.. note::
    A similar example using gen 7 mechanics is available `here <https://github.com/hsahovic/poke-env/blob/master/examples/gen7/max_damage_player.py>`__.

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

``Player``'s has one abstract method, ``choose_move``. Once implemented, we will be able to instantiate and use our player.

Creating a ``choose_move`` method
*********************************

Method signature
****************

The signature of ``choose_move`` is ``choose_move(self, battle: Battle) -> str``: it takes a ``Battle`` object representing the game state as argument, and returns a move order encoded as a string. This move order must be formatted according to the `showdown protocol <https://github.com/smogon/pokemon-showdown/blob/master/sim/SIM-PROTOCOL.md>`__. Fortunately, ``poke-env`` provides utility functions allowing us to directly format such orders from ``Pokemon`` and ``Move`` objects.

We therefore have to take care of two things: first, reading the information we need from the ``battle`` parameter. Then, we have to return a properly formatted response, corresponding to our move order.

Selecting a move
****************

The ``battle`` parameter is an object of type ``Battle`` which encodes the agent's current knowledge of the game state. It offers several properties that make accessing the game state easy. Some of the most notable are ``active_pokemon``, ``available_moves``, ``available_switches``, ``opponent_active_pokemon``, ``opponent_team`` and ``team``.

In this example, we are going to use ``available_moves``: it returns a list of ``Move`` objects which are available this turn.

We can therefore test if at least one move can be used with ``if battle.available_moves:``. We are interested in the base power of available_moves, which can be accessed with the ``base_power`` property of ``Move`` objects.

.. code-block:: python

    class MaxDamagePlayer(Player):
        def choose_move(self, battle):
            # If the player can attack, it will
            if battle.available_moves:
                # Finds the best move among available ones
                best_move = max(battle.available_moves, key=lambda move: move.base_power)

Returning a choice
******************

Now that we have selected a move, we need to return a corresponding order, which takes the form of a string. Fortunately, ``Player`` provides a method designed to craft such strings directly: ``create_order``. It takes a ``Pokemon`` (for switches) or ``Move`` object as argument, and returns a string corresponding to the order. Additionally, you can use its ``mega``, ``z_move`` and ``dynamax`` parameters to mega evolve, use a z-move, dynamax or gigantamax, if possible this turn.

We also have to return an order corresponding to a random switch if the player cannot attack. ``Player`` objects incorporate a ``choose_random_move`` method, which we will use if no attacking move is available.

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

We can now test our agent by making it battle a random agent. The complete code is:

.. code-block:: python

    # -*- coding: utf-8 -*-
    import asyncio
    import time

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


    async def main():
        start = time.time()

        # We create two players.
        random_player = RandomPlayer(
            battle_format="gen8randombattle",
        )
        max_damage_player = MaxDamagePlayer(
            battle_format="gen8randombattle",
        )

    # Now, let's evaluate our player
    await max_damage_player.battle_against(random_player, n_battles=100)

    print(
        "Max damage player won %d / 100 battles [this took %f seconds]"
        % (
            max_damage_player.n_won_battles, time.time() - start
        )
    )


    if __name__ == "__main__":
        asyncio.get_event_loop().run_until_complete(main())

Running it should take a couple of seconds and print something similar to this:

.. code-block:: python

    Max damage player won 92 / 100 battles [this took 6.320682 seconds]

If you want to use Reinforcement Learning, take a look at the :ref:`rl_with_open_ai_gym_wrapper` example.