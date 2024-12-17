"""This module defines a player class exposing the Open AI Gym API with utility functions.
"""

from poke_env.environment.abstract_battle import AbstractBattle
from poke_env.player.battle_order import BattleOrder, ForfeitBattleOrder
from poke_env.player.openai_api import PokeEnv
from poke_env.player.player import Player


class Gen4EnvSinglePlayer(PokeEnv):
    _ACTION_SPACE = list(range(4 + 6))
    _DEFAULT_BATTLE_FORMAT = "gen4randombattle"

    def action_to_move(self, action: int, battle: AbstractBattle) -> BattleOrder:
        """Converts actions to move orders.

        The conversion is done as follows:

        action = -1:
            The battle will be forfeited.
        0 <= action < 4:
            The actionth available move in battle.available_moves is executed.
        4 <= action < 10
            The action - 4th available switch in battle.available_switches is executed.

        If the proposed action is illegal, a random legal move is performed.

        :param action: The action to convert.
        :type action: int
        :param battle: The battle in which to act.
        :type battle: Battle
        :return: the order to send to the server.
        :rtype: str
        """
        if action == -1:
            return ForfeitBattleOrder()
        elif (
            action < 4
            and action < len(battle.available_moves)
            and not battle.force_switch
        ):
            return Player.create_order(battle.available_moves[action])
        elif 0 <= action - 4 < len(battle.available_switches):
            return Player.create_order(battle.available_switches[action - 4])
        else:
            return Player.choose_random_move(battle)


class Gen5EnvSinglePlayer(Gen4EnvSinglePlayer):
    _DEFAULT_BATTLE_FORMAT = "gen5randombattle"


class Gen6EnvSinglePlayer(PokeEnv):
    _ACTION_SPACE = list(range(2 * 4 + 6))
    _DEFAULT_BATTLE_FORMAT = "gen6randombattle"

    def action_to_move(self, action: int, battle: AbstractBattle) -> BattleOrder:
        """Converts actions to move orders.

        The conversion is done as follows:

        action = -1:
            The battle will be forfeited.
        0 <= action < 4:
            The actionth available move in battle.available_moves is executed.
        4 <= action < 8:
            The action - 8th available move in battle.available_moves is executed, with
            mega-evolution.
        8 <= action < 14
            The action - 8th available switch in battle.available_switches is executed.

        If the proposed action is illegal, a random legal move is performed.

        :param action: The action to convert.
        :type action: int
        :param battle: The battle in which to act.
        :type battle: Battle
        :return: the order to send to the server.
        :rtype: str
        """
        if action == -1:
            return ForfeitBattleOrder()
        elif (
            action < 4
            and action < len(battle.available_moves)
            and not battle.force_switch
        ):
            return Player.create_order(battle.available_moves[action])
        elif (
            battle.can_mega_evolve
            and 0 <= action - 4 < len(battle.available_moves)
            and not battle.force_switch
        ):
            return Player.create_order(
                battle.available_moves[action - 4], mega=True
            )
        elif 0 <= action - 8 < len(battle.available_switches):
            return Player.create_order(battle.available_switches[action - 8])
        else:
            return Player.choose_random_move(battle)


class Gen7EnvSinglePlayer(PokeEnv):
    _ACTION_SPACE = list(range(3 * 4 + 6))
    _DEFAULT_BATTLE_FORMAT = "gen7randombattle"

    def action_to_move(self, action: int, battle: AbstractBattle) -> BattleOrder:
        """Converts actions to move orders.

        The conversion is done as follows:

        action = -1:
            The battle will be forfeited.
        0 <= action < 4:
            The actionth available move in battle.available_moves is executed.
        4 <= action < 8:
            The action - 4th available move in battle.available_moves is executed, with
            z-move.
        8 <= action < 12:
            The action - 8th available move in battle.available_moves is executed, with
            mega-evolution.
        12 <= action < 18
            The action - 12th available switch in battle.available_switches is executed.

        If the proposed action is illegal, a random legal move is performed.

        :param action: The action to convert.
        :type action: int
        :param battle: The battle in which to act.
        :type battle: Battle
        :return: the order to send to the server.
        :rtype: str
        """
        if action == -1:
            return ForfeitBattleOrder()
        elif (
            action < 4
            and action < len(battle.available_moves)
            and not battle.force_switch
        ):
            return Player.create_order(battle.available_moves[action])
        elif (
            not battle.force_switch
            and battle.can_z_move
            and battle.active_pokemon
            and 0 <= action - 4 < len(battle.active_pokemon.available_z_moves)
        ):
            return Player.create_order(
                battle.active_pokemon.available_z_moves[action - 4], z_move=True
            )
        elif (
            battle.can_mega_evolve
            and 0 <= action - 8 < len(battle.available_moves)
            and not battle.force_switch
        ):
            return Player.create_order(
                battle.available_moves[action - 8], mega=True
            )
        elif 0 <= action - 12 < len(battle.available_switches):
            return Player.create_order(battle.available_switches[action - 12])
        else:
            return Player.choose_random_move(battle)


