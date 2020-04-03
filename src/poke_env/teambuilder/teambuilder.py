# -*- coding: utf-8 -*-
"""This module defines the Teambuilder abstract class, which represents objects yielding
Pokemon Showdown teams in the context of communicating with Pokemon Showdown.
"""
from abc import ABC, abstractmethod
from poke_env.teambuilder.teambuilder_pokemon import TeambuilderPokemon
from typing import List


class Teambuilder(ABC):
    @abstractmethod
    def yield_team(self):
        pass

    @staticmethod
    def parse_showdown_team(team: List[TeambuilderPokemon]) -> str:
        current_mon = None
        mons = []

        for line in team.split("\n"):
            if line == "":
                if current_mon is not None:
                    mons.append(current_mon)
                current_mon = None
            elif line.startswith("Ability"):
                ability = line.replace("Ability: ", "")
                current_mon.ability = ability.strip()
            elif line.startswith("Level: "):
                level = line.replace("Level: ", "")
                current_mon.level = level.strip()
            elif line.startswith("Happiness: "):
                happiness = line.replace("Happiness: ", "")
                current_mon.happiness = happiness.strip()
            elif line.startswith("EVs: "):
                evs = line.replace("EVs: ", "")
                evs = evs.split(" / ")
                for ev in evs:
                    ev = ev.split(" ")
                    n = ev[0]
                    stat = ev[1]
                    idx = current_mon.STATS_TO_IDX[stat.lower()]
                    current_mon.evs[idx] = n
            elif line.startswith("IVs: "):
                ivs = line.replace("IVs: ", "")
                ivs = ivs.split(" / ")
                for iv in ivs:
                    iv = iv.split(" ")
                    n = iv[0]
                    stat = iv[1]
                    idx = current_mon.STATS_TO_IDX[stat.lower()]
                    current_mon.ivs[idx] = n
            elif line.startswith("- "):
                line = line.replace("- ", "").strip()
                current_mon.moves.append(line)
            elif line.startswith("Shiny"):
                current_mon.shiny = line.strip().endswith("Yes")
            elif line.endswith(" Nature  "):
                nature = line.replace(" Nature  ", "")
                current_mon.nature = nature
            elif line.startswith("Hidden Power: "):
                hp_type = line.replace("Hidden Power: ", "").strip()
                current_mon.hiddenpowertype = hp_type
            else:
                if current_mon:
                    mons.append(current_mon)
                current_mon = TeambuilderPokemon()
                if "@" in line:
                    mon_info, item = line.split(" @ ")
                    current_mon.item = item.strip()
                else:
                    mon_info = line
                split_mon_info = mon_info.split(" ")

                if len(split_mon_info) == 1:
                    current_mon.nickname = split_mon_info[0]
                else:
                    if split_mon_info[-1] == "(M)":
                        current_mon.gender = "M"
                        split_mon_info.pop()
                    if split_mon_info[-1] == "(F)":
                        current_mon.gender = "F"
                        split_mon_info.pop()
                    if split_mon_info[-1].startswith("(") and split_mon_info[
                        -1
                    ].endswith(")"):
                        current_mon.species = split_mon_info[-1][1:-1]
                        current_mon.nickname = " ".join(split_mon_info[:-1])
                    else:
                        current_mon.nickname = split_mon_info[0]
        return mons

    @staticmethod
    def join_team(team: List[TeambuilderPokemon]) -> str:
        """Converts a list of TeambuilderPokemon objects into the corresponding packed
        showdown team format.

        :param team: The list of TeambuilderPokemon objects that form the team.
        :type team: list
        :return: The formatted team string.
        :type: str"""
        return "]".join([mon.formatted for mon in team])
