# -*- coding: utf-8 -*-
from poke_env.environment.battle import Battle
from poke_env.environment.move import Move
from poke_env.environment.pokemon import Pokemon
from poke_env.environment.status import Status
from poke_env.player.env_player import EnvPlayer
from poke_env.player.env_player import (
    Gen4EnvSinglePlayer,
    Gen5EnvSinglePlayer,
    Gen6EnvSinglePlayer,
    Gen7EnvSinglePlayer,
    Gen8EnvSinglePlayer,
)

from poke_env.player_configuration import PlayerConfiguration
from poke_env.server_configuration import ServerConfiguration
from unittest.mock import patch


player_configuration = PlayerConfiguration("username", "password")
server_configuration = ServerConfiguration("server.url", "auth.url")


class CustomEnvPlayer(EnvPlayer):
    def embed_battle(self, battle):
        return None

    def _action_to_move(self, action, battle):
        return Gen7EnvSinglePlayer._action_to_move(self, action, battle)

    @property
    def action_space(self):
        return Gen7EnvSinglePlayer._ACTION_SPACE


def test_init():
    player = CustomEnvPlayer(
        player_configuration=player_configuration,
        server_configuration=server_configuration,
        start_listening=False,
        battle_format="gen7randombattles",
    )
    assert player


@patch("poke_env.player.env_player.Queue.get", return_value=2)
def test_choose_move(queue_get_mock):
    player = CustomEnvPlayer(
        player_configuration=player_configuration,
        server_configuration=server_configuration,
        start_listening=False,
        battle_format="gen7randombattles",
    )
    battle = Battle("bat1", player.username, player.logger)
    battle._available_moves = {Move("flamethrower")}

    assert player.choose_move(battle).message == "/choose move flamethrower"

    battle._available_moves = {Pokemon(species="charizard")}

    assert player.choose_move(battle).message == "/choose switch charizard"


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

    battle_4._team, battle_4._opponent_team = battle_3._opponent_team, battle_3._team
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
    for i, el in enumerate(player.action_space):
        assert i == el
    assert len(player.action_space) == 18

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

        assert (
            len(CustomEnvClass().action_space)
            == 4 * sum([1, has_megas, has_z_moves, has_dynamax]) + 6
        )
