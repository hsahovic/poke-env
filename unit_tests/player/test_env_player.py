import asyncio

import numpy as np
from gymnasium.spaces import Box, Discrete

from poke_env.concurrency import POKE_LOOP
from poke_env.environment import (
    AbstractBattle,
    Battle,
    DoubleBattle,
    Move,
    Pokemon,
    PokemonType,
    Status,
)
from poke_env.player import (
    BattleOrder,
    DoubleBattleOrder,
    DoublesEnv,
    ForfeitBattleOrder,
    Player,
    PokeEnv,
    SinglesEnv,
)
from poke_env.player.gymnasium_api import _EnvPlayer
from poke_env.ps_client import AccountConfiguration, ServerConfiguration

account_configuration1 = AccountConfiguration("username1", "password1")
account_configuration2 = AccountConfiguration("username2", "password2")
server_configuration = ServerConfiguration("server.url", "auth.url")


class CustomEnv(SinglesEnv):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.observation_spaces = {agent: Box(-1, 1) for agent in self.possible_agents}

    def calc_reward(self, battle) -> float:
        return 0.0

    def embed_battle(self, battle):
        return []


def test_init():
    gymnasium_env = CustomEnv(
        account_configuration1=account_configuration1,
        account_configuration2=account_configuration2,
        server_configuration=server_configuration,
        start_listening=False,
        battle_format="gen7randombattles",
    )
    player = gymnasium_env.agent1
    assert isinstance(gymnasium_env, CustomEnv)
    assert isinstance(player, _EnvPlayer)


async def run_test_choose_move():
    player = CustomEnv(
        account_configuration1=account_configuration1,
        account_configuration2=account_configuration2,
        server_configuration=server_configuration,
        start_listening=False,
        battle_format="gen7randombattles",
        start_challenging=False,
    )

    # Create a mock battle and moves
    battle = Battle("bat1", player.agent1.username, player.agent1.logger, gen=8)
    battle._available_moves = [Move("flamethrower", gen=8)]

    # Test choosing a move
    message = await player.agent1.choose_move(battle)
    order = player.action_to_order(np.int64(6), battle)
    player.agent1.order_queue.put(order)

    assert message.message == "/choose move flamethrower"

    # Test switching Pokémon
    battle._available_switches = [Pokemon(species="charizard", gen=8)]
    message = await player.agent1.choose_move(battle)
    order = player.action_to_order(np.int64(0), battle)
    player.agent1.order_queue.put(order)

    assert message.message == "/choose switch charizard"


def test_choose_move():
    asyncio.run_coroutine_threadsafe(run_test_choose_move(), POKE_LOOP)


def test_reward_computing_helper():
    player = CustomEnv(
        account_configuration1=account_configuration1,
        account_configuration2=account_configuration2,
        server_configuration=server_configuration,
        start_listening=False,
        battle_format="gen7randombattles",
    )
    battle_1 = Battle("bat1", player.agent1.username, player.agent1.logger, gen=8)
    battle_2 = Battle("bat2", player.agent1.username, player.agent1.logger, gen=8)
    battle_3 = Battle("bat3", player.agent1.username, player.agent1.logger, gen=8)
    battle_4 = Battle("bat4", player.agent1.username, player.agent1.logger, gen=8)

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

    battle_3._team = {i: Pokemon(species="slaking", gen=8) for i in range(4)}
    battle_3._opponent_team = {i: Pokemon(species="slowbro", gen=8) for i in range(3)}

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
    player = CustomEnv(start_listening=False)
    assert player.action_space(player.possible_agents[0]) == Discrete(4 * 4 + 6)
    for i, (has_megas, has_z_moves, has_dynamax) in enumerate(
        [
            (False, False, False),
            (False, False, False),
            (True, False, False),
            (True, True, False),
            (True, True, True),
        ]
    ):
        p = CustomEnv(
            battle_format=f"gen{i + 4}randombattle",
            start_listening=False,
            start_challenging=False,
        )
        assert p.action_space(p.possible_agents[0]) == Discrete(
            4 * sum([1, has_megas, has_z_moves, has_dynamax]) + 6
        )


