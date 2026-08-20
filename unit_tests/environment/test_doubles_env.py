from poke_env.environment import DoublesEnv


def test_default_format_is_doubles():
    env = DoublesEnv(start_listening=False)
    try:
        assert env._battle_format == "gen8randomdoublesbattle"
        assert env.agent1.format_is_doubles
        assert env.agent2.format_is_doubles
    finally:
        env.close()
