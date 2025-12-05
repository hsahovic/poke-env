.. _getting_started:

Getting Started
***************

This section guides you through installing ``poke-env`` and setting up a Pokémon Showdown server.

Installing ``poke-env``
=======================

Ensure Python 3.10 or later is installed. Dependencies listed `here <https://github.com/hsahovic/poke-env/blob/master/requirements.txt>`__ will be installed automatically.

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

Creating Agents
===============

Agents in ``poke-env`` are instances of the ``Player`` class. Explore the following examples to get started:

- Quickstart: :doc:`examples/quickstart`
- Custom team builder: :doc:`examples/using_a_custom_teambuilder`
- RL agent: :ref:`rl_with_gymnasium_wrapper`

Configuring Showdown Players
============================

``Player`` instances require player configurations tied to Showdown accounts. Auto-generated configurations suffice for servers without authentication. For authenticated servers or custom configurations, utilize the ``account_configuration`` argument with ``AccountConfiguration`` objects.

.. code-block:: python

    from poke_env import AccountConfiguration

    # No authentication required
    my_account_config = AccountConfiguration("my_username", None)
    player = Player(account_configuration=my_account_config)

    # Authentication required
    my_account_config = AccountConfiguration("my_username", "super-secret-password")
    player = Player(account_configuration=my_account_config, server_configuration=...)

    # Auto-generated configuration for local use
    player = Player()


Connecting Bots to Showdown
===========================

``Player`` instances require a account configuration to connect to a Pokémon Showdown server. You can configure the connection to local servers, the official Showdown server, or other custom servers.

Local Servers
-------------

By default, ``Player`` instances use ``LocalhostServerConfiguration``, targeting the default local server endpoint.

Official Showdown Server
------------------------

To connect to the official Pokémon Showdown server using ``ShowdownServerConfiguration``, a player configuration with a password is required.

.. code-block:: python

    from poke_env import Player, ShowdownServerConfiguration, AccountConfiguration
    account_config = AccountConfiguration("my_username", "super-secret-password")
    player = Player(server_configuration=ShowdownServerConfiguration, account_configuration=account_config)


Custom Servers
--------------

For custom servers, create a ``ServerConfiguration`` object with the server URL and authentication endpoint.

.. code-block:: python

    from poke_env import Player, ServerConfiguration
    custom_config = ServerConfiguration("ws://my.custom.host:5432/showdown/websocket", "authentication-endpoint.com/action.php?")
    player = Player(server_configuration=custom_config)
