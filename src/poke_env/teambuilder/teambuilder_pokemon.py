"""This module defines the TeambuilderPokemon class, which is used as an intermediate
format to specify pokemon builds in teambuilders custom classes.
"""

from typing import List, Optional

from poke_env.data import to_id_str
from poke_env.stats import STATS_TO_IDX


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
        return self.packed

    def __str__(self) -> str:
        return self.packed

    @property
    def packed_evs(self) -> str:
        f_evs = ",".join([str(el) if el != 0 else "" for el in self.evs])
        if f_evs == "," * 5:
            return ""
        return f_evs

    @property
    def packed_ivs(self) -> str:
        f_ivs = ",".join([str(iv) if iv != 31 else "" for iv in self.ivs])
        if f_ivs == "," * 5:
            return ""
        return f_ivs

    @property
    def packed_moves(self) -> str:
        return ",".join([to_id_str(move) for move in self.moves])

    @property
    def packed_endstring(self) -> str:
        f_str = f",{self.hiddenpowertype or ''},"

        if self.gmax:
            return f_str + ",G"
        elif self.tera_type:
            return f_str + f",,,{self.tera_type}"

        if self.hiddenpowertype:
            return f_str

        return ""

    @property
    def packed(self) -> str:
        self._prepare_for_formatting()
        return "%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s%s" % (
            self.nickname or "",
            to_id_str(self.species) if self.species else "",
            to_id_str(self.item) if self.item else "",
            to_id_str(self.ability) if self.ability else "",
            self.packed_moves or "",
            self.nature or "",
            self.packed_evs or "",
            self.gender or "",
            self.packed_ivs or "",
            "S" if self.shiny else "",
            self.level or "",
            self.happiness or "",
            self.packed_endstring,
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

    @staticmethod
    def from_packed(packed_mon: str) -> "TeambuilderPokemon":
        """Converts a packed-format pokemon string into a TeambuilderPokemon object.

        :param packed_mon: The packed-format pokemon string to convert.
        :type packed_mon: str
        :return: The converted TeambuilderPokemon object.
        :rtype: TeambuilderPokemon
        """
        (
            raw_nickname,
            raw_species,
            raw_item,
            raw_ability,
            raw_moves,
            raw_nature,
            raw_evs,
            raw_gender,
            raw_ivs,
            raw_shiny,
            raw_level,
            endstring,
        ) = packed_mon.split("|")

        gmax = False
        tera_type = None
        hiddenpowertype = None
        happiness = None

        if endstring:
            split_endstring = endstring.split(",")

            if split_endstring[0]:
                happiness = int(split_endstring[0])

            if len(split_endstring) == 1:
                pass
            elif split_endstring[-1] == "G":
                gmax = True
            elif split_endstring[-1] != "":
                tera_type = split_endstring[-1]
            elif len(split_endstring) >= 3:
                hiddenpowertype = split_endstring[-2]

        nickname = raw_nickname or None
        species = raw_species or None
        item = raw_item or None
        ability = raw_ability or None
        nature = raw_nature or None
        gender = raw_gender or None

        if raw_moves:
            moves = raw_moves.split(",")
        else:
            moves = None

        if raw_evs:
            evs = [int(ev) if ev else 0 for ev in raw_evs.split(",")]
        else:
            evs = None

        if raw_ivs:
            ivs = [int(iv) if iv else 31 for iv in raw_ivs.split(",")]
        else:
            ivs = None

        if raw_shiny:
            assert raw_shiny == "S"
            shiny = True
        else:
            shiny = False

        if raw_level:
            level = int(raw_level)
        else:
            level = None

        return TeambuilderPokemon(
            nickname=nickname,
            species=species,
            item=item,
            ability=ability,
            moves=moves,
            nature=nature,
            evs=evs,
            gender=gender,
            ivs=ivs,
            shiny=shiny,
            level=level,
            happiness=happiness,
            hiddenpowertype=hiddenpowertype,
            gmax=gmax,
            tera_type=tera_type,
        )

    @staticmethod
    def from_showdown(showdown_mon: str) -> "TeambuilderPokemon":
        """Converts a showdown-format pokemon string into a TeambuilderPokemon object.

        :param showdown_mon: The showdown-format pokemon string to convert.
        :type showdown_mon: str
        :return: The converted TeambuilderPokemon object.
        :rtype: TeambuilderPokemon
        """
        mon = TeambuilderPokemon()

        for line in showdown_mon.split("\n"):
            while line and line.startswith(" "):
                line = line[1:]

            if not line:
                continue
            elif line.startswith("Ability"):
                ability = line.replace("Ability: ", "")
                mon.ability = ability.strip()
            elif line.startswith("Level: "):
                level = line.replace("Level: ", "")
                mon.level = int(level.strip())
            elif line.startswith("Happiness: "):
                happiness = line.replace("Happiness: ", "")
                mon.happiness = int(happiness.strip())
            elif line.startswith("EVs: "):
                evs = line.replace("EVs: ", "")
                split_evs = evs.split(" / ")
                for ev in split_evs:
                    n, stat = ev.split(" ")[:2]
                    idx = STATS_TO_IDX[stat.lower()]
                    mon.evs[idx] = int(n)
            elif line.startswith("IVs: "):
                ivs = line.replace("IVs: ", "")
                ivs_split = ivs.split(" / ")
                for iv in ivs_split:
                    n, stat = iv.split(" ")[:2]
                    idx = STATS_TO_IDX[stat.lower()]
                    mon.ivs[idx] = int(n)
            elif line.startswith("- "):
                line = line.replace("- ", "").strip()
                mon.moves.append(line)
            elif line.startswith("Shiny"):
                mon.shiny = line.strip().endswith("Yes")
            elif line.startswith("Gigantamax"):
                mon.gmax = line.strip().endswith("Yes")
            elif line.strip().endswith(" Nature"):
                nature = line.strip().replace(" Nature", "")
                mon.nature = nature
            elif line.startswith("Hidden Power: "):
                hp_type = line.replace("Hidden Power: ", "").strip()
                mon.hiddenpowertype = hp_type
            elif line.startswith("Tera Type: "):
                tera_type = line.replace("Tera Type: ", "").strip()
                mon.tera_type = tera_type
            else:
                if "@" in line:
                    mon_info, item = line.split(" @ ")
                    mon.item = item.strip()
                else:
                    mon_info = line
                split_mon_info = mon_info.split(" ")
                if split_mon_info[-1] == "(M)":
                    mon.gender = "M"
                    split_mon_info.pop()
                if split_mon_info[-1] == "(F)":
                    mon.gender = "F"
                    split_mon_info.pop()
                if split_mon_info[-1].endswith(")"):
                    for i, info in enumerate(split_mon_info):
                        if info[0] == "(":
                            mon.species = " ".join(split_mon_info[i:])[1:-1]
                            split_mon_info = split_mon_info[:i]
                            break
                mon.nickname = " ".join(split_mon_info)

        return mon
