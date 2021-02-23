.. _getting_started:


Getting started
***************

This sections will guide you in installing ``poke-env`` and configuring a suited showdown server.

Installing ``poke-env``
=======================

``poke-env`` requires python >= 3.6 to be installed. It has a number of dependencies that are listed `here <https://github.com/hsahovic/poke-env/blob/master/requirements.txt>`__ and that will be installed automatically.

Installation can be performed via pip:

.. code-block:: bash

    pip install poke-env

.. _configuring a showdown server:

Configuring a showdown server
=============================

``poke-env`` communicates with a pokemon showdown server. A public implementation of showdown is hosted `here <https://play.pokemonshowdown.com/>`__, and can be used to test your agents against real human players.

However, this implementation:

- Requires an internet connection at all time
- Has numerous performance limitation (move rate, number of concurrent battles...)
- Is not meant to be used to train agents

Therefore, it is recommended to host you own server. Fortunately, Pokemon Showdown is `open-source <https://play.pokemonshowdown.com/>`__ and just requires `Node.js v10+ <https://nodejs.org/en/>`__. ``poke-env`` used to maintain a `custom and optimized fork <https://github.com/hsahovic/Pokemon-Showdown>`__, but its features have been merged in the official showdown implementation.

To get started, you will first need to `install node v10+ <https://nodejs.org/en/download/>`__. Then, you can clone the pokemon showdown repo:

.. code-block:: bash

    git clone https://github.com/smogon/pokemon-showdown.git

Everything is now almost ready to create your first agent: you just have to start the showdown server:

.. code-block:: bash

    cd pokemon-showdown
    node pokemon-showdown start --no-security

.. warning:: The ``--no-security`` flag deactivates several important security features, so do not run a public server with this flag if you are not sure of what you are doing. This flag also removes most of showdown's rate limiting, authentication and throttling, which allows its usage to train AI agents effectively.


You should then get something like this:

.. code-block:: bash

    NEW GLOBAL: global
    NEW CHATROOM: lobby
    NEW CHATROOM: staff
    Worker 1 now listening on 0.0.0.0:8000
    Test your server at http://localhost:8000

If that is the case, congratulations! You just launched your server! You can now refer to :ref:`examples` to create your first agent.


Creating agents
===============

In ``poke-env``, agents are represented by instances of python classes inheriting from ``Player``. This class incorporates everything that is needed to communicate with showdown servers, as well as many utilities designed to make creating agents easier.

To get started on creating an agent, we recommended taking a look at explained examples.

- Running agent: :ref:`cross_evaluate_random_players`
- Creating a first non-trivial agent: :ref:`max_damage_player`
- Using Reinforcement Learning to train an agent: :ref:`rl_with_open_ai_gym_wrapper`
- Using teams and managing team preview in non-random formats: :ref:`ou_max_player`
- Building a custom teambuilder: :ref:`using_custom_teambuilder`


Configuring showdown players
============================

``Player`` instances need a player configuration corresponding to showdown accounts. By default, such configurations are automatically generated for each ``Player``. These automatically generated configurations are compatible with servers bypassing authentication, such as the recommended fork mentionned above.

You can create custom configurations, for instance to use existing showdown accounts. To do so, use the ``player_configuration`` argument of ``Player`` constructors: you can pass in a ``PlayerConfiguration``, which are named tuples with two arguments: an username and a password.

Users without authentication
----------------------------

If your showdown configuration does not require authentication, you can use any username and set the password to ``None``.

.. code-block:: python

    from poke_env.player_configuration import PlayerConfiguration

    # This will work on servers that do not require authentication, which is the
    # case of the server launched in our 'Getting Started' section
    my_player_config = PlayerConfiguration("my_username", None)

Users with authentication
--------------------------

If your showdown configuration uses authentication, the values of each ``player_configuration`` that you create must be defined in the server's authentication database. On `pokemonshowdown.com <https://play.pokemonshowdown.com/>`__, you can achieve this by registering an username.

.. code-block:: python

    from poke_env.player_configuration import PlayerConfiguration

    # This object can be used with a player connecting to a server using authentication
    # The user 'my_username' must exist and have 'super-secret-password' as his password
    my_player_config = PlayerConfiguration("my_username", "super-secret-password")

Connecting your bots to showdown
================================

``Player`` instances need a server configuration pointing to a websocket endpoint and an authentication endpoint. By default, ``Player`` instances will use ``LocalhostServerConfiguration``, which corresponds to the default configuration of local showdown servers.

You can set custom configurations by using the ``server_configuration`` argument of ``Player`` instances. It expects a ``ServerConfiguration`` object, which is a named tuple containing a server url and authentication url.

``poke-env`` includes two ready-to-use ``ServerConfiguration`` objects: ``LocalhostServerConfiguration`` and ``ShowdownServerConfiguration``.

The first one points to ``locahost:8000`` - the default endpoint for a local showdown server - whereas the second one points to ``https://play.pokemonshowdown.com/``. Both use the same authentication endpoint, https://play.pokemonshowdown.com/action.php?.

If you use our custom fork of showdown, as mentionned in Getting Started, players do not need to authenticate to battle. This effectively skips authentication calls: your agents can access your server without an internet connection.

Custom server configuration
===========================

You can create your own server configuration if you want to connect your player to another server. You can do so like that:

.. code-block:: python

    from poke_env.server_configuration import ServerConfiguration

    # If your server is accessible at my.custom.host:5432, and your authentication
    # endpoint is authentication-endpoint.com/action.php?
    my_server_config= ServerConfiguration(
        "my.custom.host:5432",
        "authentication-endpoint.com/action.php?"
    )

    # You can now use my_server_config with a Player object
