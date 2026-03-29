.. _getting_started:

Getting Started
***************

This section guides you through installing ``poke-env`` and setting up a Pokémon Showdown server.

Installing ``poke-env``
=======================

Ensure Python 3.10 or later is installed. Package dependencies are installed
automatically.

.. code-block:: bash

    pip install poke-env

.. _configuring a showdown server:

Configuring a Pokémon Showdown Server
=====================================

Though ``poke-env`` can interact with a `public server <https://play.pokemonshowdown.com/>`__, hosting a private server is advisable for training agents due to performance and rate limitations on the public server.

1. Install `Node.js v10+ <https://nodejs.org/en/>`__.
2. Clone the Pokémon Showdown repository and set it up:

.. code-block:: bash

    git clone https://github.com/smogon/pokemon-showdown.git
    cd pokemon-showdown
    npm install
    cp config/config-example.js config/config.js
    node pokemon-showdown start --no-security

.. warning:: The ``--no-security`` flag disables crucial security features, use with caution. This flag facilitates AI training by removing rate limiting and authentication requirements.

Your First Local Battle
=======================

Once your local server is running, you can verify your setup by running two
built-in players against each other. ``RandomPlayer`` uses the default
localhost server configuration, so no explicit account or server setup is
required for this example.

.. code-block:: python

    import asyncio

    from poke_env.player import RandomPlayer


    async def main():
        player_1 = RandomPlayer(max_concurrent_battles=1)
        player_2 = RandomPlayer(max_concurrent_battles=1)

        await player_1.battle_against(player_2, n_battles=1)

        print(f"Finished battles: {player_1.n_finished_battles}")
        print(f"Player 1 wins: {player_1.n_won_battles}")


    if __name__ == "__main__":
        asyncio.run(main())

Creating Agents
===============

Agents in ``poke-env`` are instances of the ``Player`` class. Explore the following examples to get started:

- Quickstart: :doc:`examples/quickstart`
- Custom team builder: :doc:`examples/using_a_custom_teambuilder`
- Reinforcement learning with action masking: :ref:`reinforcement_learning`
- Action mapping and strict/fake conversion modes: :ref:`action_mapping_and_strict_modes`
- Strict battle-state validation: :ref:`strict_battle_tracking`
- Replay export: :ref:`saving_replays`

Configuring Showdown Players
============================

``Player`` instances require account configurations tied to Showdown accounts.
Auto-generated configurations are enough for local or unauthenticated servers.
For authenticated servers or custom setups, pass an
``AccountConfiguration`` object explicitly.

.. code-block:: python

    from poke_env import AccountConfiguration
    from poke_env.player import RandomPlayer

    # No authentication required
    my_account_config = AccountConfiguration("my_username", None)
    player = RandomPlayer(account_configuration=my_account_config)

    # Authentication required
    my_account_config = AccountConfiguration("my_username", "super-secret-password")
    player = RandomPlayer(
        account_configuration=my_account_config,
        server_configuration=...,
    )

    # Auto-generated configuration for local use
    player = RandomPlayer()


Connecting Bots to Showdown
===========================

``Player`` instances require an account configuration to connect to a Pokémon
Showdown server. You can configure the connection to local servers, the
official Showdown server, or other custom servers.

Local Servers
-------------

By default, ``Player`` instances use ``LocalhostServerConfiguration``, targeting the default local server endpoint.

Official Showdown Server
------------------------

To connect to the official Pokémon Showdown server using ``ShowdownServerConfiguration``, a player configuration with a password is required.

.. code-block:: python

    from poke_env import AccountConfiguration, ShowdownServerConfiguration
    from poke_env.player import RandomPlayer
    account_config = AccountConfiguration("my_username", "super-secret-password")
    player = RandomPlayer(
        server_configuration=ShowdownServerConfiguration,
        account_configuration=account_config,
    )


Custom Servers
--------------

For custom servers, create a ``ServerConfiguration`` object with the server URL and authentication endpoint.

.. code-block:: python

    from poke_env import ServerConfiguration
    from poke_env.player import RandomPlayer
    custom_config = ServerConfiguration(
        "ws://my.custom.host:5432/showdown/websocket",
        "https://my.custom.host/action.php?",
    )
    player = RandomPlayer(server_configuration=custom_config)

What Next
=========

- Browse task-oriented guides: :doc:`examples/index`