class Gen8EnvSinglePlayer(PokeEnv):
    _ACTION_SPACE = list(range(4 * 4 + 6))
    _DEFAULT_BATTLE_FORMAT = "gen8randombattle"

    def action_to_move(self, action: int, battle: AbstractBattle) -> BattleOrder:
        """Converts actions to move orders.

        The conversion is done as follows:

        action = -1:
            The battle will be forfeited.
        0 <= action < 4:
            The actionth available move in battle.available_moves is executed.
        4 <= action < 8:
            The action - 4th available move in battle.available_moves is executed, with
            z-move.
        8 <= action < 12:
            The action - 8th available move in battle.available_moves is executed, with
            mega-evolution.
        8 <= action < 12:
            The action - 8th available move in battle.available_moves is executed, with
            mega-evolution.
        12 <= action < 16:
            The action - 12th available move in battle.available_moves is executed,
            while dynamaxing.
        16 <= action < 22
            The action - 16th available switch in battle.available_switches is executed.

        If the proposed action is illegal, a random legal move is performed.

        :param action: The action to convert.
        :type action: int
        :param battle: The battle in which to act.
        :type battle: Battle
        :return: the order to send to the server.
        :rtype: str
        """
        if action == -1:
            return ForfeitBattleOrder()
        elif (
            action < 4
            and action < len(battle.available_moves)
            and not battle.force_switch
        ):
            return Player.create_order(battle.available_moves[action])
        elif (
            not battle.force_switch
            and battle.can_z_move
            and battle.active_pokemon
            and 0 <= action - 4 < len(battle.active_pokemon.available_z_moves)
        ):
            return Player.create_order(
                battle.active_pokemon.available_z_moves[action - 4], z_move=True
            )
        elif (
            battle.can_mega_evolve
            and 0 <= action - 8 < len(battle.available_moves)
            and not battle.force_switch
        ):
            return Player.create_order(
                battle.available_moves[action - 8], mega=True
            )
        elif (
            battle.can_dynamax
            and 0 <= action - 12 < len(battle.available_moves)
            and not battle.force_switch
        ):
            return Player.create_order(
                battle.available_moves[action - 12], dynamax=True
            )
        elif 0 <= action - 16 < len(battle.available_switches):
            return Player.create_order(battle.available_switches[action - 16])
        else:
            return Player.choose_random_move(battle)


class Gen9EnvSinglePlayer(PokeEnv):
    _ACTION_SPACE = list(range(5 * 4 + 6))
    _DEFAULT_BATTLE_FORMAT = "gen9randombattle"

    def action_to_move(self, action: int, battle: AbstractBattle) -> BattleOrder:
        """Converts actions to move orders.

        The conversion is done as follows:

        action = -1:
            The battle will be forfeited.
        0 <= action < 4:
            The actionth available move in battle.available_moves is executed.
        4 <= action < 8:
            The action - 4th available move in battle.available_moves is executed, with
            z-move.
        8 <= action < 12:
            The action - 8th available move in battle.available_moves is executed, with
            mega-evolution.
        8 <= action < 12:
            The action - 8th available move in battle.available_moves is executed, with
            mega-evolution.
        12 <= action < 16:
            The action - 12th available move in battle.available_moves is executed,
            while dynamaxing.
        16 <= action < 20:
            The action - 16th available move in battle.available_moves is executed,
            while terastallizing.
        20 <= action < 26
            The action - 20th available switch in battle.available_switches is executed.

        If the proposed action is illegal, a random legal move is performed.

        :param action: The action to convert.
        :type action: int
        :param battle: The battle in which to act.
        :type battle: Battle
        :return: the order to send to the server.
        :rtype: str
        """
        if action == -1:
            return ForfeitBattleOrder()
        elif (
            action < 4
            and action < len(battle.available_moves)
            and not battle.force_switch
        ):
            return Player.create_order(battle.available_moves[action])
        elif (
            not battle.force_switch
            and battle.can_z_move
            and battle.active_pokemon
            and 0 <= action - 4 < len(battle.active_pokemon.available_z_moves)
        ):
            return Player.create_order(
                battle.active_pokemon.available_z_moves[action - 4], z_move=True
            )
        elif (
            battle.can_mega_evolve
            and 0 <= action - 8 < len(battle.available_moves)
            and not battle.force_switch
        ):
            return Player.create_order(
                battle.available_moves[action - 8], mega=True
            )
        elif (
            battle.can_dynamax
            and 0 <= action - 12 < len(battle.available_moves)
            and not battle.force_switch
        ):
            return Player.create_order(
                battle.available_moves[action - 12], dynamax=True
            )
        elif (
            battle.can_tera
            and 0 <= action - 16 < len(battle.available_moves)
            and not battle.force_switch
        ):
            return Player.create_order(
                battle.available_moves[action - 16], terastallize=True
            )
        elif 0 <= action - 20 < len(battle.available_switches):
            return Player.create_order(battle.available_switches[action - 20])
        else:
            return Player.choose_random_move(battle)