def test_singles_action_order_conversions():
    for gen, (has_megas, has_z_moves, has_dynamax, has_tera) in enumerate(
        [
            (False, False, False, False),
            (False, False, False, False),
            (True, False, False, False),
            (True, True, False, False),
            (True, True, True, False),
            (True, True, True, True),
        ],
        start=4,
    ):
        p = SinglesEnv(
            battle_format=f"gen{gen}randombattle",
            start_listening=False,
            start_challenging=False,
        )
        battle = Battle("bat1", p.agent1.username, p.agent1.logger, gen=gen)
        active_pokemon = Pokemon(species="charizard", gen=gen)
        move = Move("flamethrower", gen=gen)
        active_pokemon._moves = {move.id: move}
        active_pokemon._active = True
        active_pokemon._item = "firiumz"
        battle._team = {"charizard": active_pokemon}
        assert p.action_to_order(np.int64(-1), battle).message == "/forfeit"
        check_action_order_roundtrip(p, ForfeitBattleOrder(), battle)
        battle._available_moves = [move]
        assert (
            p.action_to_order(np.int64(6), battle).message
            == "/choose move flamethrower"
        )
        check_action_order_roundtrip(p, Player.create_order(move), battle)
        battle._available_switches = [active_pokemon]
        assert (
            p.action_to_order(np.int64(0), battle).message == "/choose switch charizard"
        )
        check_action_order_roundtrip(p, Player.create_order(active_pokemon), battle)
        battle._available_switches = []
        assert (
            p.action_to_order(np.int64(9), battle).message
            == "/choose move flamethrower"
        )
        if has_megas:
            battle._can_mega_evolve = True
            assert (
                p.action_to_order(np.int64(6 + 4), battle).message
                == "/choose move flamethrower mega"
            )
            check_action_order_roundtrip(
                p, Player.create_order(move, mega=True), battle
            )
        if has_z_moves:
            battle._can_z_move = True
            assert (
                p.action_to_order(np.int64(6 + 4 + 4), battle).message
                == "/choose move flamethrower zmove"
            )
            check_action_order_roundtrip(
                p, Player.create_order(move, z_move=True), battle
            )
        if has_dynamax:
            battle._can_dynamax = True
            assert (
                p.action_to_order(np.int64(6 + 4 + 8), battle).message
                == "/choose move flamethrower dynamax"
            )
            check_action_order_roundtrip(
                p, Player.create_order(move, dynamax=True), battle
            )
        if has_tera:
            battle._can_tera = PokemonType.FIRE
            assert (
                p.action_to_order(np.int64(6 + 4 + 12), battle).message
                == "/choose move flamethrower terastallize"
            )
            check_action_order_roundtrip(
                p, Player.create_order(move, terastallize=True), battle
            )


def test_doubles_action_order_conversions():
    for gen, (has_megas, has_z_moves, has_dynamax, has_tera) in enumerate(
        [
            (True, True, True, False),
            (True, True, True, True),
        ],
        start=8,
    ):
        p = DoublesEnv(
            battle_format=f"gen{gen}randomdoublesbattle",
            start_listening=False,
            start_challenging=False,
        )
        battle = DoubleBattle("bat1", p.agent1.username, p.agent1.logger, gen=gen)
        battle._player_role = "p1"
        active_pokemon = Pokemon(species="charizard", gen=gen)
        move = Move("flamethrower", gen=gen)
        active_pokemon._moves = {move.id: move}
        active_pokemon._active = True
        active_pokemon._item = "firiumz"
        battle._team = {"charizard": active_pokemon}
        battle._opponent_active_pokemon = {"p2a": active_pokemon}
        battle._active_pokemon = {"p1a": active_pokemon}
        assert p.action_to_order(np.array([-1, 0]), battle).message == "/forfeit"
        check_action_order_roundtrip(p, ForfeitBattleOrder(), battle)
        battle._available_moves = [[move], []]
        assert (
            p.action_to_order(np.array([7 + 12, 0]), battle).message
            == "/choose move flamethrower 1, default"
        )
        check_action_order_roundtrip(
            p, DoubleBattleOrder(Player.create_order(move, move_target=1)), battle
        )
        battle._available_switches = [[active_pokemon], []]
        assert (
            p.action_to_order(np.array([1, 0]), battle).message
            == "/choose switch charizard, default"
        )
        check_action_order_roundtrip(
            p, DoubleBattleOrder(Player.create_order(active_pokemon)), battle
        )
        battle._available_switches = [[], []]
        assert (
            p.action_to_order(np.array([10 + 12, 0]), battle).message
            == "/choose move flamethrower 1, default"
        )
        if has_megas:
            battle._can_mega_evolve = [True, True]
            assert (
                p.action_to_order(np.array([7 + 12 + 20, 0]), battle).message
                == "/choose move flamethrower mega 1, default"
            )
            check_action_order_roundtrip(
                p,
                DoubleBattleOrder(Player.create_order(move, mega=True, move_target=1)),
                battle,
            )
        if has_z_moves:
            battle._can_z_move = [True, True]
            assert (
                p.action_to_order(np.array([7 + 12 + 20 + 20, 0]), battle).message
                == "/choose move flamethrower zmove 1, default"
            )
            check_action_order_roundtrip(
                p,
                DoubleBattleOrder(
                    Player.create_order(move, z_move=True, move_target=1)
                ),
                battle,
            )
        if has_dynamax:
            battle._can_dynamax = [True, True]
            assert (
                p.action_to_order(np.array([7 + 12 + 20 + 40, 0]), battle).message
                == "/choose move flamethrower dynamax 1, default"
            )
            check_action_order_roundtrip(
                p,
                DoubleBattleOrder(
                    Player.create_order(move, dynamax=True, move_target=1)
                ),
                battle,
            )
        if has_tera:
            battle._can_tera = [PokemonType.FIRE, PokemonType.FIRE]
            assert (
                p.action_to_order(np.array([7 + 12 + 20 + 60, 0]), battle).message
                == "/choose move flamethrower terastallize 1, default"
            )
            check_action_order_roundtrip(
                p,
                DoubleBattleOrder(
                    Player.create_order(move, terastallize=True, move_target=1)
                ),
                battle,
            )


def check_action_order_roundtrip(
    env: PokeEnv, order: BattleOrder, battle: AbstractBattle
):
    a = env.order_to_action(order, battle)
    o = env.action_to_order(a, battle)
    assert order.message == o.message
