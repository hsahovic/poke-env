"""This module defines the TeambuilderPokemon class, which is used as an intermediate
format to specify pokemon builds in teambuilders custom classes.
"""

from __future__ import annotations

from typing import List, Optional

from poke_env.data import to_id_str


class TeambuilderPokemon:
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
    evs: List[int]
    ivs: List[int]
    moves: List[str]

    def __init__(
        self,
        nickname: Optional[str] = None,
        species: Optional[str] = None,
        item: Optional[str] = None,
        ability: Optional[str] = None,
        moves: Optional[List[str]] = None,
        nature: Optional[str] = None,
        evs: Optional[List[int]] = None,
        gender: Optional[str] = None,
        ivs: Optional[List[int]] = None,
        shiny: Optional[bool] = None,
        level: Optional[int] = None,
        happiness: Optional[int] = None,
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
        self.evs = evs if evs is not None else [0] * 6
        self.ivs = ivs if ivs is not None else [31] * 6

        if moves is None:
            self.moves = []
        else:
            self.moves = moves

    def __repr__(self) -> str:
        return self.formatted

    def __str__(self) -> str:
        return self.formatted

    @classmethod
    def parse_showteam_pkmn_substr(cls, substr: str) -> TeambuilderPokemon:
        split_msg = substr.split("|")
        return TeambuilderPokemon(
            nickname=split_msg[0] or None,
            species=to_id_str(split_msg[1]) if split_msg[1] else None,
            item=to_id_str(split_msg[2]) if split_msg[2] else None,
            ability=to_id_str(split_msg[3]) if split_msg[3] else None,
            moves=(
                [to_id_str(m) for m in split_msg[4].split(",")]
                if split_msg[4]
                else None
            ),
            nature=split_msg[5] or None,
            evs=(
                [int(e) if e != "" else 0 for e in split_msg[6].split(",")]
                if split_msg[6]
                else None
            ),
            gender=split_msg[7] or None,
            ivs=(
                [int(i) if i != "" else 31 for i in split_msg[8].split(",")]
                if split_msg[8]
                else None
            ),
            shiny=split_msg[9] == "S" if split_msg[9] else None,
            level=int(split_msg[10]) if split_msg[10] else None,
            tera_type=split_msg[11].split(",")[-1] if split_msg[11] else None,
        )

    @property
    def formatted_evs(self) -> str:
        f_evs = ",".join([str(el) if el != 0 else "" for el in self.evs])
        if f_evs == "," * 5:
            return ""
        return f_evs

    @property
    def formatted_ivs(self) -> str:
        f_ivs = ",".join([str(el) if el != 31 else "" for el in self.ivs])
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
            if (
                move.startswith("hiddenpower")
                and len(move) > 11
                and all([iv == 31 for iv in self.ivs])
            ):
                self.ivs = list(self.HP_TO_IVS[move[11:]])
