.. _connecting_to_showdown_and_challenging_humans:

Connecting to Showdown and Challenging Humans
=============================================

The complete example source code is available
`here <https://github.com/hsahovic/poke-env/blob/master/examples/connecting_an_agent_to_showdown.py>`__.

This example demonstrates how to connect an agent to Pokémon Showdown and
challenge human players.

Prerequisites
*************

- For the official server, you need a Showdown account and password.
- For a custom server, you need a matching ``ServerConfiguration``.
- For local bot-vs-bot testing, start with :doc:`../getting_started` instead.

Connecting Your Agent to Showdown
*********************************

To connect an agent to a Showdown server hosted online, you must specify a
matching server configuration.

A configuration pointing to
`play.pokemonshowdown.com <https://play.pokemonshowdown.com/>`__ is available
in ``poke_env.ps_client.server_configuration`` and can be used directly. To
specify a different server, see :ref:`configuring a showdown server`.

To connect to `play.pokemonshowdown.com <https://play.pokemonshowdown.com/>`__,
you also need an account for your agent to use. The following snippet assumes
that the account ``bot_username`` exists and can be accessed with
``bot_password``.

.. code-block:: python

    from poke_env.player import RandomPlayer
    from poke_env import AccountConfiguration, ShowdownServerConfiguration

    # We create a random player
    player = RandomPlayer(
        account_configuration=AccountConfiguration("bot_username", "bot_password"),
        server_configuration=ShowdownServerConfiguration,
    )

Challenging a Human Player
**************************

Now that your agent is configured to access Showdown, you can use it to
challenge any specific connected user. The following snippet will make your
agent challenge ``your_username`` for one battle.

.. code-block:: python

    await player.send_challenges("your_username", n_challenges=1)

Accepting Challenges from Human Players
***************************************

You can use ``accept_challenges`` to automatically accept challenges from a
specific player or from any player.

.. code-block:: python

    await player.accept_challenges("opp_username", 1)
    await player.accept_challenges(None, 1)

Playing on the Ladder
*********************

Finally, you can use the ``ladder`` method to play games on the ladder.

.. code-block:: python

    # Play five games on the ladder
    await player.ladder(5)

After playing games on the ladder, you may receive rating information. You can
access it with the ``Battle.rating`` and ``Battle.opponent_rating`` properties:

.. code-block:: python

    # Print the rating of the player and its opponent after each battle
    for battle in player.battles.values():
        print(battle.rating, battle.opponent_rating)

The complete example is:

.. code-block:: python

    import asyncio

    from poke_env.player import RandomPlayer
    from poke_env import AccountConfiguration, ShowdownServerConfiguration


    async def main():
        # We create a random player
        player = RandomPlayer(
            account_configuration=AccountConfiguration("bot_username", "bot_password"),
            server_configuration=ShowdownServerConfiguration,
        )

        # Sending challenges to 'your_username'
        await player.send_challenges("your_username", n_challenges=1)

        # Accepting one challenge from any user
        await player.accept_challenges(None, 1)

        # Accepting three challenges from 'your_username'
        await player.accept_challenges("your_username", 3)

        # Playing 5 games on the ladder
        await player.ladder(5)

        # Print the rating of the player and its opponent after each battle
        for battle in player.battles.values():
            print(battle.rating, battle.opponent_rating)


    if __name__ == "__main__":
        asyncio.run(main())
