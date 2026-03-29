.. _saving_replays:

Saving Battle Replays
=====================

The complete source code for this example is available
`here <https://github.com/hsahovic/poke-env/blob/master/examples/saving_replays.py>`__.

``poke-env`` supports two replay workflows:

- automatic replay persistence with ``save_replays``;
- explicit replay export from a ``Player`` or ``Battle``.

Prerequisites
*************

- Replay files are produced from completed battles.
- The explicit example below uses two local players, so it requires a running
  Showdown server.

Automatic Replay Saving
***********************

.. code-block:: python

    from poke_env.player import RandomPlayer

    player = RandomPlayer(save_replays=True)
    player_with_custom_folder = RandomPlayer(save_replays="replays")

Replays are written automatically when a battle finishes. If
``save_replays=True``, they are stored in the default ``replays`` folder. If
``save_replays`` is a string, that path is used instead.

Explicit Replay Export
**********************

.. code-block:: python

    import asyncio

    from poke_env.player import RandomPlayer


    async def main():
        p1 = RandomPlayer(max_concurrent_battles=1)
        p2 = RandomPlayer(max_concurrent_battles=1)

        await p1.battle_against(p2, n_battles=1)

        battle_tag = next(iter(p1.battles))

        # Export through Player helper
        p1.save_replay(battle_tag, "replays/player_export.html")

        # Export through Battle object
        p2.battles[battle_tag].save_replay("replays/battle_export.html")


    if __name__ == "__main__":
        asyncio.run(main())

.. warning:: This example requires a running Pokémon Showdown server. See
   :ref:`configuring a showdown server`.
