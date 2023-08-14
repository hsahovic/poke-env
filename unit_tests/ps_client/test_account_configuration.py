from poke_env.ps_client.account_configuration import (
    _create_account_configuration_from_player,
)


def test_account_configuration_auto_naming():
    class ShortPlayer:
        pass

    class VeryLongPlayerClassName:
        pass

    assert (
        _create_account_configuration_from_player(ShortPlayer()).username
        == "ShortPlayer 1"
    )
    assert (
        _create_account_configuration_from_player(ShortPlayer()).username
        == "ShortPlayer 2"
    )
    assert (
        _create_account_configuration_from_player(VeryLongPlayerClassName()).username
        == "VeryLongPlayerCl 1"
    )
    assert (
        _create_account_configuration_from_player(VeryLongPlayerClassName()).username
        == "VeryLongPlayerCl 2"
    )
    assert (
        _create_account_configuration_from_player(VeryLongPlayerClassName()).username
        == "VeryLongPlayerCl 3"
    )
    assert (
        _create_account_configuration_from_player(VeryLongPlayerClassName()).username
        == "VeryLongPlayerCl 4"
    )
    assert (
        _create_account_configuration_from_player(VeryLongPlayerClassName()).username
        == "VeryLongPlayerCl 5"
    )
    assert (
        _create_account_configuration_from_player(VeryLongPlayerClassName()).username
        == "VeryLongPlayerCl 6"
    )
    assert (
        _create_account_configuration_from_player(VeryLongPlayerClassName()).username
        == "VeryLongPlayerCl 7"
    )
    assert (
        _create_account_configuration_from_player(VeryLongPlayerClassName()).username
        == "VeryLongPlayerCl 8"
    )
    assert (
        _create_account_configuration_from_player(VeryLongPlayerClassName()).username
        == "VeryLongPlayerCl 9"
    )
    assert (
        _create_account_configuration_from_player(VeryLongPlayerClassName()).username
        == "VeryLongPlayerC 10"
    )
