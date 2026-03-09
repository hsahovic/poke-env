from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from poke_env.battle.effect import Effect
from poke_env.battle.field import Field
from poke_env.battle.move import SPECIAL_MOVES, Move
from poke_env.battle.pokemon_gender import PokemonGender
from poke_env.battle.pokemon_type import PokemonType
from poke_env.battle.status import Status
from poke_env.battle.target import Target
from poke_env.battle.z_crystal import Z_CRYSTAL
from poke_env.data import GenData, to_id_str
from poke_env.stats import compute_raw_stats
from poke_env.teambuilder.teambuilder_pokemon import TeambuilderPokemon


class Pokemon:
    __slots__ = (
        "_ability",
        "_active",
        "_active",
        "_base_stats",
        "_boosts",
        "_current_hp",
        "_effects",
        "_first_turn",
        "_gen",
        "_gender",
        "_heightm",
        "_item",
        "_last_details",
        "_last_request",
        "_level",
        "_max_hp",
        "_forme_change_ability",
        "_moves",
        "_must_recharge",
        "_name",
        "_possible_abilities",
        "_preparing_move",
        "_preparing_target",
        "_protect_counter",
        "_shiny",
        "_stats",
        "_revealed",
        "_species",
        "_status",
        "_status_counter",
        "_selected_in_teampreview",
        "_temporary_ability",
        "_temporary_types",
        "_terastallized",
        "_terastallized_type",
        "_type_1",
        "_type_2",
        "_weightkg",
    )

    def __init__(
        self,
        gen: int,
        *,
        species: Optional[str] = None,
        name: Optional[str] = None,
        request_pokemon: Optional[Dict[str, Any]] = None,
        details: Optional[str] = None,
        teambuilder: Optional[TeambuilderPokemon] = None,
    ):
        # Species related attributes
        self._base_stats: Dict[str, int]
        self._heightm: int
        self._possible_abilities: List[str]
        self._species: str = ""
        self._type_1: PokemonType
        self._type_2: Optional[PokemonType] = None
        self._weightkg: int

        # Individual related attributes
        self._ability: Optional[str] = None
        self._gender: Optional[PokemonGender] = None
        self._level: int = 100
        self._max_hp: Optional[int] = 0
        self._moves: Dict[str, Move] = {}
        self._name: Optional[str] = None
        self._shiny: Optional[bool] = False

        # Battle related attributes
        self._gen = gen
        self._active: bool = False
        self._boosts: Dict[str, int] = {
            "accuracy": 0,
            "atk": 0,
            "def": 0,
            "evasion": 0,
            "spa": 0,
            "spd": 0,
            "spe": 0,
        }
        self._current_hp: Optional[int] = 0
        self._effects: Dict[Effect, int] = {}
        self._first_turn: bool = False
        self._terastallized: bool = False
        self._terastallized_type: Optional[PokemonType] = None
        self._item: Optional[str] = GenData.from_gen(gen).UNKNOWN_ITEM
        self._last_request: Optional[Dict[str, Any]] = {}
        self._last_details: str = ""
        self._must_recharge: bool = False
        self._preparing_move: Optional[Move] = None
        self._preparing_target: Optional[bool | Pokemon] = None
        self._protect_counter: int = 0
        self._revealed: bool = False
        self._selected_in_teampreview: bool = False
        self._stats: Dict[str, Optional[int]] = {
            "hp": None,
            "atk": None,
            "def": None,
            "spa": None,
            "spd": None,
            "spe": None,
        }
        self._status: Optional[Status] = None
        self._status_counter: int = 0
        self._temporary_ability: Optional[str] = None
        self._forme_change_ability: Optional[str] = None
        self._temporary_types: List[PokemonType] = []

        if request_pokemon:
            self.update_from_request(request_pokemon)
        elif details:
            self._update_from_details(details)
        elif species:
            self._update_from_pokedex(species)
        elif teambuilder:
            self._update_from_teambuilder(teambuilder)

        if name is not None:
            self._name = name

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        if self._status is None:
            status_repr = None
        else:
            status_repr = self._status.name

        return (
            f"{self._species} (pokemon object) "
            f"[Active: {self._active}, Status: {status_repr}]"
        )

    def _add_move(self, move_id: str, use: bool = False) -> Optional[Move]:
        """Store the move if applicable."""
        id_ = Move.retrieve_id(move_id)

        if not Move.should_be_stored(id_, self.gen):
            return None

        if id_ not in self._moves:
            move = Move(move_id=id_, raw_id=move_id, gen=self.gen)
            self._moves[id_] = move
        if use:
            self._moves[id_].use()

        return self._moves[id_]

    def boost(self, stat: str, amount: int):
        self._boosts[stat] += amount
        if self._boosts[stat] > 6:
            self._boosts[stat] = 6
        elif self._boosts[stat] < -6:
            self._boosts[stat] = -6

    def cant_move(self):
        self._first_turn = False
        self._protect_counter = 0

        if self._status == Status.SLP:
            self._status_counter += 1

    def check_consistency(self, pkmn_request: Dict[str, Any], player_role: str):
        assert (
            pkmn_request["ident"] == f"{player_role}: {self.name}"
        ), f"{pkmn_request['ident']} != {player_role}: {self.name}"
        split_details = pkmn_request["details"].split(", ")
        level = None
        gender = None
        shiny = split_details[-1] == "shiny"
        if shiny:
            split_details.pop()
        if len(split_details) == 3:
            _, level, gender = split_details
        elif len(split_details) == 2:
            if split_details[1].startswith("L"):
                _, level = split_details
            else:
                _, gender = split_details
        level = int(level[1:]) if level is not None else 100
        gender = (
            PokemonGender.from_request_details(gender)
            if gender is not None
            else PokemonGender.NEUTRAL
        )
        assert level == self.level, f"{level} != {self.level}"
        assert self.gender is not None
        assert (
            gender == self.gender
        ), f"{gender.name.lower()} != {self.gender.name.lower()}"
        assert shiny == self.shiny, f"{shiny} != {self.shiny}"
        assert (
            pkmn_request["active"] == self.active
        ), f"{pkmn_request['active']} != {self.active}"
        if self.item == "unknown_item":
            self._item = pkmn_request["item"]
        if self.gen > 4:
            assert pkmn_request["item"] == (
                self.item or ""
            ), f"{pkmn_request['item']} != {self.item or ''}"
        if self.base_species == "ditto":
            return
        assert (
            pkmn_request["condition"] == self.hp_status
        ), f"{pkmn_request['condition']} != {self.hp_status}"
        if self.base_species == "mew":
            return
        for move_request, move in zip(pkmn_request["moves"], self.moves.values()):
            assert Move.retrieve_id(move_request) == Move.retrieve_id(
                move.id
            ), f"{Move.retrieve_id(move_request)} != {Move.retrieve_id(move.id)}"
        if self.ability is None:
            self.ability = pkmn_request["baseAbility"]
        assert pkmn_request["baseAbility"] == (
            self.base_ability or ""
        ), f"{pkmn_request['baseAbility']} != {self.base_ability or ''}"
        if "ability" in pkmn_request:
            assert pkmn_request["ability"] == (
                self.ability or ""
            ), f"{pkmn_request['ability']} != {self.ability or ''}"

    def check_move_consistency(
        self, active_request: Dict[str, Any], is_doubles: bool = False
    ):
        if self.base_species in ["ditto", "mew"]:
            return
        for move_request in active_request["moves"]:
            matches = [
                m
                for m in self.moves.values()
                if Move.retrieve_id(m.id) == move_request["id"]
            ]
            assert len(matches) <= 1
            if not matches:
                continue
            move = matches[0]
            if (
                "pp" in move_request
                and self.gen not in [1, 2, 3, 4, 7, 8]
                and not is_doubles
            ):
                # exclude early gens because of unreliable Showdown event messages
                # exclude gen 7 and 8 because of Z-move and Max Move PP untrackability
                # TODO: when gen 4 issues gets fixed by PS team, 4 can be allowed again
                # exclude doubles because targets are sometimes not resolvable
                assert (
                    move_request["pp"] == move.current_pp
                ), f"{move_request['pp']} != {move.current_pp}\n{move_request}"
            if "maxpp" in move_request:
                assert (
                    move_request["maxpp"] == move.max_pp
                ), f"{move_request['maxpp']} != {move.max_pp}"
            assert move.target is not None
            if "target" in move_request:
                if move.non_ghost_target and PokemonType.GHOST not in self.types:
                    target_name = Target.SELF.name
                elif (
                    move.id == "terastarstorm"
                    and not self.fainted
                    and self.is_terastallized
                    and self.tera_type == PokemonType.STELLAR
                ):
                    target_name = Target.ALL_ADJACENT_FOES.name
                elif move.id == "pollenpuff" and Effect.HEAL_BLOCK in self.effects:
                    target_name = Target.ADJACENT_FOE.name
                else:
                    target_name = move.target.name
                assert (
                    Target.from_showdown_message(move_request["target"]).name
                    == target_name
                ), f"{Target.from_showdown_message(move_request['target']).name} != {target_name}\n{move_request}"

    def clear_active(self):
        self._active = False

    def clear_boosts(self):
        for stat in self._boosts:
            self._boosts[stat] = 0

    def _clear_effects(self):
        for effect in [e for e in self._effects]:
            self.end_effect(effect.name)

    def clear_negative_boosts(self):
        for stat, value in self._boosts.items():
            if value < 0:
                self._boosts[stat] = 0

    def clear_positive_boosts(self):
        for stat, value in self._boosts.items():
            if value > 0:
                self._boosts[stat] = 0

    def copy_boosts(self, mon: Pokemon):
        self._boosts = dict(mon._boosts.items())

    def cure_status(self, status: Optional[str] = None):
        if status and Status[status.upper()] == self._status:
            self._status = None
            self._status_counter = 0
        elif status is None and not self.fainted:
            self._status = None

    def damage(self, hp_status: str):
        self.set_hp_status(hp_status)

    def end_effect(self, effect_str: str):
        effect = Effect.from_showdown_message(effect_str)
        if effect in self._effects:
            self._effects.pop(effect)

        if effect == Effect.TYPECHANGE:
            self._temporary_types = []

        elif effect == Effect.SKILL_SWAP:
            self._temporary_ability = None

        # Because of Showdown protocols, Protosynthesis and Quark Drive
        # both get two Effects added to the mon, but only have one protocol
        # message when the Effect ends
        elif effect == Effect.QUARK_DRIVE:
            for effect in [
                Effect.QUARKDRIVEATK,
                Effect.QUARKDRIVEDEF,
                Effect.QUARKDRIVESPA,
                Effect.QUARKDRIVESPD,
                Effect.QUARKDRIVESPE,
            ]:
                if effect in self._effects:
                    self._effects.pop(effect)

        elif effect == Effect.PROTOSYNTHESIS:
            for effect in [
                Effect.PROTOSYNTHESISATK,
                Effect.PROTOSYNTHESISDEF,
                Effect.PROTOSYNTHESISSPA,
                Effect.PROTOSYNTHESISSPD,
                Effect.PROTOSYNTHESISSPE,
            ]:
                if effect in self._effects:
                    self._effects.pop(effect)

    def end_item(self, item: str):
        self._item = None

        if item == "powerherb":
            self._preparing_move = None
            self._preparing_target = False

    def end_turn(self):
        if self._status == Status.TOX:
            self._status_counter += 1
        for effect in list(self.effects.keys()):
            if effect.is_turn_countable:
                self.effects[effect] += 1
            if effect.ends_on_turn:
                self.end_effect(effect.name)

    def faint(self):
        self._current_hp = 0
        self._status = Status.FNT
        self.temporary_ability = None
        self._clear_effects()

    def forme_change(self, species: str):
        species = species.split(",")[0]
        self._update_from_pokedex(species, store_species=False)

    def identifies_as(self, ident: str) -> bool:
        return self.base_species == to_id_str(ident) or self.base_species in [
            to_id_str(substr) for substr in ident.split("-")
        ]

    def invert_boosts(self):
        self._boosts = {k: -v for k, v in self._boosts.items()}

    def mega_evolve(self, stone: str):
        species_id_str = to_id_str(self.species)
        mega_species = (
            species_id_str + "mega"
            if not species_id_str.endswith("mega")
            else species_id_str
        )
        self.temporary_ability = None
        if mega_species in GenData.from_gen(self.gen).pokedex:
            self._update_from_pokedex(mega_species, store_species=False)
        elif stone[-1] in "XYxy":
            mega_species = mega_species + stone[-1].lower()
            self._update_from_pokedex(mega_species, store_species=False)

    def moved(self, move_id: str, failed: bool = False, use: bool = True):
        self._must_recharge = False
        self._preparing_move = None
        self._preparing_target = None
        move = self._add_move(move_id, use=use)

        if move and move.is_protect_counter and not failed:
            self._protect_counter += 1
        else:
            self._protect_counter = 0

        if self._status == Status.SLP:
            self._status_counter += 1

        if len(self._moves) > 4:
            new_moves = {}

            # Keep the current move
            if move and move in self._moves.values():
                new_moves = {
                    move_id: m for move_id, m in self._moves.items() if m is move
                }

            for move_name in self._moves:
                if len(new_moves) == 4:
                    break
                elif move_name not in new_moves:
                    new_moves[move_name] = self._moves[move_name]

            self._moves = new_moves

        # Handle silent effect ending
        if Effect.GLAIVE_RUSH in self.effects:
            self.end_effect("Glaive Rush")
        elif (
            Effect.CHARGE in self.effects
            and isinstance(move, Move)
            and move.base_power > 0
            and move.type == PokemonType.ELECTRIC
            and use
        ):
            self.end_effect("Charge")
        elif (
            Effect.FLASH_FIRE in self.effects
            and isinstance(move, Move)
            and move.base_power > 0
            and move.type == PokemonType.FIRE
            and use
        ):
            self.end_effect("Flash Fire")

    def prepare(self, move_id: str, target: Optional[Pokemon]):
        self.moved(move_id, use=False)

        move_id = Move.retrieve_id(move_id)
        move = self.moves[move_id]

        self._preparing_move = move
        self._preparing_target = target

    def primal(self):
        species_id_str = to_id_str(self._species)
        primal_species = (
            species_id_str + "primal"
            if not species_id_str.endswith("primal")
            else species_id_str
        )
        self._update_from_pokedex(primal_species, store_species=False)

    def set_boost(self, stat: str, amount: int):
        assert (
            abs(amount) <= 6
        ), f"{stat} of mon {self._species} is not <= 6. Got {amount}"
        self._boosts[stat] = int(amount)

    def set_hp(self, hp_status: str):
        self.set_hp_status(hp_status)

    # Param `store` dictates whether we should store the HP as a mon's stats
    def set_hp_status(self, hp_status: str, store=False):
        if hp_status == "0 fnt":
            self.faint()
            return

        if " " in hp_status:
            hp, status = hp_status.split(" ")
            self._status = Status[status.upper()]

            # Handle silent effect ending
            if self._status == Status.SLP and Effect.YAWN in self.effects:
                self.end_effect("yawn")
        else:
            hp = hp_status
            self._status = None

        current_hp, max_hp = "".join([c for c in hp if c in "0123456789/"]).split("/")
        self._current_hp = int(current_hp)
        self._max_hp = int(max_hp)

        if store:
            self._stats["hp"] = self._max_hp

    def start_effect(self, effect_str: str, details: Optional[Any] = None):
        effect = Effect.from_showdown_message(effect_str)
        if effect not in self._effects:
            self._effects[effect] = 0
        elif effect.is_action_countable:
            self._effects[effect] += 1

        if effect.breaks_protect:
            self._protect_counter = 0

        if effect == Effect.TYPECHANGE and details is not None:
            self._temporary_types = []
            for type_ in details.split("/"):
                self._temporary_types.append(PokemonType.from_name(type_))
        elif effect == Effect.SKILL_SWAP and details:
            # Skill Swap reveals a mon's ability
            if self.ability is None:
                self.ability = details[1]
            self.temporary_ability = details[0]

    def _swap_boosts(self):
        self._boosts["atk"], self._boosts["spa"] = (
            self._boosts["spa"],
            self._boosts["atk"],
        )

    def switch_in(self, details: Optional[str] = None):
        self._active = True

        if details:
            self._update_from_details(details)

        self._first_turn = True
        self._revealed = True

    def switch_out(self, fields: Dict[Field, int]):
        if (
            self.ability == "regenerator"
            and (
                self.item == "abilityshield"
                or Field.NEUTRALIZING_GAS not in fields.keys()
            )
            and self.status != Status.FNT
        ):
            self._current_hp = min(int(self.current_hp + self.max_hp / 3), self.max_hp)

        self._active = False
        self.clear_boosts()
        self._clear_effects()
        self._first_turn = False
        self._must_recharge = False
        self._preparing_move = None
        self._preparing_target = None
        self._protect_counter = 0
        self.temporary_ability = None
        self._temporary_types = []

        if self._status == Status.TOX:
            self._status_counter = 0

    def terastallize(self, type_: str):
        self._terastallized_type = PokemonType.from_name(type_)
        self._terastallized = True
        self._temporary_types = []

    def transform(self, into: Pokemon):
        current_hp = self.current_hp
        self._update_from_pokedex(into.species, store_species=False)
        self._current_hp = int(current_hp)
        self._boosts = into.boosts.copy()

    def _update_from_pokedex(self, species: str, store_species: bool = True):
        species = to_id_str(species)
        dex_entry = GenData.from_gen(self.gen).pokedex[species]
        if store_species:
            self._species = species
        self._base_stats = dex_entry["baseStats"]

        self._type_1 = PokemonType.from_name(dex_entry["types"][0])
        if len(dex_entry["types"]) == 1:
            self._type_2 = None
        else:
            self._type_2 = PokemonType.from_name(dex_entry["types"][1])

        if "forme" in dex_entry and (
            dex_entry["forme"].startswith("Mega")
            or dex_entry["forme"] in ["Primal", "Stellar", "Terastal"]
            or dex_entry["forme"].endswith("-Tera")
        ):
            self.forme_change_ability = dex_entry["abilities"]["0"]
        elif self.forme_change_ability is None:
            self._possible_abilities = [
                to_id_str(ability) for ability in dex_entry["abilities"].values()
            ]
            if len(self._possible_abilities) == 1:
                self.ability = self._possible_abilities[0]
        else:
            self.forme_change_ability = None

        self._heightm = dex_entry["heightm"]
        self._weightkg = dex_entry["weightkg"]

    def _update_from_details(self, details: str):
        if details == self._last_details:
            return
        else:
            self._last_details = details

        if ", shiny" in details:
            self._shiny = True
            details = details.replace(", shiny", "")
        else:
            self._shiny = False

        split_details = details.split(", ")

        gender = None
        level = None

        for split_detail in split_details:
            if split_detail.startswith("tera:"):
                self._terastallized_type = PokemonType.from_name(split_detail[5:])

                split_details.remove(split_detail)
                break

        if len(split_details) == 3:
            species, level, gender = split_details
        elif len(split_details) == 2:
            if split_details[1].startswith("L"):
                species, level = split_details
            else:
                species, gender = split_details
        else:
            species = to_id_str(split_details[0])

        if gender:
            self._gender = PokemonGender.from_request_details(gender)
        else:
            self._gender = PokemonGender.NEUTRAL

        if level:
            self._level = int(level[1:])
        else:
            self._level = 100

        if species != self._species:
            self._update_from_pokedex(species)

    def update_from_request(self, request_pokemon: Dict[str, Any]):
        self._active = request_pokemon["active"]

        if request_pokemon == self._last_request:
            return

        if self.ability is None:
            self.ability = request_pokemon["baseAbility"]
        if (
            "ability" in request_pokemon
            and request_pokemon["ability"] != request_pokemon["baseAbility"]
        ):
            self.temporary_ability = request_pokemon["ability"]

        self._last_request = request_pokemon

        condition = request_pokemon["condition"]
        self.set_hp_status(condition, store=True)

        self._name = request_pokemon["ident"][4:]
        self._item = request_pokemon["item"]

        details = request_pokemon["details"]
        self._update_from_details(details)

        for move in request_pokemon["moves"]:
            self._add_move(move)

        if len(self._moves) > 4:
            moves_to_keep = {
                Move.retrieve_id(move_id) for move_id in request_pokemon["moves"]
            }
            self._moves = {
                move_id: move
                for move_id, move in self._moves.items()
                if move_id in moves_to_keep
            }

        if "stats" in request_pokemon:
            for stat in request_pokemon["stats"]:
                self._stats[stat] = request_pokemon["stats"][stat]

    def _update_from_teambuilder(self, tb: TeambuilderPokemon):
        if tb.nickname is not None and tb.species is None:
            self._update_from_pokedex(tb.nickname)
        elif tb.nickname is not None and tb.species is not None:
            self._update_from_pokedex(tb.species)
            self._name = tb.nickname
        elif tb.nickname is None and tb.species is not None:
            self._update_from_pokedex(tb.species)
        else:
            raise ValueError(
                "TeambuilderPokemon must have either a nickname or species", tb
            )

        if tb.level:
            self._level = tb.level
        self._ability = to_id_str(tb.ability)
        self._item = to_id_str(tb.item) if tb.item else None
        if tb.gender:
            self._gender = PokemonGender.from_request_details(tb.gender)
        self._shiny = tb.shiny
        if tb.tera_type:
            self._terastallized_type = PokemonType.from_name(tb.tera_type)
        self._moves = {}
        for move_str in tb.moves:
            move = Move(Move.retrieve_id(move_str), gen=self.gen)
            self._moves[move.id] = move

        if tb.level:
            nature = tb.nature.lower() if tb.nature else "serious"
            self._stats = {}
            stats = compute_raw_stats(
                self._species,
                tb.evs,
                tb.ivs,
                tb.level,
                nature,
                GenData.from_gen(self.gen),
            )
            for stat, val in zip(["hp", "atk", "def", "spa", "spd", "spe"], stats):
                self._stats[stat] = val

    def was_illusioned(self, fields: Dict[Field, int]):
        self._current_hp = None
        self._max_hp = None
        self._status = None

        last_request = self._last_request
        self._last_request = None

        if last_request:
            self.update_from_request(last_request)

        self.switch_out(fields)

    def available_moves_from_request(self, request: Dict[str, Any]) -> List[Move]:
        moves: List[Move] = []

        request_moves: List[str] = [
            move["id"] for move in request["moves"] if not move.get("disabled", False)
        ]
        for move in request_moves:
            if move in self.moves:
                if self.is_dynamaxed:
                    moves.append(self.moves[move].dynamaxed)
                else:
                    moves.append(self.moves[move])
            elif move in SPECIAL_MOVES:
                moves.append(Move(move, gen=self.gen))
            elif (
                move == "hiddenpower"
                and len([m for m in self.moves if m.startswith("hiddenpower")]) == 1
            ):
                moves.append(
                    [v for m, v in self.moves.items() if m.startswith("hiddenpower")][0]
                )
            else:
                has_copy_move = {
                    "copycat",
                    "metronome",
                    "mefirst",
                    "mirrormove",
                    "assist",
                    "transform",
                    "mimic",
                }.intersection(self.moves)

                """
                Check if the pokemon has abilities that can grant moves

                Some abilities (like Dancer, which can be copied via Trace) allow using
                moves that aren't in the pokemon's moveset
                """
                has_move_granting_ability = (
                    self.ability in ("dancer", "trace") if self.ability else False
                )

                if not has_copy_move and not has_move_granting_ability:
                    assert False, (
                        f"Error with move {move}. Expected self.moves to contain copycat, "
                        "metronome, mefirst, mirrormove, assist, transform, mimic, "
                        f"or the pokemon to have a move-granting ability. Got moves: {self.moves}, "
                        f"ability: {self.ability}"
                    )
                moves.append(Move(move, gen=self.gen))
        return moves

    def damage_multiplier(self, type_or_move: Union[PokemonType, Move]) -> float:
        """
        Returns the damage multiplier associated with a given type or move on this
        pokemon.

        This method is a shortcut for PokemonType.damage_multiplier with relevant types.

        :param type_or_move: The type or move of interest.
        :type type_or_move: PokemonType or Move
        :return: The damage multiplier associated with given type on the pokemon.
        :rtype: float
        """
        if isinstance(type_or_move, Move):
            type_or_move = type_or_move.type
        return type_or_move.damage_multiplier(
            self.type_1, self.type_2, type_chart=GenData.from_gen(self.gen).type_chart
        )

    @property
    def ability(self) -> Optional[str]:
        """
        :return: The pokemon's ability. None if unknown or removed.
        :rtype: str, optional
        """
        if self.temporary_ability is not None:
            return self.temporary_ability
        elif self.forme_change_ability is not None:
            return self.forme_change_ability
        else:
            return self._ability

    @ability.setter
    def ability(self, ability: str):
        if self.ability == to_id_str(ability):
            return
        elif self._ability is None:
            self._ability = to_id_str(ability)
        else:
            self._temporary_ability = to_id_str(ability)

    @property
    def active(self) -> Optional[bool]:
        """
        :return: Boolean indicating whether the pokemon is active.
        :rtype: bool
        """
        return self._active

    @active.setter
    def active(self, value: Optional[bool]):
        self.active = value

    @property
    def available_z_moves(self) -> List[Move]:
        """
        Caution: this property is not properly tested yet.

        :return: The set of moves that pokemon can use as z-moves.
        :rtype: List[Move]
        """
        if isinstance(self.item, str) and self.item.endswith("iumz"):
            type_, move = Z_CRYSTAL[self.item]
            if type_:
                return [
                    move
                    for move in self._moves.values()
                    if move.type == type_ and move.can_z_move
                ]
            elif move in self._moves:
                return [self._moves[move]]
        return []

    @property
    def base_ability(self) -> Optional[str]:
        """
        :return: The pokemon's base ability. None if unknown.
        :rtype: str, optional
        """
        return self._forme_change_ability or self._ability

    @property
    def base_species(self) -> str:
        """
        :return: The pokemon's base species.
        :rtype: str
        """
        dex_entry = GenData.from_gen(self.gen).pokedex[self._species]
        return to_id_str(dex_entry["baseSpecies"])

    @property
    def base_stats(self) -> Dict[str, int]:
        """
        :return: The pokemon's base stats.
        :rtype: Dict[str, int]
        """
        return self._base_stats

    @property
    def boosts(self) -> Dict[str, int]:
        """
        :return: The pokemon's boosts.
        :rtype: Dict[str, int]
        """
        return self._boosts

    @boosts.setter
    def boosts(self, value: Dict[str, int]):
        self._boosts = value

    @property
    def current_hp(self) -> int:
        """
        :return: The pokemon's current hp. For your pokemons, this is the actual value.
            For opponent's pokemon, this value depends on showdown information: it can
            be on a scale from 0 to 100 or on a pixel scale.
        :rtype: int
        """
        return self._current_hp or 0

    @property
    def current_hp_fraction(self) -> float:
        """
        :return: The pokemon's current remaining hp fraction.
        :rtype: float
        """
        if self.current_hp:
            return self.current_hp / self.max_hp
        return 0

    @property
    def effects(self) -> Dict[Effect, int]:
        """
        :return: A Dict mapping the effects currently affecting the pokemon and the
            associated counter.
        :rtype: Dict[Effect, int]
        """
        return self._effects

    @property
    def fainted(self) -> bool:
        """
        :return: Whether the pokemon has fainted.
        :rtype: bool
        """
        return Status.FNT == self._status

    @property
    def first_turn(self) -> bool:
        """
        :return: Whether this is this pokemon's first action since its last switch in.
        :rtype: bool
        """
        return self._first_turn

    @property
    def gen(self) -> int:
        """
        :return: The generation of the pokemon.
        :rtype: int
        """
        return self._gen

    @property
    def gender(self) -> Optional[PokemonGender]:
        """
        :return: The pokemon's gender.
        :rtype: PokemonGender, optional
        """
        return self._gender

    @property
    def height(self) -> float:
        """
        :return: The pokemon's height, in meters.
        :rtype: float
        """
        return self._heightm

    @property
    def hp_status(self) -> str:
        if self.status == Status.FNT:
            s = "0 fnt"
        else:
            s = f"{self.current_hp}/{self.max_hp}"
            if self.status is not None:
                s += f" {self.status.name.lower()}"
        return s

    def identifier(self, player_role: str) -> str:
        """ "
        :param player_role: The player's role in the battle (p1 or p2)
        :type player_role: str
        :return: The pokemon's identifier, which can be used to identify it in Showdown logs
        """
        assert player_role in ["p1", "p2"]
        return player_role + ": " + self.name

    @property
    def is_dynamaxed(self) -> bool:
        """
        :return: Whether the pokemon is currently dynamaxed
        :rtype: bool
        """
        return Effect.DYNAMAX in self.effects

    @property
    def is_terastallized(self) -> bool:
        """
        :return: Whether the pokemon is currently terastallized
        :rtype: bool
        """
        return self._terastallized

    @property
    def item(self) -> Optional[str]:
        """
        :return: The pokemon's item.
        :rtype: str | None
        """
        return self._item

    @item.setter
    def item(self, item: Optional[str]):
        self._item = to_id_str(item) if item is not None else None

    @property
    def level(self) -> int:
        """
        :return: The pokemon's level.
        :rtype: int
        """
        return self._level

    @property
    def max_hp(self) -> int:
        """
        :return: The pokemon's max hp. For your pokemons, this is the actual value.
            For opponent's pokemon, this value depends on showdown information: it can
            be on a scale from 0 to 100 or on a pixel scale.
        :rtype: int
        """
        return self._max_hp or 0

    @property
    def forme_change_ability(self) -> Optional[str]:
        """
        :return: The pokemon's ability after changing forme. None if the pokemon hasn't changed forme.
        :rtype: str, optional
        """
        return self._forme_change_ability

    @forme_change_ability.setter
    def forme_change_ability(self, ability: Optional[str]):
        self._forme_change_ability = to_id_str(ability) if ability is not None else None

    @property
    def moves(self) -> Dict[str, Move]:
        """
        :return: A dictionary of the pokemon's known moves.
        :rtype: Dict[str, Move]
        """
        return self._moves

    @property
    def must_recharge(self) -> bool:
        """
        :return: A boolean indicating whether the pokemon must recharge.
        :rtype: bool
        """
        return self._must_recharge

    @must_recharge.setter
    def must_recharge(self, value: bool):
        self._must_recharge = value

    @property
    def name(self) -> str:
        """
        :return: The pokemon's name, which can be used to create Showdown's
            identifier.
        :rtype: str
        """
        if self._name is not None:
            return self._name
        else:
            dex_entry = GenData.from_gen(self.gen).pokedex[self._species]
            if dex_entry["baseSpecies"].islower():
                return dex_entry["name"]
            else:
                return dex_entry["baseSpecies"]

    @property
    def original_types(self) -> List[PokemonType]:
        if self._type_2 is None:
            return [self._type_1]
        else:
            return [self._type_1, self._type_2]

    @property
    def pokeball(self) -> Optional[str]:
        """
        :return: The pokeball in which is the pokemon.
        :rtype: str | None
        """
        if self._last_request is not None:
            return self._last_request.get("pokeball", None)
        return None

    @property
    def possible_abilities(self) -> List[str]:
        """
        :return: The list of possible abilities for this pokemon.
        :rtype: List[str]
        """
        return self._possible_abilities

    @property
    def preparing(self) -> bool:
        """
        :return: Whether this pokemon is preparing a multi-turn move.
        :rtype: bool
        """
        return bool(self._preparing_target) or bool(self._preparing_move)

    @property
    def preparing_target(self) -> Optional[Union[bool, Pokemon]]:
        """
        :return: The moves target - optional.
        :rtype: Any
        """
        return self._preparing_target

    @property
    def preparing_move(self) -> Optional[Move]:
        """
        :return: The move being prepared - optional.
        :rtype: Move, optional
        """
        return self._preparing_move

    @property
    def protect_counter(self) -> int:
        """
        :return: How many protect-like moves where used in a row by this pokemon.
        :rtype: int
        """
        return self._protect_counter

    @property
    def revealed(self) -> bool:
        """
        :return: Whether this pokemon has appeared in the current battle.
        :rtype: bool
        """
        return self._revealed

    @property
    def shiny(self) -> bool:
        """
        :return: Whether this pokemon is shiny.
        :rtype: bool
        """
        return bool(self._shiny)

    @property
    def species(self) -> str:
        """
        :return: The pokemon's species.
        :rtype: str | None
        """
        return self._species

    @property
    def stats(self) -> Dict[str, Optional[int]]:
        """
        :return: The pokemon's stats, as a dictionary.
        :rtype: Dict[str, int | None]
        """
        return self._stats

    @stats.setter
    def stats(self, stats: Dict[str, Optional[int]]):
        self._stats = stats

    @property
    def status(self) -> Optional[Status]:
        """
        :return: The pokemon's status.
        :rtype: Optional[Status]
        """
        return self._status

    @status.setter
    def status(self, status: Optional[Union[Status, str]]):
        self._status = Status[status.upper()] if isinstance(status, str) else status

    @property
    def status_counter(self) -> int:
        """
        :return: The pokemon's status turn count. Only counts TOXIC and SLEEP statuses.
        :rtype: int
        """
        return self._status_counter

    @property
    def stab_multiplier(self) -> float:
        """
        :return: The pokemon's STAB multiplier.
        :rtype: float
        """
        # https://bulbapedia.bulbagarden.net/wiki/Terastal_phenomenon#Effects
        if (
            self._terastallized
            and (
                self.tera_type in (self._type_1, self._type_2)
                or self.tera_type in self._temporary_types
            )
            and self.ability == "adaptability"
        ):
            return 2.25
        elif self._terastallized and (
            self.tera_type in (self._type_1, self._type_2)
            or self.tera_type in self._temporary_types
        ):
            return 2
        elif self.ability == "adaptability":
            return 2
        return 1.5

    @property
    def selected_in_teampreview(self) -> bool:
        """
        :return: Whether this pokemon was selected in teampreview.
        :rtype: bool
        """
        return self._selected_in_teampreview

    @property
    def temporary_ability(self) -> str | None:
        """
        :return: The pokemon's temporary ability, None if none is set.
        :rtype: Optional[str]
        """
        return self._temporary_ability

    @temporary_ability.setter
    def temporary_ability(self, ability: str | None):
        self._temporary_ability = to_id_str(ability) if ability is not None else None

    @property
    def tera_type(self) -> Optional[PokemonType]:
        """
        :return: The Tera Type of the Pokemon, None if unnown
        :rtype: Optional[PokemonType]
        """
        return self._terastallized_type

    @property
    def type_1(self) -> PokemonType:
        """
        :return: The pokemon's first type.
        :rtype: PokemonType
        """
        if self._terastallized and self._terastallized_type is not None:
            return self._terastallized_type
        elif len(self._temporary_types) > 0:
            return self._temporary_types[0]
        return self._type_1

    @property
    def type_2(self) -> Optional[PokemonType]:
        """
        :return: The pokemon's second type.
        :rtype: Optional[PokemonType]
        """
        if self._terastallized or len(self._temporary_types) == 1:
            return None
        elif len(self._temporary_types) > 1:
            return self._temporary_types[1]
        return self._type_2

    @property
    def types(self) -> List[PokemonType]:
        """
        :return: The pokemon's types. Not a Tuple because moves can add types
            and also remove types, and override them too.
        :rtype: Tuple[PokemonType]
        """
        if len(self._temporary_types) > 0:
            return self._temporary_types
        else:
            types = [self.type_1]
            if self.type_2 is not None:
                types.append(self.type_2)
            return types

    @property
    def weight(self) -> float:
        """
        :return: The pokemon's weight, in kilograms.
        :rtype: float
        """
        return self._weightkg
