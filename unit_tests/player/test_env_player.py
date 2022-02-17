# -*- coding: utf-8 -*-
import asyncio
import unittest
import pytest

from gym.spaces import Space, Discrete
from inspect import isawaitable

from poke_env.environment.abstract_battle import AbstractBattle
from poke_env.environment.battle import Battle
from poke_env.environment.move import Move
from poke_env.environment.pokemon import Pokemon
from poke_env.environment.status import Status
from poke_env.player.battle_order import BattleOrder
from poke_env.player.baselines import RandomPlayer
from poke_env.player.env_player import EnvPlayer
from poke_env.player.env_player import (
    Gen4EnvSinglePlayer,
    Gen5EnvSinglePlayer,
    Gen6EnvSinglePlayer,
    Gen7EnvSinglePlayer,
    Gen8EnvSinglePlayer,
)
from poke_env.player.openai_api import _AsyncPlayer
from poke_env.player_configuration import PlayerConfiguration
from poke_env.server_configuration import ServerConfiguration
from unittest.mock import patch


player_configuration = PlayerConfiguration("username", "password")
server_configuration = ServerConfiguration("server.url", "auth.url")


class CustomEnvPlayer(EnvPlayer):
    def calc_reward(self, last_battle, current_battle) -> float:
        pass

    def action_to_move(self, action: int, battle: AbstractBattle) -> BattleOrder:
        return Gen7EnvSinglePlayer.action_to_move(self, action, battle)

    def describe_embedding(self) -> Space:
        pass

    _ACTION_SPACE = Gen7EnvSinglePlayer._ACTION_SPACE

    def embed_battle(self, battle):
        return None


def test_init():
    gym_env = CustomEnvPlayer(
        player_configuration=player_configuration,
        server_configuration=server_configuration,
        start_listening=False,
        battle_format="gen7randombattles",
    )
    player = gym_env.agent
    assert isinstance(gym_env, CustomEnvPlayer)
    assert isinstance(player, _AsyncPlayer)


class AsyncMock(unittest.mock.MagicMock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)


@patch(
    "poke_env.player.openai_api._AsyncQueue.async_get",
    return_value=2,
    new_callable=AsyncMock,
)
@patch("poke_env.player.openai_api._AsyncQueue.async_put", new_callable=AsyncMock)
def test_choose_move(queue_put_mock, queue_get_mock):
    print("ciao")
    player = CustomEnvPlayer(
        player_configuration=player_configuration,
        server_configuration=server_configuration,
        start_listening=False,
        battle_format="gen7randombattles",
        start_challenging=False,
    )
    battle = Battle("bat1", player.username, player.logger)
    battle._available_moves = {Move("flamethrower")}
    message = player.agent.choose_move(battle)

    assert isawaitable(message)

    message = asyncio.get_event_loop().run_until_complete(message)

    assert message.message == "/choose move flamethrower"

    battle._available_moves = {Pokemon(species="charizard")}

    message = player.agent.choose_move(battle)

    assert isawaitable(message)

    message = asyncio.get_event_loop().run_until_complete(message)

    assert message.message == "/choose switch charizard"


def test_reward_computing_helper():
    player = CustomEnvPlayer(
        player_configuration=player_configuration,
        server_configuration=server_configuration,
        start_listening=False,
        battle_format="gen7randombattles",
    )
    battle_1 = Battle("bat1", player.username, player.logger)
    battle_2 = Battle("bat2", player.username, player.logger)
    battle_3 = Battle("bat3", player.username, player.logger)
    battle_4 = Battle("bat4", player.username, player.logger)

    assert (
        player.reward_computing_helper(
            battle_1,
            fainted_value=0,
            hp_value=0,
            number_of_pokemons=4,
            starting_value=0,
            status_value=0,
            victory_value=1,
        )
        == 0
    )

    battle_1._won = True
    assert (
        player.reward_computing_helper(
            battle_1,
            fainted_value=0,
            hp_value=0,
            number_of_pokemons=4,
            starting_value=0,
            status_value=0,
            victory_value=1,
        )
        == 1
    )

    assert (
        player.reward_computing_helper(
            battle_2,
            fainted_value=0,
            hp_value=0,
            number_of_pokemons=4,
            starting_value=0.5,
            status_value=0,
            victory_value=5,
        )
        == -0.5
    )

    battle_2._won = False
    assert (
        player.reward_computing_helper(
            battle_2,
            fainted_value=0,
            hp_value=0,
            number_of_pokemons=4,
            starting_value=0,
            status_value=0,
            victory_value=5,
        )
        == -5
    )

    battle_3._team = {i: Pokemon(species="slaking") for i in range(4)}
    battle_3._opponent_team = {i: Pokemon(species="slowbro") for i in range(3)}

    battle_3._team[0].status = Status["FRZ"]
    battle_3._team[1]._current_hp = 100
    battle_3._team[1]._max_hp = 200
    battle_3._opponent_team[0].status = Status["FNT"]
    battle_3._opponent_team[1].status = Status["FNT"]

    # Opponent: two fainted, one full hp opponent
    # You: one half hp mon, one frozen mon
    assert (
        player.reward_computing_helper(
            battle_3,
            fainted_value=2,
            hp_value=3,
            number_of_pokemons=4,
            starting_value=0,
            status_value=0.25,
            victory_value=100,
        )
        == 2.25
    )

    battle_3._won = True
    assert (
        player.reward_computing_helper(
            battle_3,
            fainted_value=2,
            hp_value=3,
            number_of_pokemons=4,
            starting_value=0,
            status_value=0.25,
            victory_value=100,
        )
        == 100
    )

    battle_4._team, battle_4._opponent_team = (
        battle_3._opponent_team,
        battle_3._team,
    )
    assert (
        player.reward_computing_helper(
            battle_4,
            fainted_value=2,
            hp_value=3,
            number_of_pokemons=4,
            starting_value=0,
            status_value=0.25,
            victory_value=100,
        )
        == -2.25
    )


