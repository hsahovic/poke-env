import asyncio
from dataclasses import dataclass
from typing import Dict, List, Optional

from poke_env.battle import AbstractBattle, Battle, Field, SideCondition, Weather
from poke_env.player import Player, RandomPlayer
from poke_env.player.battle_order import BattleOrder


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
                mon.species: mon.current_hp_fraction for mon in battle.team.values()
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


async def main():
    player = ObservationTrackingPlayer(battle_format="gen9randombattle")
    opponent = RandomPlayer(battle_format="gen9randombattle")
    await player.battle_against(opponent, n_battles=3)


if __name__ == "__main__":
    asyncio.run(main())
