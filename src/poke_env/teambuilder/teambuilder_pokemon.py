# -*- coding: utf-8 -*-
"""This module defines the TeambuilderPokemon class, which is used as an intermediate
format to specify pokemon builds in teambuilders custom classes.
"""
from poke_env.utils import to_id_str


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

    @property
    def formatted_evs(self):
        f_evs = ",".join([str(el) if el != 0 else "" for el in self.evs])
        if f_evs == "," * 5:
            return ""
        return f_evs

    @property
    def formatted_ivs(self):
        f_ivs = ",".join([str(el) if el != 31 else "" for el in self.ivs])
        if f_ivs == "," * 5:
            return ""
        return f_ivs

    @property
    def formatted_moves(self):
        return ",".join([to_id_str(move) for move in self.moves])

    @property
    def formatted_endstring(self):
        if self.hiddenpowertype:
            return ",%s," % self.hiddenpowertype
        return ""

    @property
    def formatted(self):
        return "%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s%s" % (
            self.nickname or "",
            to_id_str(self.species) if self.species else "",
            to_id_str(self.item) if self.item else "",
            to_id_str(self.ability) if self.ability else "",
            self.formatted_moves or "",
            self.nature or "",
            self.formatted_evs or "",
            self.gender or "",
            self.formatted_ivs or "",
            "S" if self.shiny else "",
            self.level or "",
            self.happiness or "",
            self.formatted_endstring,
        )
