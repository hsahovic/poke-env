"""Complete a partial team with Smogon's usage statistics."""

from random import Random

from poke_env.data import SmogonStats
from poke_env.teambuilder import SmogonStatsTeambuilder, TeambuilderPokemon


def main() -> None:
    stats = SmogonStats.fetch("gen9ou", month="latest")
    partial_team = [TeambuilderPokemon(species=stats.top_pokemon(limit=1)[0].name)]

    for team_strategy, pokemon_strategy in (("greedy", "sample"), ("sample", "greedy")):
        builder = SmogonStatsTeambuilder(
            stats,
            partial_team,
            team_strategy=team_strategy,
            pokemon_strategy=pokemon_strategy,
            rng=Random(7),
        )
        print(f"{team_strategy=}, {pokemon_strategy=}")
        print(builder.yield_team())


if __name__ == "__main__":
    main()
