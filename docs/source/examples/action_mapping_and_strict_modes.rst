.. _action_mapping_and_strict_modes:

Action Mapping And Strict/Fake Modes
====================================

``SinglesEnv`` and ``DoublesEnv`` convert between environment actions and
Showdown orders via:

- ``action_to_order``
- ``order_to_action``

Both methods support two important flags:

- ``strict`` (default ``True``): raises ``ValueError`` when a conversion is invalid.
- ``fake`` (default ``False``): allows best-effort conversions, even if not legal.

Why This Matters
****************

During RL training or debugging, invalid actions happen frequently. You can choose
between hard-failing (strict) and fallback behavior (non-strict).

- Use ``strict=True`` while validating your policy and action encoding.
- Use ``strict=False`` when you prefer robustness and fallback to random legal orders.

.. note:: ``action_space`` only includes legal training actions. Sentinel values like
   default/forfeit are accepted by converters, but they are not part of the sampled
   action space.

Singles Example
***************

.. code-block:: python

    import numpy as np

    from poke_env.environment import SinglesEnv

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
