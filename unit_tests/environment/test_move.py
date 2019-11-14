# -*- coding: utf-8 -*-
from poke_env.data import MOVES
from poke_env.environment.move import Move


def move_generator():
    for move in MOVES:
        yield Move(move)


def test_all_moves_instanciate():
    for move in move_generator():
        pass


def test_move_accuracies():
    for move in move_generator():
        assert isinstance(move.accuracy, float)
        assert 0 <= move.accuracy <= 1


def test_move_base_power():
    for move in move_generator():
        assert isinstance(move.base_power, int)
        assert 0 <= move.base_power <= 255


def test_move_breaks_protect():
    for move in move_generator():
        assert isinstance(move.breaks_protect, bool)
