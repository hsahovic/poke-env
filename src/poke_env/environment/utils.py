from poke_env.environment.battle import Battle


def simple_battle_embedder(battle: Battle):
    # -1 indicates that the move does not have a base power
    # or is not available
    moves_base_power = -np.ones(4)
    moves_dmg_multiplier = np.ones(4)
    for i, move in enumerate(battle.available_moves):
        moves_base_power[i] = (
            move.base_power / 100
        )  # Simple rescaling to facilitate learning
        if move.type:
            moves_dmg_multiplier[i] = move.type.damage_multiplier(
                battle.opponent_active_pokemon.type_1,
                battle.opponent_active_pokemon.type_2,
            )

    # We count how many pokemons have not fainted in each team
    remaining_mon_team = (
        len([mon for mon in battle.team.values() if mon.fainted]) / 6
    )
    remaining_mon_opponent = (
        len([mon for mon in battle.opponent_team.values() if mon.fainted]) / 6
    )

    # Final vector with 10 components
    return np.concatenate(
        [
            moves_base_power,
            moves_dmg_multiplier,
            [remaining_mon_team, remaining_mon_opponent],
        ]
    )
def reward_computing_helper(
    fainted_value: float = 0.0,
    hp_value: float = 0.0,
    number_of_pokemons: int = 6,
    starting_value: float = 0.0,
    status_value: float = 0.0,
    victory_value: float = 1.0,
) -> float:
    """A helper function to compute rewards.

    The reward is computed by computing the value of a game state, and by comparing
    it to the last state.

    State values are computed by weighting different factor. Fainted pokemons,
    their remaining HP, inflicted statuses and winning are taken into account.

    For instance, if the last time this function was called for battle A it had
    a state value of 8 and this call leads to a value of 9, the returned reward will
    be 9 - 8 = 1.

    Consider a single battle where each player has 6 pokemons. No opponent pokemon
    has fainted, but our team has one fainted pokemon. Three opposing pokemons are
    burned. We have one pokemon missing half of its HP, and our fainted pokemon has
    no HP left.

    The value of this state will be:

    - With fainted value: 1, status value: 0.5, hp value: 1:
        = - 1 (fainted) + 3 * 0.5 (status) - 1.5 (our hp) = -1
    - With fainted value: 3, status value: 0, hp value: 1:
        = - 3 + 3 * 0 - 1.5 = -4.5

    :param fainted_value: The reward weight for fainted pokemons. Defaults to 0.
    :type fainted_value: float
    :param hp_value: The reward weight for hp per pokemon. Defaults to 0.
    :type hp_value: float
    :param number_of_pokemons: The number of pokemons per team. Defaults to 6.
    :type number_of_pokemons: int
    :param starting_value: The default reference value evaluation. Defaults to 0.
    :type starting_value: float
    :param status_value: The reward value per non-fainted status. Defaults to 0.
    :type status_value: float
    :param victory_value: The reward value for winning. Defaults to 1.
    :type victory_value: float
    :return: The reward.
    :rtype: float
    """
    previous_reward = starting_value

    def reward_computer(battle: Battle):
        """wrapped func
        :param battle: The battle for which to compute rewards.
        :type battle: AbstractBattle
        """
        current_value = 0

        for mon in battle.team.values():
            current_value += mon.current_hp_fraction * hp_value
            if mon.fainted:
                current_value -= fainted_value
            elif mon.status is not None:
                current_value -= status_value

        current_value += (number_of_pokemons - len(battle.team)) * hp_value

        for mon in battle.opponent_team.values():
            current_value -= mon.current_hp_fraction * hp_value
            if mon.fainted:
                current_value += fainted_value
            elif mon.status is not None:
                current_value += status_value

        current_value -= (number_of_pokemons - len(battle.opponent_team)) * hp_value

        if battle.won:
            current_value += victory_value
        elif battle.lost:
            current_value -= victory_value

        to_return = current_value - previous_reward
        previous_reward = current_value

        if battle.won or battle.lost:
            previous_reward = starting_value
            previous_reward = starting_value

        return to_return

    return reward_computer