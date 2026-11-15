Data: Access and manipulate comprehensive Pokémon data
======================================================

Item data
---------

``GenData.items`` maps Showdown item IDs to metadata for that generation,
including berry, Fling and Natural Gift attributes where applicable. Items
introduced in later generations are excluded; Showdown nonstandard flags are
preserved, so presence does not imply legality in every format. Callback names
are stored as strings, as with move data, and are not executable effects.
The bundled data is refreshed by the automatic data update workflow.

.. code-block:: python

   from poke_env.data import GenData, to_id_str

   items = GenData.from_format("gen9ou").items
   leftovers = items[to_id_str("Leftovers")]
   berry_power = GenData.from_gen(5).items["sitrusberry"]["naturalGift"]["basePower"]

Smogon usage statistics
-----------------------

``SmogonStats`` loads a cutoff-specific monthly snapshot of Smogon's usage
statistics. Remote snapshots are downloaded as compressed JSON and cached in
``.poke_env_stats_cache`` by default.

.. code-block:: python

   from poke_env.data import SmogonStats

   stats = SmogonStats.fetch("gen9ou", cutoff=1695)
   great_tusk = stats["Great Tusk"]
   counters = great_tusk.top_counters(limit=5, min_weighted_encounters=100)

Pass ``cache_dir=None`` to disable caching or ``refresh=True`` to replace a cached
snapshot. When an older snapshot has no compressed resource, fetching falls back to
its uncompressed JSON and stores it in the compressed cache format.
The ``month`` parameter defaults to the latest month listed by Smogon; pass an
explicit ``YYYY-MM`` month when reproducibility is required.

.. automodule:: poke_env.data.gen_data
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: poke_env.data.normalize
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: poke_env.data.smogon
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: poke_env.data.replay_template
   :members:
   :undoc-members:
   :show-inheritance:
