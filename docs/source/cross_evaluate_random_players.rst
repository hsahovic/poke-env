.. _cross_evaluate_random_players:

Cross evaluating random players
===============================

The corresponding complete source code can be found `here <https://github.com/hsahovic/poke-env/blob/master/examples/cross_evaluate_random_players.py>`__.

The goal of this example is to demonstrate how to run existing agents locally, and how to easily measure the relative performance of multiple agents with the ``cross_evaluate`` function.

.. note:: This example necessitates ``tabulate``. You can install it by running ``pip install tabulate``.

Getting *something* to run
**************************

``poke-env`` uses ``asyncio`` for concurrency:your code must therefore manage asyncio to run.

Let's start by defining a ``main`` and some boilerplate code to run it with ``asyncio``.

.. code-block:: python

    # -*- coding: utf-8 -*-
    import asyncio

    async def main():
        pass

    if __name__ == "__main__":
        asyncio.get_event_loop().run_until_complete(main())

Creating player configurations
******************************

Now that we can run our ``main``, let's create three player configurations.

.. code-block:: python

    ...
    from poke_env.player_configuration import PlayerConfiguration

    async def main():
        player_1_configuration = PlayerConfiguration("Player 1", None)
        player_2_configuration = PlayerConfiguration("Player 2", None)
        player_3_configuration = PlayerConfiguration("Player 3", None)

    ...

.. Note:: This example suppose that you use a local showdown server that does not require authentication.

Creating random players
***********************

Now that we have our player configurations, we will create the corresponding players.

.. code-block:: python

    ...
    from poke_env.server_configuration import LocalhostServerConfiguration

    async def main():
        ...
        # We create the corresponding players.
        players = [
            RandomPlayer(
                player_configuration=player_config,
                battle_format="gen7randombattle",
                server_configuration=LocalhostServerConfiguration,
                max_concurrent_battles=10,
            )
            for player_config in [
                player_1_configuration,
                player_2_configuration,
                player_3_configuration,
            ]
        ]

    ...

These players will play battles in the ``gen7randombattle`` battle format, connect to a local server, and play up to 10 battles simultaneously.

Cross evaluating players
************************

Now that our players are defined, we can evaluate them: every player will play 20 games against every other player (for a total of 60 battles).

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

    --------  --------  --------  --------
    -         Player 1  Player 2  Player 3
    Player 1            0.6       0.5
    Player 2  0.4                 0.35
    Player 3  0.5       0.65
    --------  --------  --------  --------

If you want to create a custom player, take a look at the :ref:`max_damage_player` example.

If you want to jump into Reinforcement Learning, take a look at the :ref:`rl_with_open_ai_gym_wrapper` example.