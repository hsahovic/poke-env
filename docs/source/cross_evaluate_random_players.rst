.. _cross_evaluate_random_players:

Cross evaluating random players
===============================

The corresponding complete source code can be found `here <https://github.com/hsahovic/poke-env/blob/master/examples/cross_evaluate_random_players.py>`__.

.. note::
    A similar example using gen 7 mechanics is available `here <https://github.com/hsahovic/poke-env/blob/master/examples/gen7/cross_evaluate_random_players.py>`__.

The goal of this example is to demonstrate how to run existing agents locally, and how to easily measure the relative performance of multiple agents with the ``cross_evaluate`` utility function.

.. note:: This example uses ``tabulate`` ti format results. You can install it by running ``pip install tabulate``.

Getting *something* to run
**************************

``poke-env`` uses ``asyncio`` for concurrency: most of the functions used to run ``poke-env`` code are async functions. Using asyncio is therefore required.

Let's start by defining a ``main`` and some boilerplate code to run it with ``asyncio``:

.. code-block:: python

    # -*- coding: utf-8 -*-
    import asyncio

    async def main():
        pass

    if __name__ == "__main__":
        asyncio.get_event_loop().run_until_complete(main())


Creating random players
***********************

We can start by creating three players. Players (or agents) are the objects that control the decisions taken in battle: here, we create ``RandomPlayer`` s, which take decisions randomly. By default, ``Player`` instances will automatically use a generated username and try to connect to a showdown server hosted locally.

You can modify this behavior by using the ``player_configuration`` and ``server_configuration`` parameters of the constructor of ``Player`` objects, during initialization.

By default, players play the ``gen8randombattle`` format. You can specify another battle format by passing a ``battle_format`` parameter. If you choose to play a format that requires teams, you'll also need to define it with the ``team`` parameter. You can refer to :ref:`ou_max_player` for an example using a custom team and format.

.. code-block:: python

    ...
    from poke_env.player.random_player import RandomPlayer

    async def main():
        # We create three random players
        players = [
            RandomPlayer(max_concurrent_battles=10) for _ in range(3)
        ]

    ...


.. Note:: This example supposes that you use a local showdown server that does not require authentication.


These players will play battles in the ``gen8randombattle`` battle format, connect to a locally hosted server, and play up to 10 battles simultaneously.

Cross evaluating players
************************

Now that our players are defined, we can evaluate them: every player will play 20 games against every other player, for a total of 60 battles.

To do so, we can use the helper function ``cross_evaluate``:

.. code-block:: python

    ...
    from poke_env.player.utils import cross_evaluate

    async def main():
        ...
        cross_evaluation = await cross_evaluate(players, n_challenges=20)

    ...

Finally, we can display the results in a nice table:

.. code-block:: python

    ...
    from tabulate import tabulate

    async def main():
        ...
        # Defines a header for displaying results
        table = [["-"] + [p.username for p in players]]

        # Adds one line per player with corresponding results
        for p_1, results in cross_evaluation.items():
            table.append([p_1] + [cross_evaluation[p_1][p_2] for p_2 in results])

        # Displays results in a nicely formatted table.
        print(tabulate(table))

    ...

Running the `whole file <https://github.com/hsahovic/poke-env/blob/master/examples/cross_evaluate_random_players.py>`__ should take a couple of seconds and print something similar to this:

.. code-block:: python

    --------------  --------------  --------------  --------------
    -               RandomPlayer 1  RandomPlayer 2  RandomPlayer 3
    RandomPlayer 1                  0.53            0.52
    RandomPlayer 2  0.47                            0.5
    RandomPlayer 3  0.48            0.5
    --------------  --------------  --------------  --------------

If you want to create a custom player, take a look at the :ref:`max_damage_player` example.

If you want to jump into Reinforcement Learning, take a look at the :ref:`rl_with_open_ai_gym_wrapper` example.