from poke_env.environment import DoublesEnv, SinglesEnv


def test_default_format_is_doubles():
    env = DoublesEnv(start_listening=False)
    try:
        assert env._battle_format == "gen9randomdoublesbattle"
        assert env.agent1.format_is_doubles
        assert env.agent2.format_is_doubles
    finally:
        env.close()


def test_singles_default_format_is_gen9():
    env = SinglesEnv(start_listening=False)
    try:
        assert env._battle_format == "gen9randombattle"
        assert not env.agent1.format_is_doubles
        assert not env.agent2.format_is_doubles
    finally:
        env.close()
