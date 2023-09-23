from poke_env.environment import AbstractBattle
from poke_env.player import BattleOrder, Player


def test_account_configuration_auto_naming():
    class ShortPlayer(Player):
        def choose_move(self, battle: AbstractBattle) -> BattleOrder:
            return self.choose_default_move()

    class VeryLongPlayerClassName(Player):
        def choose_move(self, battle: AbstractBattle) -> BattleOrder:
            return self.choose_default_move()

    assert ShortPlayer().username == "ShortPlayer 1"
    assert ShortPlayer().username == "ShortPlayer 2"
    assert VeryLongPlayerClassName().username == "VeryLongPlayerCl 1"
    assert VeryLongPlayerClassName().username == "VeryLongPlayerCl 2"
    assert VeryLongPlayerClassName().username == "VeryLongPlayerCl 3"
    assert VeryLongPlayerClassName().username == "VeryLongPlayerCl 4"
    assert VeryLongPlayerClassName().username == "VeryLongPlayerCl 5"
    assert VeryLongPlayerClassName().username == "VeryLongPlayerCl 6"
    assert VeryLongPlayerClassName().username == "VeryLongPlayerCl 7"
    assert VeryLongPlayerClassName().username == "VeryLongPlayerCl 8"
    assert VeryLongPlayerClassName().username == "VeryLongPlayerCl 9"
    assert VeryLongPlayerClassName().username == "VeryLongPlayerC 10"
