import asyncio

from gymnasium.spaces import Box, Discrete

from poke_env.concurrency import POKE_LOOP
from poke_env.environment import Battle, Move, Pokemon, PokemonType, Status
from poke_env.player import PokeEnv
from poke_env.player.poke_env import _EnvPlayer
from poke_env.ps_client import AccountConfiguration, ServerConfiguration

account_configuration1 = AccountConfiguration("username1", "password1")
account_configuration2 = AccountConfiguration("username2", "password2")
server_configuration = ServerConfiguration("server.url", "auth.url")


class CustomEnv(PokeEnv):
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
    order = player.action_to_order(6, battle)
    player.agent1.order_queue.put(order)

    assert message.message == "/choose move flamethrower"

    # Test switching Pokémon
    battle._available_switches = [Pokemon(species="charizard", gen=8)]
    message = await player.agent1.choose_move(battle)
    order = player.action_to_order(0, battle)
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

    for battle_format, (has_megas, has_z_moves, has_dynamax) in zip(
        [
            "gen4randombattle",
            "gen5randombattle",
            "gen6randombattle",
            "gen7randombattle",
            "gen8randombattle",
        ],
        [
            (False, False, False),
            (False, False, False),
            (True, False, False),
            (True, True, False),
            (True, True, True),
        ],
    ):

        p = CustomEnv(
            battle_format=battle_format, start_listening=False, start_challenging=False
        )

        assert p.action_space(p.possible_agents[0]) == Discrete(
            4 * sum([1, has_megas, has_z_moves, has_dynamax]) + 6
        )


def test_action_to_move():
    for i, (has_megas, has_z_moves, has_dynamax, has_tera) in enumerate(
        [
            (False, False, False, False),
            (False, False, False, False),
            (True, False, False, False),
            (True, True, False, False),
            (True, True, True, False),
            (True, True, True, True),
        ]
    ):
        p = PokeEnv(
            battle_format=f"gen{i + 4}randombattle",
            start_listening=False,
            start_challenging=False,
        )
        battle = Battle("bat1", p.agent1.username, p.agent1.logger, gen=8)
        active_pokemon = Pokemon(species="charizard", gen=8)
        move = Move("flamethrower", gen=8)
        active_pokemon._moves = {move.id: move}
        active_pokemon._active = True
        active_pokemon._item = "firiumz"
        battle._team = {"charizard": active_pokemon}
        assert p.action_to_order(-1, battle).message == "/forfeit"
        battle._available_switches = [active_pokemon]
        assert p.action_to_order(0, battle).message == "/choose switch charizard"
        battle._available_moves = [move]
        assert p.action_to_order(6, battle).message == "/choose move flamethrower"
        if has_megas:
            battle._can_mega_evolve = True
            assert (
                p.action_to_order(6 + 4, battle).message
                == "/choose move flamethrower mega"
            )
        if has_z_moves:
            battle._can_z_move = True
            assert (
                p.action_to_order(6 + 4 + 4, battle).message
                == "/choose move flamethrower zmove"
            )
        if has_dynamax:
            battle._can_dynamax = True
            assert (
                p.action_to_order(6 + 4 + 8, battle).message
                == "/choose move flamethrower dynamax"
            )
        if has_tera:
            battle._can_tera = PokemonType.FIRE
            assert (
                p.action_to_order(6 + 4 + 12, battle).message
                == "/choose move flamethrower terastallize"
            )
