.. _action_mapping_and_strict_modes:

Action Mapping and Strict/Fake Modes
====================================

``SinglesEnv`` and ``DoublesEnv`` expose helpers to convert between encoded
actions and Showdown orders:

- ``action_to_order``
- ``order_to_action``
- ``get_action_mask``

Both methods support two important flags:

- ``strict`` (default ``True``): raises ``ValueError`` when a conversion is invalid.
- ``fake`` (default ``False``): allows best-effort conversions, even if not legal.

Prerequisites
*************

- You need a live ``Battle`` or ``DoubleBattle`` object, usually from a player
  callback or an environment step.
- This guide is most useful when building custom RL policies, wrappers, or
  action encoders.

Why This Matters
****************

During RL training or debugging, invalid actions happen frequently. You can
choose between hard-failing (strict) and fallback behavior (non-strict).

- Use ``strict=True`` while validating your policy and action encoding.
- Use ``strict=False`` when you prefer robustness and fallback to random legal orders.

.. note:: The Gymnasium ``action_space`` spans the full encoded action range.
   Use ``get_action_mask`` to determine which actions are currently legal.
   Sentinel values like default/forfeit are accepted by the converters, but
   they are not emitted by the standard sampled action spaces.

Singles Example
***************

.. code-block:: python

    import numpy as np

    from poke_env.environment import SinglesEnv

    mask = SinglesEnv.get_action_mask(battle)

    # Convert action -> order
    order = SinglesEnv.action_to_order(
        np.int64(6),
        battle,
        fake=False,
        strict=True,
    )

    # Convert order -> action
    action = SinglesEnv.order_to_action(
        order,
        battle,
        fake=False,
        strict=True,
    )

Doubles Example
***************

.. code-block:: python

    import numpy as np

    from poke_env.environment import DoublesEnv

    mask = DoublesEnv.get_action_mask(battle)

    action = np.array([7, 27], dtype=np.int64)
    order = DoublesEnv.action_to_order(action, battle, fake=False, strict=False)

    recovered_action = DoublesEnv.order_to_action(
        order,
        battle,
        fake=False,
        strict=False,
    )

Recommended Workflow
********************

1. Start with ``strict=True`` and unit-test your action encoding.
2. If you need fault tolerance during long runs, switch to ``strict=False``.
3. Keep ``fake=False`` unless you explicitly need best-effort conversion behavior.
