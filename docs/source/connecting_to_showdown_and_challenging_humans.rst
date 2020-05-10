.. _connecting_to_showdown_and_challenging_humans:

Connecting to showdown and challenging humans
=============================================

The corresponding complete source code can be found `here <https://github.com/hsahovic/poke-env/blob/master/examples/connecting_an_agent_to_showdown.py>`__.

The goal of this example is to demonstrate how to run an agent on showdown, and how to challenge human players.

Connecting your agent to showdown
*********************************

To connect an agent to a showdown server hosted online, you must specify a matching server configuration.

A configuration pointing towards `play.pokemonshowdown.com <https://play.pokemonshowdown.com/>`__ is available in ``poke_env.server_configuration`` and can be used directly. To specify a different server, see :ref:`configuring a showdown server`.

To connect to `play.pokemonshowdown.com <https://play.pokemonshowdown.com/>`__, you also need an account for your agent to use. The following snippets assumes that the account ``bot_username`` exists, and can be accessed with ``bot_password``.

.. code-block:: python

    from poke_env.player.random_player import RandomPlayer
    from poke_env.player_configuration import PlayerConfiguration
    from poke_env.server_configuration import ShowdownServerConfiguration

    # We create a random player
    player = RandomPlayer(
        player_configuration=PlayerConfiguration("bot_username", "bot_password"),
        server_configuration=ShowdownServerConfiguration,
    )

Challenging a human player
**************************

Now that your agent is configured to access showdown, you can use it to challenge any specific user connected on showdown. To do so, you just need their username. The following snippet will make your agent challenge user ``your_username`` for one battle.

.. code-block:: python

    await player.send_challenges("your_username", n_challenges=1)

Alternatively, you can also use ``accept_challenges`` to automatically accept the challenges from a player. To do so, run:

.. code-block:: python

    # Replace opp_username with None to accept challenges from any player
    await player.accept_challenges('opp_username', 1)

Alternatively, you can also use ``accept_challenges`` and ``send_challenges`` locally, either to test your agents yourself or to create custom battle schedules.

The complete source code is:

.. code-block:: python

    # -*- coding: utf-8 -*-
    import asyncio

    from poke_env.player.random_player import RandomPlayer
    from poke_env.player_configuration import PlayerConfiguration
    from poke_env.server_configuration import ShowdownServerConfiguration


    async def main():
        # We create a random player
        player = RandomPlayer(
            player_configuration=PlayerConfiguration("keop998", "aaaaaa"),
            server_configuration=ShowdownServerConfiguration,
        )
        # await player.send_challenges("your_username", n_challenges=1)
        await player.accept_challenges(None, 1)


    if __name__ == "__main__":
        asyncio.get_event_loop().run_until_complete(main())
