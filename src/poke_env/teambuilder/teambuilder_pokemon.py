"""This module defines the TeambuilderPokemon class, which is used as an intermediate
format to specify pokemon builds in teambuilders custom classes.
"""
from typing import List, Optional

from poke_env.data import to_id_str
from poke_env.stats import STATS_TO_IDX


class TeambuilderPokemon:
    STATS_TO_IDX = STATS_TO_IDX

    HP_TO_IVS = {
        "bug": [31, 31, 31, 30, 31, 30],
        "dark": [31, 31, 31, 31, 31, 31],
        "dragon": [30, 31, 31, 31, 31, 31],
        "electric": [31, 31, 31, 31, 30, 31],
        "fighting": [31, 31, 30, 30, 30, 30],
        "fire": [31, 30, 31, 30, 31, 30],
        "flying": [31, 31, 31, 30, 30, 30],
        "ghost": [31, 30, 31, 31, 31, 30],
        "grass": [30, 31, 31, 31, 30, 31],
        "ground": [31, 31, 31, 31, 30, 30],
        "ice": [31, 30, 30, 31, 31, 31],
        "poison": [31, 31, 30, 31, 30, 30],
        "psychic": [30, 31, 31, 30, 31, 31],
        "rock": [31, 31, 30, 30, 31, 30],
        "steel": [31, 31, 31, 31, 31, 30],
        "water": [31, 31, 31, 30, 30, 31],
    }

    def __init__(
        self,
        nickname: Optional[str] = None,
        species: Optional[str] = None,
        item: Optional[str] = None,
        ability: Optional[str] = None,
        moves: Optional[List[str]] = None,
        nature: Optional[str] = None,
        evs: List[Optional[str]] = [None] * 6,
        gender: Optional[str] = None,
        ivs: List[Optional[str]] = [None] * 6,
        shiny: Optional[bool] = None,
        level: Optional[str] = None,
        happiness: Optional[str] = None,
        hiddenpowertype: Optional[str] = None,
        gmax: Optional[bool] = None,
        tera_type: Optional[str] = None,
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
        self.gmax = gmax
        self.tera_type = tera_type
        self.evs = evs
        self.ivs = ivs

        if moves is None:
            self.moves = []
        else:
            self.moves = moves

    def __repr__(self) -> str:
        return self.formatted

    def __str__(self) -> str:
        return self.formatted

    @property
    def formatted_evs(self) -> str:
        f_evs = ",".join(
            [el if el is not None and el != "0" else "" for el in self.evs]
        )
        if f_evs == "," * 5:
            return ""
        return f_evs

    @property
    def formatted_ivs(self) -> str:
        f_ivs = ",".join(
            [el if el is not None and el != "31" else "" for el in self.ivs]
        )
        if f_ivs == "," * 5:
            return ""
        return f_ivs

    @property
    def formatted_moves(self) -> str:
        return ",".join([to_id_str(move) for move in self.moves])

    @property
    def formatted_endstring(self) -> str:
        f_str = f",{self.hiddenpowertype or ''},"

        if self.gmax:
            return f_str + ",G"
        elif self.tera_type:
            return f_str + f",,,{self.tera_type}"

        if self.hiddenpowertype:
            return f_str

        return ""

    @property
    def formatted(self) -> str:
        self._prepare_for_formatting()
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

    def _prepare_for_formatting(self):
        for move in self.moves:
            move = to_id_str(move)
            if move.startswith("hiddenpower") and all([iv is None for iv in self.ivs]):
                if len(move) > 11:
                    self.ivs = [str(iv) for iv in self.HP_TO_IVS[move[11:]]]
        self.ivs = [iv if iv is not None else "31" for iv in self.ivs]
        self.evs = [ev if ev is not None else "0" for ev in self.evs]
