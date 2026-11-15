.. _strict_battle_tracking:

Strict Battle Tracking
======================

``Player`` provides ``strict_battle_tracking`` to aggressively validate
internal battle-state consistency against Showdown requests.

Prerequisites
*************

- This option is most useful while running live battles or integration tests.
- It is intended for debugging parser/state issues rather than day-to-day
  training runs.

.. code-block:: python

    from poke_env.player import RandomPlayer

    player = RandomPlayer(
        battle_format="gen9randombattle",
        strict_battle_tracking=True,
    )

When To Use It
**************

Use ``strict_battle_tracking=True`` when you are:

- debugging battle-state desynchronization issues;
- validating custom battle parsing logic or advanced agents;
- developing against multiple formats and wanting early failure on inconsistencies.

Caveats
*******

- Strict mode may raise assertions when Showdown requests and locally tracked
  state disagree.
- Illusion-heavy scenarios can require special handling in your test setup.

For production runs where resilience is preferred over strict validation, keep
``strict_battle_tracking=False``.

Formats with arbitrary abilities
********************************

For Almost Any Ability, Custom Game, and other formats allowing abilities outside
of a species' normal ability pool, disable Pokedex ability inference:

.. code-block:: python

    player = RandomPlayer(
        battle_format="gen9almostanyability",
        infer_abilities=False,
        strict_battle_tracking=True,
    )

Opponent abilities then remain unknown until revealed. Own-team requests always
provide authoritative abilities, regardless of this option. Inference is enabled
by default for standard formats. The same option is available when constructing
``Battle``, ``DoubleBattle``, or ``Pokemon`` directly; ``possible_abilities`` still
lists the species' Pokedex abilities.

For environments, pass the option through ``PlayerOptions`` to configure both
agents (including agents recreated when unpickling):

.. code-block:: python

    from poke_env import PlayerOptions
    from poke_env.environment import SinglesEnv

    env = SinglesEnv(
        player_options=PlayerOptions(
            battle_format="gen9almostanyability",
            infer_abilities=False,
            strict_battle_tracking=True,
        ),
    )

The same ``player_options`` argument is supported by ``PokeEnv`` and
``DoublesEnv``. To construct a player from shared options directly, use
``PlayerOptions.to_player_kwargs``.