def test_action_space():
    player = CustomEnvPlayer(start_listening=False)
    assert player.action_space == Discrete(len(Gen7EnvSinglePlayer._ACTION_SPACE))

    for PlayerClass, (has_megas, has_z_moves, has_dynamax) in zip(
        [
            Gen4EnvSinglePlayer,
            Gen5EnvSinglePlayer,
            Gen6EnvSinglePlayer,
            Gen7EnvSinglePlayer,
            Gen8EnvSinglePlayer,
        ],
        [
            (False, False, False),
            (False, False, False),
            (True, False, False),
            (True, True, False),
            (True, True, True),
        ],
    ):

        class CustomEnvClass(PlayerClass):
            def embed_battle(self, *args, **kwargs):
                return []

            def calc_reward(self, last_battle, current_battle):
                return 0.0

            def describe_embedding(self):
                return None

            def get_opponent(self):
                return None

        p = CustomEnvClass(start_listening=False, start_challenging=False)

        assert p.action_space == Discrete(
            4 * sum([1, has_megas, has_z_moves, has_dynamax]) + 6
        )


def test_get_opponent():
    player = CustomEnvPlayer(start_listening=False, opponent="test")
    assert player.get_opponent() == "test"
    player.opponent = None
    with pytest.raises(RuntimeError):
        player.get_opponent()


def test_set_opponent():
    player = CustomEnvPlayer(start_listening=False)
    assert isinstance(player.opponent, RandomPlayer)
    with pytest.raises(RuntimeError):
        player.set_opponent(0)
    dummy_player = RandomPlayer()
    player.set_opponent(dummy_player)
    assert player.opponent == dummy_player


@patch(
    "poke_env.environment.pokemon.Pokemon.available_z_moves",
    new_callable=unittest.mock.PropertyMock,
)
def test_action_to_move(z_moves_mock):
    for PlayerClass, (has_megas, has_z_moves, has_dynamax) in zip(
        [
            Gen4EnvSinglePlayer,
            Gen5EnvSinglePlayer,
            Gen6EnvSinglePlayer,
            Gen7EnvSinglePlayer,
            Gen8EnvSinglePlayer,
        ],
        [
            (False, False, False),
            (False, False, False),
            (True, False, False),
            (True, True, False),
            (True, True, True),
        ],
    ):

        class CustomEnvClass(PlayerClass):
            def embed_battle(self, *args, **kwargs):
                return []

            def calc_reward(self, last_battle, current_battle):
                return 0.0

            def describe_embedding(self):
                return None

            def get_opponent(self):
                return None

        p = CustomEnvClass(start_listening=False, start_challenging=False)
        battle = Battle("bat1", p.username, p.logger)
        assert p.action_to_move(-1, battle).message == "/forfeit"
        battle._available_moves = [Move("flamethrower")]
        assert p.action_to_move(0, battle).message == "/choose move flamethrower"
        battle._available_switches = [Pokemon(species="charizard")]
        assert (
            p.action_to_move(
                4
                + (4 * int(has_megas))
                + (4 * int(has_z_moves) + (4 * int(has_dynamax))),
                battle,
            ).message
            == "/choose switch charizard"
        )
        battle._available_switches = []
        assert p.action_to_move(3, battle).message == "/choose move flamethrower"
        if has_megas:
            battle._can_mega_evolve = True
            assert (
                p.action_to_move(4 + (4 * int(has_z_moves)), battle).message
                == "/choose move flamethrower mega"
            )
            battle._can_mega_evolve = False
        if has_z_moves:
            battle._can_z_move = True
            active_pokemon = Pokemon(species="charizard")
            active_pokemon._active = True
            battle._team = {"charizard": active_pokemon}
            z_moves_mock.return_value = [Move("flamethrower")]
            assert (
                p.action_to_move(4, battle).message == "/choose move flamethrower zmove"
            )
            battle._team = {}
        if has_dynamax:
            battle._can_dynamax = True
            assert (
                p.action_to_move(12, battle).message
                == "/choose move flamethrower dynamax"
            )
