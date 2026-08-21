"""Teambuilders backed by Smogon usage statistics."""

from copy import deepcopy
from math import prod
from pathlib import Path
from random import Random
from typing import Literal, Mapping, Optional, Sequence, TypeVar, Union

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
    then uses the geometric mean of the selected Pokemon's teammate distributions.
    Negative or zero teammate scores do not contribute to the partner
    distribution.  The teammate data describes pairs, so completions use pairwise
    signals rather than attempting to reproduce the full distribution of teams.

    :param stats: Statistics snapshot used for every completion.
    :param team: Partially specified Pokemon to retain and complete.
    :param team_strategy: ``"greedy"`` selects the most likely species at each
        step; ``"sample"`` draws species from the corresponding distributions.
    :param pokemon_strategy: ``"greedy"`` selects the most likely ability, item,
        spread, move, and Tera type; ``"sample"`` draws each value from its
        marginal distribution. If a snapshot reports fewer than four moves, all
        reported moves are used.
    :param rng: Source of randomness for sampled choices. Supplying a seeded
        :class:`random.Random` makes generated teams reproducible.
    """

    def __init__(
        self,
        stats: SmogonStats,
        team: Sequence[TeambuilderPokemon] = (),
        *,
        team_strategy: Strategy = "greedy",
        pokemon_strategy: Strategy = "greedy",
        rng: Optional[Random] = None,
    ):
        if team_strategy not in ("greedy", "sample"):
            raise ValueError("team_strategy must be 'greedy' or 'sample'")
        if pokemon_strategy not in ("greedy", "sample"):
            raise ValueError("pokemon_strategy must be 'greedy' or 'sample'")
        if len(team) > 6:
            raise ValueError("team cannot contain more than six Pokemon")
        if any(not pokemon.species for pokemon in team):
            raise ValueError("each partially specified Pokemon must have a species")

        self.stats = stats
        self._team = tuple(deepcopy(pokemon) for pokemon in team)
        self.team_strategy = team_strategy
        self.pokemon_strategy = pokemon_strategy
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

    @classmethod
    def from_format(
        cls,
        battle_format: str,
        team: Sequence[TeambuilderPokemon] = (),
        *,
        month: str = "latest",
        cutoff: int = 0,
        timeout: float = 30,
        cache_dir: Optional[Union[str, Path]] = ".poke_env_stats_cache",
        refresh: bool = False,
        team_strategy: Strategy = "greedy",
        pokemon_strategy: Strategy = "greedy",
        rng: Optional[Random] = None,
    ) -> "SmogonStatsTeambuilder":
        """Create a teambuilder from a Smogon statistics format.

        This is a convenience wrapper around :meth:`SmogonStats.fetch`. Use the
        constructor directly when a parsed snapshot is already available.

        :param battle_format: Format whose Smogon statistics should be used.
        :param team: Partially specified Pokemon to retain and complete.
        :param month: Statistics month, or ``"latest"``.
        :param cutoff: Smogon rating cutoff for the statistics snapshot.
        :param timeout: HTTP timeout used when fetching statistics.
        :param cache_dir: Directory used for cached snapshots. Set to ``None`` to
            disable caching.
        :param refresh: Whether to replace an existing cached snapshot.
        :param team_strategy: Strategy used to select missing species.
        :param pokemon_strategy: Strategy used to complete missing set values.
        :param rng: Source of randomness for sampled choices.
        """
        stats = SmogonStats.fetch(
            battle_format,
            month=month,
            cutoff=cutoff,
            timeout=timeout,
            cache_dir=cache_dir,
            refresh=refresh,
        )
        return cls(
            stats,
            team,
            team_strategy=team_strategy,
            pokemon_strategy=pokemon_strategy,
            rng=rng,
        )

    def yield_team(self) -> str:
        """Return a packed completed team."""
        return self.join_team(self._build_team())

    def _build_team(self) -> list[TeambuilderPokemon]:
        """Return a structured completed team for the public convenience helpers."""
        team = [deepcopy(pokemon) for pokemon in self._team]
        selected_stats = [self._usage_for(pokemon) for pokemon in team]

        while len(team) < 6:
            pokemon_stats = self._select_species(selected_stats)
            team.append(TeambuilderPokemon(species=pokemon_stats.name))
            selected_stats.append(pokemon_stats)

        for pokemon in team:
            self._complete_pokemon(pokemon, self._usage_for(pokemon))
        return team

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
        if not selected_stats:
            weights = {
                pokemon_id: pokemon.usage for pokemon_id, pokemon in candidates.items()
            }
        else:
            teammate_distributions = []
            for selected in selected_stats:
                positive_scores = {
                    pokemon_id: max(selected.teammate_scores.get(pokemon_id, 0.0), 0.0)
                    for pokemon_id in candidates
                }
                total = sum(positive_scores.values())
                if total <= 0:
                    weights = {
                        pokemon_id: pokemon.usage
                        for pokemon_id, pokemon in candidates.items()
                    }
                    break
                teammate_distributions.append(
                    {
                        pokemon_id: score / total
                        for pokemon_id, score in positive_scores.items()
                    }
                )
            else:
                weights = {
                    pokemon_id: prod(
                        distribution[pokemon_id]
                        for distribution in teammate_distributions
                    )
                    ** (1 / len(teammate_distributions))
                    for pokemon_id in candidates
                }

        return candidates[
            self._choose(weights, "available Pokemon", self.team_strategy)
        ]

    def _complete_pokemon(
        self, pokemon: TeambuilderPokemon, usage: PokemonUsageStats
    ) -> None:
        if pokemon.ability is None:
            pokemon.ability = self._choose(
                usage.abilities, "ability", self.pokemon_strategy
            )
        if pokemon.item is None and usage.items:
            pokemon.item = self._choose(usage.items, "item", self.pokemon_strategy)
        if pokemon.nature is None or pokemon.evs is None:
            spread = self._choose(usage.spreads, "spread", self.pokemon_strategy)
            if pokemon.nature is None:
                pokemon.nature = spread.nature
            if pokemon.evs is None:
                pokemon.evs = list(spread.evs)
        if len(pokemon.moves) < 4:
            pokemon.moves.extend(self._choose_moves(usage.moves, pokemon.moves))
        if pokemon.tera_type is None and usage.tera_types:
            pokemon.tera_type = self._choose(
                usage.tera_types, "Tera type", self.pokemon_strategy
            )

    def _choose_moves(
        self, moves: Mapping[str, float], known_moves: Sequence[str]
    ) -> list[str]:
        remaining = {
            move: weight
            for move, weight in moves.items()
            if move not in {to_id_str(move) for move in known_moves}
        }
        needed = min(4 - len(known_moves), len(remaining))
        selected = []
        for _ in range(needed):
            move = self._choose(remaining, "move", self.pokemon_strategy)
            selected.append(move)
            del remaining[move]
        return selected

    def _choose(
        self, weights: Mapping[_Choice, float], description: str, strategy: Strategy
    ) -> _Choice:
        ordered = sorted(weights, key=str)
        if not ordered:
            raise ValueError(f"statistics snapshot has no {description} values")
        if strategy == "greedy":
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


def generate_team(
    battle_format: str,
    *,
    month: str = "latest",
    cutoff: int = 0,
    timeout: float = 30,
    cache_dir: Optional[Union[str, Path]] = ".poke_env_stats_cache",
    refresh: bool = False,
    team_strategy: Strategy = "greedy",
    pokemon_strategy: Strategy = "greedy",
    rng: Optional[Random] = None,
) -> list[TeambuilderPokemon]:
    """Generate a structured team from a Smogon statistics format.

    The returned list can be inspected or modified before being converted to a
    packed team with :meth:`Teambuilder.join_team`. Use
    :meth:`SmogonStatsTeambuilder.from_format` when the builder itself should be
    reused or passed to a :class:`~poke_env.player.Player`.
    """
    builder = SmogonStatsTeambuilder.from_format(
        battle_format,
        month=month,
        cutoff=cutoff,
        timeout=timeout,
        cache_dir=cache_dir,
        refresh=refresh,
        team_strategy=team_strategy,
        pokemon_strategy=pokemon_strategy,
        rng=rng,
    )
    return builder._build_team()


def complete_team(
    partial_team: Sequence[TeambuilderPokemon],
    battle_format: str,
    *,
    month: str = "latest",
    cutoff: int = 0,
    timeout: float = 30,
    cache_dir: Optional[Union[str, Path]] = ".poke_env_stats_cache",
    refresh: bool = False,
    team_strategy: Strategy = "greedy",
    pokemon_strategy: Strategy = "greedy",
    rng: Optional[Random] = None,
) -> list[TeambuilderPokemon]:
    """Complete a partial team using a Smogon statistics format.

    ``partial_team`` should contain :class:`TeambuilderPokemon` objects, for
    example from :meth:`Teambuilder.parse_showdown_team` or
    :meth:`Teambuilder.parse_packed_team`. The returned list is independent of the
    input and can be packed with :meth:`Teambuilder.join_team`.
    """
    builder = SmogonStatsTeambuilder.from_format(
        battle_format,
        partial_team,
        month=month,
        cutoff=cutoff,
        timeout=timeout,
        cache_dir=cache_dir,
        refresh=refresh,
        team_strategy=team_strategy,
        pokemon_strategy=pokemon_strategy,
        rng=rng,
    )
    return builder._build_team()
