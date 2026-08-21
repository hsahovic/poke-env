"""Complete a partial team with Smogon's usage statistics."""

from random import Random

from poke_env.teambuilder import (
    SmogonStatsTeambuilder,
    Teambuilder,
    TeambuilderPokemon,
    complete_team,
    generate_team,
)


def main() -> None:
    generated = generate_team(
        "gen9ou", team_strategy="sample", pokemon_strategy="greedy", rng=Random(7)
    )
    print("Generated structured team:")
    print([pokemon.species for pokemon in generated])
    print("Packed team:")
    print(Teambuilder.join_team(generated))

    partial_team = [TeambuilderPokemon(species=generated[0].species)]
    completed = complete_team(
        partial_team,
        "gen9ou",
        team_strategy="sample",
        pokemon_strategy="greedy",
        rng=Random(7),
    )
    print("Completed partial team:")
    print(Teambuilder.join_team(completed))

    builder = SmogonStatsTeambuilder.from_format(
        "gen9ou", team_strategy="greedy", pokemon_strategy="sample", rng=Random(7)
    )
    print("Reusable builder:")
    print(builder.yield_team())


if __name__ == "__main__":
    main()
