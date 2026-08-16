"""Teambuilders backed by Smogon usage statistics."""

from copy import deepcopy
from math import exp
from random import Random
from typing import Literal, Mapping, Optional, Sequence, TypeVar

from poke_env.data.normalize import to_id_str
from poke_env.data.smogon import PokemonUsageStats, SmogonStats
from poke_env.teambuilder.teambuilder import Teambuilder
from poke_env.teambuilder.teambuilder_pokemon import TeambuilderPokemon

Strategy = Literal["greedy", "sample"]
_Choice = TypeVar("_Choice")


class SmogonStatsTeambuilder(Teambuilder):
    """Complete teams using one explicit Smogon usage-statistics snapshot.

    The snapshot supplies marginal set frequencies, so fields of a Pokemon's set
    are selected independently.  Species selection starts from overall usage and
    multiplies it by the exponential of the selected team's teammate scores. This
    is a useful association heuristic, not a calibrated joint team distribution.

    :param stats: Statistics snapshot used for every completion.
    :param team: Partially specified Pokemon to retain and complete.
    :param strategy: ``"greedy"`` selects the most likely values; ``"sample"``
        draws from the corresponding weighted distributions.
    :param rng: Source of randomness for ``"sample"``. Supplying a seeded
        :class:`random.Random` makes generated teams reproducible.
    """

    def __init__(
        self,
        stats: SmogonStats,
        team: Sequence[TeambuilderPokemon] = (),
        *,
        strategy: Strategy = "greedy",
        rng: Optional[Random] = None,
    ):
        if strategy not in ("greedy", "sample"):
            raise ValueError("strategy must be 'greedy' or 'sample'")
        if len(team) > 6:
            raise ValueError("team cannot contain more than six Pokemon")
        if any(not pokemon.species for pokemon in team):
            raise ValueError("each partially specified Pokemon must have a species")

        self.stats = stats
        self._team = tuple(deepcopy(pokemon) for pokemon in team)
        self.strategy = strategy
        self.rng = rng or Random()

        known_species = [
            pokemon.species for pokemon in self._team if pokemon.species is not None
        ]
        if len({to_id_str(species) for species in known_species}) != len(known_species):
            raise ValueError("team cannot contain duplicate species")
        for species in known_species:
            if self.stats.get(species) is None:
                raise ValueError(
                    f"species is not present in the statistics snapshot: {species}"
                )
        for pokemon in self._team:
            if len(pokemon.moves) > 4:
                raise ValueError(
                    f"{pokemon.species} has more than four specified moves"
                )
            if len(set(map(to_id_str, pokemon.moves))) != len(pokemon.moves):
                raise ValueError(f"{pokemon.species} has duplicate specified moves")

    def yield_team(self) -> str:
        """Return a packed completed team."""
        team = [deepcopy(pokemon) for pokemon in self._team]
        selected_stats = [self._usage_for(pokemon) for pokemon in team]

        while len(team) < 6:
            pokemon_stats = self._select_species(selected_stats)
            team.append(TeambuilderPokemon(species=pokemon_stats.name))
            selected_stats.append(pokemon_stats)

        for pokemon in team:
            self._complete_pokemon(pokemon, self._usage_for(pokemon))
        return self.join_team(team)

    def _usage_for(self, pokemon: TeambuilderPokemon) -> PokemonUsageStats:
        assert pokemon.species is not None
        return self.stats[pokemon.species]

    def _select_species(
        self, selected_stats: Sequence[PokemonUsageStats]
    ) -> PokemonUsageStats:
        selected_ids = {pokemon.id for pokemon in selected_stats}
        candidates = {
            pokemon.id: pokemon
            for pokemon in self.stats.pokemon.values()
            if pokemon.id not in selected_ids and pokemon.usage > 0
        }
        weights = {
            pokemon_id: pokemon.usage
            * exp(
                sum(
                    selected.teammate_scores.get(pokemon_id, 0.0)
                    for selected in selected_stats
                )
            )
            for pokemon_id, pokemon in candidates.items()
        }
        return candidates[self._choose(weights, "available Pokemon")]

    def _complete_pokemon(
        self, pokemon: TeambuilderPokemon, usage: PokemonUsageStats
    ) -> None:
        if pokemon.ability is None:
            pokemon.ability = self._choose(usage.abilities, "ability")
        if pokemon.item is None and usage.items:
            pokemon.item = self._choose(usage.items, "item")
        if pokemon.nature is None or pokemon.evs is None:
            spread = self._choose(usage.spreads, "spread")
            if pokemon.nature is None:
                pokemon.nature = spread.nature
            if pokemon.evs is None:
                pokemon.evs = list(spread.evs)
        if len(pokemon.moves) < 4:
            pokemon.moves.extend(self._choose_moves(usage.moves, pokemon.moves))
        if pokemon.tera_type is None and usage.tera_types:
            pokemon.tera_type = self._choose(usage.tera_types, "Tera type")

    def _choose_moves(
        self, moves: Mapping[str, float], known_moves: Sequence[str]
    ) -> list[str]:
        remaining = {
            move: weight
            for move, weight in moves.items()
            if move not in {to_id_str(move) for move in known_moves}
        }
        needed = 4 - len(known_moves)
        if len(remaining) < needed:
            raise ValueError("statistics snapshot has fewer than four moves")
        selected = []
        for _ in range(needed):
            move = self._choose(remaining, "move")
            selected.append(move)
            del remaining[move]
        return selected

    def _choose(self, weights: Mapping[_Choice, float], description: str) -> _Choice:
        ordered = sorted(weights, key=str)
        if not ordered:
            raise ValueError(f"statistics snapshot has no {description} values")
        if self.strategy == "greedy":
            return max(ordered, key=lambda value: weights[value])

        total = sum(weights[value] for value in ordered)
        if total <= 0:
            raise ValueError(
                f"statistics snapshot has no positive {description} weights"
            )
        threshold = self.rng.random() * total
        for value in ordered:
            threshold -= weights[value]
            if threshold <= 0:
                return value
        return ordered[-1]
