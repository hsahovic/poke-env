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
