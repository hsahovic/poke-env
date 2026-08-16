Data: Access and manipulate comprehensive Pokémon data
======================================================

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
