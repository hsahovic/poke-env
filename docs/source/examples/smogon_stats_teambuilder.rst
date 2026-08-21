Smogon stats teambuilder
========================

``SmogonStatsTeambuilder`` completes a partial team from one Smogon usage
statistics snapshot. It uses the snapshot's overall usage and teammate data to
choose species, then fills in each Pokémon's missing ability, item, spread,
moves, and Tera type from that Pokémon's marginal frequencies.

For a reusable builder, load a snapshot directly or use
``SmogonStatsTeambuilder.from_format("gen9ou")``. Its ``yield_team`` method
returns the packed format expected by ``Player``. For one-off use, the
``generate_team`` and ``complete_team`` helpers return lists of
``TeambuilderPokemon`` objects, which can be inspected or modified before being
packed with ``Teambuilder.join_team``.

Team and Pokémon completion are controlled independently:

``team_strategy``
   ``"greedy"`` chooses the highest-weight species at each step. ``"sample"``
   draws each species from the current team-conditioned distribution.

``pokemon_strategy``
   ``"greedy"`` chooses the most frequent missing set values. ``"sample"``
   draws each missing value from its marginal distribution.

This gives all four combinations, for example sampled species with greedy set
completion or greedy species with sampled set completion. A seeded
``random.Random`` makes sampled completions reproducible.

.. literalinclude:: ../../../examples/smogon_stats_teambuilder.py
   :language: python

The teammate statistics describe pairs of Pokémon, not complete teams. The
builder uses them to make a plausible team, but it does not reproduce the
original team distribution exactly.
