.. _tracking_observations:

Tracking battle observations
============================

The corresponding complete source code can be found `here <https://github.com/hsahovic/poke-env/blob/master/examples/tracking_observations.py>`__.

The goal of this example is to demonstrate how to record battle state over time by snapshotting the ``Battle`` object inside ``choose_move``.

Defining a snapshot
*******************

Create a dataclass that captures whatever battle state you need. Since ``Battle`` attributes are mutable and updated in-place, copy the values you care about into plain data:

.. code-block:: python

    @dataclass
    class TurnSnapshot:
        turn: int
        active_pokemon: Optional[str]
        opponent_active_pokemon: Optional[str]
        team_hp: Dict[str, float]
        opponent_team_hp: Dict[str, float]
        weather: Dict[Weather, int]
        fields: Dict[Field, int]
        side_conditions: Dict[SideCondition, int]
        opponent_side_conditions: Dict[SideCondition, int]

        @classmethod
        def from_battle(cls, battle: Battle):
            return cls(
                turn=battle.turn,
                active_pokemon=(
                    battle.active_pokemon.species if battle.active_pokemon else None
                ),
                opponent_active_pokemon=(
                    battle.opponent_active_pokemon.species
                    if battle.opponent_active_pokemon
                    else None
                ),
                team_hp={
                    mon.species: mon.current_hp_fraction
                    for mon in battle.team.values()
                },
                opponent_team_hp={
                    mon.species: mon.current_hp_fraction
                    for mon in battle.opponent_team.values()
                },
                weather=dict(battle.weather),
                fields=dict(battle.fields),
                side_conditions=dict(battle.side_conditions),
                opponent_side_conditions=dict(battle.opponent_side_conditions),
            )

This is just one example — add or remove fields to suit your needs.

Recording snapshots in choose_move
***********************************

Override ``choose_move`` to take a snapshot each turn. The guard on ``history[-1].turn`` prevents duplicates when ``choose_move`` is called more than once on the same turn (e.g. after an invalid choice):

.. code-block:: python

    class ObservationTrackingPlayer(Player):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.observations: Dict[str, List[TurnSnapshot]] = {}

        def choose_move(self, battle: AbstractBattle) -> BattleOrder:
            assert isinstance(battle, Battle)
            history = self.observations.setdefault(battle.battle_tag, [])
            snapshot = TurnSnapshot.from_battle(battle)
            if not history or history[-1].turn != snapshot.turn:
                history.append(snapshot)
            return self.choose_random_singles_move(battle)

Cleaning up to prevent memory leaks
************************************

If you play many battles, the ``observations`` dict will grow without bound. Override ``_battle_finished_callback`` to process and discard history when each battle ends:

.. code-block:: python

    def _battle_finished_callback(self, battle: AbstractBattle):
        history = self.observations.pop(battle.battle_tag, [])
        print(f"{battle.battle_tag}: {len(history)} turns recorded")
        for snapshot in history:
            if not snapshot.active_pokemon or not snapshot.opponent_active_pokemon:
                continue
            our_hp = snapshot.team_hp[snapshot.active_pokemon]
            opp_hp = snapshot.opponent_team_hp[snapshot.opponent_active_pokemon]
            print(
                f"  Turn {snapshot.turn}: "
                f"{snapshot.active_pokemon} ({our_hp:.0%}) vs "
                f"{snapshot.opponent_active_pokemon} ({opp_hp:.0%})"
            )

Replace the prints with whatever you need — logging to disk, feeding a model, etc. The key point is to ``pop`` the history so it doesn't accumulate.

Running the example
*******************

.. code-block:: python

    async def main():
        player = ObservationTrackingPlayer(battle_format="gen9randombattle")
        opponent = RandomPlayer(battle_format="gen9randombattle")
        await player.battle_against(opponent, n_battles=3)

    asyncio.run(main())

Running the `complete example <https://github.com/hsahovic/poke-env/blob/master/examples/tracking_observations.py>`__ will play three random battles and print per-turn HP for each.
