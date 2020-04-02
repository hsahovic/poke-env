# -*- coding: utf-8 -*-
"""This module defines the TeambuilderPokemon class, which is used as an intermediate
format to specify pokemon builds in teambuilders custom classes.
"""


class TeambuilderPokemon:
    STATS_TO_IDX = {"hp": 0, "atk": 1, "def": 2, "spa": 3, "spd": 4, "spe": 5}

    def __init__(
        self,
        nickname=None,
        species=None,
        item=None,
        ability=None,
        moves=None,
        nature=None,
        evs=None,
        gender=None,
        ivs=None,
        shiny=None,
        level=None,
        happiness=None,
        hiddenpowertype=None,
    ):
        self.nickname = nickname
        self.species = species
        self.item = item
        self.ability = ability
        self.nature = nature
        self.gender = gender
        self.shiny = shiny
        self.level = level
        self.happiness = happiness
        self.hiddenpowertype = hiddenpowertype

        if evs is not None:
            self.evs = evs
        else:
            self.evs = [0, 0, 0, 0, 0, 0]

        if ivs is not None:
            self.ivs = ivs
        else:
            self.ivs = [31, 31, 31, 31, 31, 31]

        if moves is None:
            self.moves = []
        else:
            self.moves = moves
