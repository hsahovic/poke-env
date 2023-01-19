"""This module defines a player class exposing the Open AI Gym API with utility functions.
"""
from abc import ABC
from threading import Lock
from typing import Optional, Union, List

from poke_env.environment.abstract_battle import AbstractBattle
from poke_env.environment.battle import Battle
from poke_env.player.battle_order import BattleOrder, ForfeitBattleOrder
from poke_env.player.openai_api import OpenAIGymEnv
from poke_env.player.player import Player
from poke_env.player_configuration import PlayerConfiguration
from poke_env.server_configuration import ServerConfiguration
from poke_env.teambuilder.teambuilder import Teambuilder


class EnvPlayer(OpenAIGymEnv, ABC):
    """Player exposing the Open AI Gym Env API."""

    _ACTION_SPACE = None
    _DEFAULT_BATTLE_FORMAT = "gen8randombattle"

    def __init__(
        self,
        opponent: Optional[Union[Player, str]],
        player_configuration: Optional[PlayerConfiguration] = None,
        *,
        avatar: Optional[int] = None,
        battle_format: Optional[str] = None,
        log_level: Optional[int] = None,
        save_replays: Union[bool, str] = False,
        server_configuration: Optional[ServerConfiguration] = None,
        start_listening: bool = True,
        start_timer_on_battle_start: bool = False,
        ping_interval: Optional[float] = 20.0,
        ping_timeout: Optional[float] = 20.0,
        team: Optional[Union[str, Teambuilder]] = None,
        start_challenging: bool = True,
        use_old_gym_api: bool = True,  # False when new API is implemented in most ML libs
    ):
        """
        :param opponent: Opponent to challenge.
        :type opponent: Player or str, optional
        :param player_configuration: Player configuration. If empty, defaults to an
            automatically generated username with no password. This option must be set
            if the server configuration requires authentication.
        :type player_configuration: PlayerConfiguration, optional
        :param avatar: Player avatar id. Optional.
        :type avatar: int, optional
        :param battle_format: Name of the battle format this player plays. Defaults to
            gen8randombattle.
        :type battle_format: Optional, str. Default to randombattles, with specifics
            varying per class.
        :param log_level: The player's logger level.
        :type log_level: int. Defaults to logging's default level.
        :param save_replays: Whether to save battle replays. Can be a boolean, where
            True will lead to replays being saved in a potentially new /replay folder,
            or a string representing a folder where replays will be saved.
        :type save_replays: bool or str
        :param server_configuration: Server configuration. Defaults to Localhost Server
            Configuration.
        :type server_configuration: ServerConfiguration, optional
        :param start_listening: Whether to start listening to the server. Defaults to
            True.
        :type start_listening: bool
        :param start_timer_on_battle_start: Whether to automatically start the battle
            timer on battle start. Defaults to False.
        :type start_timer_on_battle_start: bool
        :param ping_interval: How long between keepalive pings (Important for backend
            websockets). If None, disables keepalive entirely.
        :type ping_interval: float, optional
        :param ping_timeout: How long to wait for a timeout of a specific ping
            (important for backend websockets.
            Increase only if timeouts occur during runtime).
            If None pings will never time out.
        :type ping_timeout: float, optional
        :param team: The team to use for formats requiring a team. Can be a showdown
            team string, a showdown packed team string, of a ShowdownTeam object.
            Defaults to None.
        :type team: str or Teambuilder, optional
        :param start_challenging: Whether to automatically start the challenge loop
            or leave it inactive.
        :type start_challenging: bool
        :param use_old_gym_api: Whether to use old gym api (where step returns
            (observation, reward, done, info)) or the new one (where step returns
            (observation, reward, terminated, truncated, info))
        :type use_old_gym_api: bool
        """
        self._reward_buffer = {}
        self._opponent_lock = Lock()
        self._opponent: Optional[Union[Player, str]] = opponent
        b_format = self._DEFAULT_BATTLE_FORMAT
        if battle_format:
            b_format = battle_format
        if opponent is None:
            start_challenging = False
        super().__init__(
            player_configuration=player_configuration,
            avatar=avatar,
            battle_format=b_format,
            log_level=log_level,
            save_replays=save_replays,
            server_configuration=server_configuration,
            start_listening=start_listening,
            start_timer_on_battle_start=start_timer_on_battle_start,
            team=team,
            ping_interval=ping_interval,
            ping_timeout=ping_timeout,
            start_challenging=start_challenging,
            use_old_gym_api=use_old_gym_api,
        )

    def reward_computing_helper(
        self,
        battle: AbstractBattle,
        *,
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

        :param battle: The battle for which to compute rewards.
        :type battle: AbstractBattle
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
        if battle not in self._reward_buffer:
            self._reward_buffer[battle] = starting_value
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

        to_return = current_value - self._reward_buffer[battle]
        self._reward_buffer[battle] = current_value

        return to_return

    def action_space_size(self) -> int:
        return len(self._ACTION_SPACE)

    def get_opponent(self) -> Union[Player, str, List[Player], List[str]]:
        with self._opponent_lock:
            if self._opponent is None:
                raise RuntimeError(
                    "Unspecified opponent. "
                    "Specify it in the constructor or use set_opponent"
                )
            return self._opponent

    def set_opponent(self, opponent: Union[Player, str]):
        """
        Sets the next opponent to the specified opponent.

        :param opponent: The next opponent to challenge
        :type opponent: Player or str
        """
        if not isinstance(opponent, Player) and not isinstance(opponent, str):
            raise RuntimeError(f"Expected type Player or str. Got {type(opponent)}")
        with self._opponent_lock:
            self._opponent = opponent

    def reset_env(
        self, opponent: Optional[Union[Player, str]] = None, restart: bool = True
    ):  # pragma: no cover
        """
        Resets the environment to an inactive state: it will forfeit all unfinished
        battles, reset the internal battle tracker and optionally change the next
        opponent and restart the challenge loop.

        :param opponent: The opponent to use for the next battles. If empty it
            will not change opponent.
        :type opponent: Player or str, optional
        :param restart: If True the challenge loop will be restarted before returning,
            otherwise the challenge loop will be left inactive and can be
            started manually.
        :type restart: bool
        """
        self.close(purge=False)
        self.reset_battles()
        if opponent:
            self.set_opponent(opponent)
        if restart:
            self.start_challenging()


class Gen4EnvSinglePlayer(EnvPlayer, ABC):
    _ACTION_SPACE = list(range(4 + 6))
    _DEFAULT_BATTLE_FORMAT = "gen4randombattle"

    def action_to_move(self, action: int, battle: Battle) -> BattleOrder:  # pyre-ignore
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
            return self.agent.create_order(battle.available_moves[action])
        elif 0 <= action - 4 < len(battle.available_switches):
            return self.agent.create_order(battle.available_switches[action - 4])
        else:
            return self.agent.choose_random_move(battle)


class Gen5EnvSinglePlayer(Gen4EnvSinglePlayer, ABC):
    _DEFAULT_BATTLE_FORMAT = "gen5randombattle"


class Gen6EnvSinglePlayer(EnvPlayer, ABC):
    _ACTION_SPACE = list(range(2 * 4 + 6))
    _DEFAULT_BATTLE_FORMAT = "gen6randombattle"

    def action_to_move(self, action: int, battle: Battle) -> BattleOrder:  # pyre-ignore
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
            return self.agent.create_order(battle.available_moves[action])
        elif (
            battle.can_mega_evolve
            and 0 <= action - 4 < len(battle.available_moves)
            and not battle.force_switch
        ):
            return self.agent.create_order(
                battle.available_moves[action - 4], mega=True
            )
        elif 0 <= action - 8 < len(battle.available_switches):
            return self.agent.create_order(battle.available_switches[action - 8])
        else:
            return self.agent.choose_random_move(battle)


class Gen7EnvSinglePlayer(EnvPlayer, ABC):
    _ACTION_SPACE = list(range(3 * 4 + 6))
    _DEFAULT_BATTLE_FORMAT = "gen7randombattle"

    def action_to_move(self, action: int, battle: Battle) -> BattleOrder:  # pyre-ignore
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
            return self.agent.create_order(battle.available_moves[action])
        elif (
            not battle.force_switch
            and battle.can_z_move
            and battle.active_pokemon
            and 0
            <= action - 4
            < len(battle.active_pokemon.available_z_moves)  # pyre-ignore
        ):
            return self.agent.create_order(
                battle.active_pokemon.available_z_moves[action - 4], z_move=True
            )
        elif (
            battle.can_mega_evolve
            and 0 <= action - 8 < len(battle.available_moves)
            and not battle.force_switch
        ):
            return self.agent.create_order(
                battle.available_moves[action - 8], mega=True
            )
        elif 0 <= action - 12 < len(battle.available_switches):
            return self.agent.create_order(battle.available_switches[action - 12])
        else:
            return self.agent.choose_random_move(battle)


class Gen8EnvSinglePlayer(EnvPlayer, ABC):
    _ACTION_SPACE = list(range(4 * 4 + 6))
    _DEFAULT_BATTLE_FORMAT = "gen8randombattle"

    def action_to_move(self, action: int, battle: Battle) -> BattleOrder:  # pyre-ignore
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
            return self.agent.create_order(battle.available_moves[action])
        elif (
            not battle.force_switch
            and battle.can_z_move
            and battle.active_pokemon
            and 0
            <= action - 4
            < len(battle.active_pokemon.available_z_moves)  # pyre-ignore
        ):
            return self.agent.create_order(
                battle.active_pokemon.available_z_moves[action - 4], z_move=True
            )
        elif (
            battle.can_mega_evolve
            and 0 <= action - 8 < len(battle.available_moves)
            and not battle.force_switch
        ):
            return self.agent.create_order(
                battle.available_moves[action - 8], mega=True
            )
        elif (
            battle.can_dynamax
            and 0 <= action - 12 < len(battle.available_moves)
            and not battle.force_switch
        ):
            return self.agent.create_order(
                battle.available_moves[action - 12], dynamax=True
            )
        elif 0 <= action - 16 < len(battle.available_switches):
            return self.agent.create_order(battle.available_switches[action - 16])
        else:
            return self.agent.choose_random_move(battle)
