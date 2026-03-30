.. _examples:

Examples
========

This page collects the main end-to-end examples for the most common
``poke-env`` workflows.

Choose an Example
*****************

- :doc:`quickstart`: your first local battle and first custom agent; requires a
  local Showdown server.
- :doc:`using_a_custom_teambuilder`: custom team selection and generation;
  requires a local Showdown server.
- :doc:`connecting_to_showdown_and_challenging_humans`: connecting to the
  official or a custom server and interacting with human players; an account is
  required for the public server.
- :doc:`reinforcement_learning`: training with action masking and
  Stable-Baselines3; requires a local server plus RL dependencies.
- :doc:`action_mapping_and_strict_modes`: understanding environment actions,
  legality checks, and masks for custom RL pipelines.
- :doc:`strict_battle_tracking`: debugging request parsing and battle-state
  desynchronization issues.
- :doc:`saving_replays`: automatic replay persistence and explicit HTML replay
  export.

.. toctree::
    :maxdepth: 4

    quickstart
    using_a_custom_teambuilder
    connecting_to_showdown_and_challenging_humans
    tracking_observations
    reinforcement_learning
    action_mapping_and_strict_modes
    strict_battle_tracking
    saving_replays
