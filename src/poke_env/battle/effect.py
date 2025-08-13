"""This module defines the Effect class, which represents in-game effects."""

from __future__ import annotations

import logging
from enum import Enum, auto, unique
from typing import Dict, Set


@unique
class Effect(Enum):
    """Enumeration, represent an effect a Pokemon can be affected by."""

    UNKNOWN = auto()
    AFTER_YOU = auto()
    AFTERMATH = auto()
    AQUA_RING = auto()
    AROMATHERAPY = auto()
    AROMA_VEIL = auto()
    ATTRACT = auto()
    AUTOTOMIZE = auto()
    BAD_DREAMS = auto()
    BANEFUL_BUNKER = auto()
    BATTLE_BOND = auto()
    BEAK_BLAST = auto()
    BIDE = auto()
    BIND = auto()
    BURNING_BULWARK = auto()
    BURN_UP = auto()
    CELEBRATE = auto()
    CHARGE = auto()
    CLAMP = auto()
    COMMANDER = auto()
    CONFUSION = auto()
    COURT_CHANGE = auto()
    CRAFTY_SHIELD = auto()
    CUD_CHEW = auto()
    CURSE = auto()
    CUSTAP_BERRY = auto()
    DANCER = auto()
    DEFENSE_CURL = auto()
    DESTINY_BOND = auto()
    DISABLE = auto()
    DISGUISE = auto()
    DOOM_DESIRE = auto()
    DRAGON_CHEER = auto()
    DYNAMAX = auto()
    EERIE_SPELL = auto()
    ELECTRIC_TERRAIN = auto()
    ELECTRIFY = auto()
    EMBARGO = auto()
    EMERGENCY_EXIT = auto()
    ENCORE = auto()
    ENDURE = auto()
    FALLEN = auto()
    FALLEN1 = auto()
    FALLEN2 = auto()
    FALLEN3 = auto()
    FALLEN4 = auto()
    FALLEN5 = auto()
    FAIRY_LOCK = auto()
    FEINT = auto()
    FICKLE_BEAM = auto()
    FIRE_SPIN = auto()
    FLASH_FIRE = auto()
    FLINCH = auto()
    FLOWER_VEIL = auto()
    FOCUS_BAND = auto()
    FOCUS_ENERGY = auto()
    FOCUS_PUNCH = auto()
    FOLLOW_ME = auto()
    FORESIGHT = auto()
    FOREWARN = auto()
    FUTURE_SIGHT = auto()
    GASTRO_ACID = auto()
    GLAIVE_RUSH = auto()
    GRAVITY = auto()
    GRUDGE = auto()
    GUARD_DOG = auto()
    GUARD_SPLIT = auto()
    GULP_MISSILE = auto()
    G_MAX_CENTIFERNO = auto()
    G_MAX_CHI_STRIKE = auto()
    G_MAX_ONE_BLOW = auto()
    G_MAX_RAPID_FLOW = auto()
    G_MAX_SANDBLAST = auto()
    HADRON_ENGINE = auto()
    HEAL_BELL = auto()
    HEAL_BLOCK = auto()
    HEALER = auto()
    HELPING_HAND = auto()
    HYDRATION = auto()
    HYPERSPACE_FURY = auto()
    HYPERSPACE_HOLE = auto()
    ICE_FACE = auto()
    ILLUSION = auto()
    IMMUNITY = auto()
    IMPRISON = auto()
    INFESTATION = auto()
    INGRAIN = auto()
    INNARDS_OUT = auto()
    INSOMNIA = auto()
    INSTRUCT = auto()
    IRON_BARBS = auto()
    KINGS_SHIELD = auto()
    LASER_FOCUS = auto()
    LEECH_SEED = auto()
    LEPPA_BERRY = auto()
    LIGHTNING_ROD = auto()
    LIMBER = auto()
    LINGERING_AROMA = auto()
    LIQUID_OOZE = auto()
    LOCKED_MOVE = auto()
    LOCK_ON = auto()
    MAGIC_COAT = auto()
    MAGMA_STORM = auto()
    MAGNET_RISE = auto()
    MAGNITUDE = auto()
    MAT_BLOCK = auto()
    MAX_GUARD = auto()
    MIMIC = auto()
    MIMICRY = auto()
    MIND_READER = auto()
    MINIMIZE = auto()
    MIRACLE_EYE = auto()
    MIST = auto()
    MISTY_TERRAIN = auto()
    MUMMY = auto()
    MUST_RECHARGE = auto()
    NIGHTMARE = auto()
    NO_RETREAT = auto()
    OBLIVIOUS = auto()
    OBSTRUCT = auto()
    OCTOLOCK = auto()
    ORICHALCUM_PULSE = auto()
    OWN_TEMPO = auto()
    PARTIALLY_TRAPPED = auto()
    PASTEL_VEIL = auto()
    PERISH0 = auto()
    PERISH1 = auto()
    PERISH2 = auto()
    PERISH3 = auto()
    PHANTOM_FORCE = auto()
    POLTERGEIST = auto()
    POWDER = auto()
    POWER_CONSTRUCT = auto()
    POWER_SHIFT = auto()
    POWER_SPLIT = auto()
    POWER_TRICK = auto()
    PROTECT = auto()
    PROTECTIVE_PADS = auto()
    PROTOSYNTHESIS = auto()
    PROTOSYNTHESISATK = auto()
    PROTOSYNTHESISDEF = auto()
    PROTOSYNTHESISSPA = auto()
    PROTOSYNTHESISSPD = auto()
    PROTOSYNTHESISSPE = auto()
    PSYCHIC_TERRAIN = auto()
    PURSUIT = auto()
    QUARK_DRIVE = auto()
    QUARKDRIVEATK = auto()
    QUARKDRIVEDEF = auto()
    QUARKDRIVESPA = auto()
    QUARKDRIVESPD = auto()
    QUARKDRIVESPE = auto()
    QUASH = auto()
    QUICK_CLAW = auto()
    QUICK_DRAW = auto()
    QUICK_GUARD = auto()
    RAGE = auto()
    RAGE_POWDER = auto()
    REFLECT = auto()
    RIPEN = auto()
    ROOST = auto()
    ROUGH_SKIN = auto()
    SAFEGUARD = auto()
    SAFETY_GOGGLES = auto()
    SALT_CURE = auto()
    SAND_TOMB = auto()
    SCREEN_CLEANER = auto()
    SHADOW_FORCE = auto()
    SHED_SKIN = auto()
    SILK_TRAP = auto()
    SKETCH = auto()
    SKILL_SWAP = auto()
    SKY_DROP = auto()
    SLOW_START = auto()
    SMACK_DOWN = auto()
    SNAP_TRAP = auto()
    SNATCH = auto()
    SPARKLING_ARIA = auto()
    SPEED_SWAP = auto()
    SPIKY_SHIELD = auto()
    SPITE = auto()
    SPOTLIGHT = auto()
    STICKY_HOLD = auto()
    STICKY_WEB = auto()
    STOCKPILE = auto()
    STOCKPILE1 = auto()
    STOCKPILE2 = auto()
    STOCKPILE3 = auto()
    STORM_DRAIN = auto()
    STRUGGLE = auto()
    SUBSTITUTE = auto()
    SUCTION_CUPS = auto()
    SUPREME_OVERLORD = auto()
    SYRUP_BOMB = auto()
    SWEET_VEIL = auto()
    SYMBIOSIS = auto()
    SYNCHRONIZE = auto()
    TAR_SHOT = auto()
    TAUNT = auto()
    TELEKINESIS = auto()
    TELEPATHY = auto()
    TERA_SHELL = auto()
    TERA_SHIFT = auto()
    TIDY_UP = auto()
    TOXIC_DEBRIS = auto()
    THERMAL_EXCHANGE = auto()
    THROAT_CHOP = auto()
    THUNDER_CAGE = auto()
    TORMENT = auto()
    TRAPPED = auto()
    TRICK = auto()
    TYPEADD = auto()
    TYPECHANGE = auto()
    UPROAR = auto()
    VITAL_SPIRIT = auto()
    WANDERING_SPIRIT = auto()
    WATER_BUBBLE = auto()
    WATER_VEIL = auto()
    WHIRLPOOL = auto()
    WIDE_GUARD = auto()
    WIMP_OUT = auto()
    WRAP = auto()
    YAWN = auto()
    ZERO_TO_HERO = auto()

    def __str__(self) -> str:
        return f"{self.name} (effect) object"

    @staticmethod
    def from_showdown_message(message: str) -> Effect:
        """Returns the Effect object corresponding to the message.

        :param message: The message to convert.
        :type message: str
        :return: The corresponding Effect object.
        :rtype: Effect
        """
        message = message.replace("item: ", "")
        message = message.replace("move: ", "")
        message = message.replace("ability: ", "")
        message = message.replace(" ", "_")
        message = message.replace("-", "_")
        message = message.upper()

        if message == "FALLENUNDEFINED":
            message = "FALLEN"

        try:
            return Effect[message]
        except KeyError:
            logging.getLogger("poke-env").warning(
                "Unexpected effect '%s' received. Effect.UNKNOWN will be used instead. "
                "If this is unexpected, please open an issue at "
                "https://github.com/hsahovic/poke-env/issues/ along with this error "
                "message and a description of your program.",
                message,
            )
            return Effect.UNKNOWN

    @staticmethod
    def from_data(message: str) -> Effect:
        """Returns the Effect object corresponding to the string in static data.

        :param message: The message to convert.
        :type message: str
        :return: The corresponding Effect object.
        :rtype: Effect
        """
        message = message.replace("_", "")
        message = message.replace(" ", "")
        message = message.replace("-", "")
        message = message.upper()
        try:
            return _FROM_DATA[message]
        except KeyError:
            logging.getLogger("poke-env").warning(
                "Unexpected effect '%s' received. Effect.UNKNOWN will be used instead. "
                "If this is unexpected, please open an issue at "
                "https://github.com/hsahovic/poke-env/issues/ along with this error "
                "message and a description of your program.",
                message,
            )
            return Effect.UNKNOWN

    @property
    def breaks_protect(self):
        """
        :return: Whether this effect breaks protect-like states.
        :rtype: bool
        """
        return self in _PROTECT_BREAKING_EFFECTS

    @property
    def ends_on_move(self) -> bool:
        """
        :return: Whether this effect ends when a pokemon moves.
        :rtype: bool
        """
        return self in _ENDS_ON_MOVE_EFFECTS

    @property
    def ends_on_switch(self) -> bool:
        """
        :return: Whether this effect ends when the pokemon switches out.
        :rtype: bool
        """
        return self.is_volatile_status or self in _ENDS_ON_SWITCH_EFFECTS

    @property
    def ends_on_turn(self) -> bool:
        """
        :return: Whether this effect ends at the end of the turn.
        :rtype: bool
        """
        return self in _ENDS_ON_TURN_EFFECTS

    @property
    def is_turn_countable(self) -> bool:
        """
        :return: Whether it is useful to keep track of the number of turns this effect
            has been active for.
        :rtype: bool
        """
        return self in _TURN_COUNTER_EFFECTS

    @property
    def is_action_countable(self) -> bool:
        """
        :return: Whether it is useful to keep track of the number of times this effect
            has been activated.
        :rtype: bool
        """
        return self in _ACTION_COUNTER_EFFECTS

    @property
    def is_volatile_status(self) -> bool:
        """
        :return: Whether the effect is a volatile status, brought by a move
        :rtype: bool
        """
        return self in _VOLATILE_STATUS_EFFECTS

    @property
    def is_from_ability(self) -> bool:
        """
        :return: Whether this effect is a result of an ability
        :rtype: bool
        """
        return self in _FROM_ABILITY_EFFECTS

    @property
    def is_from_item(self) -> bool:
        """
        :return: Whether this effect is a result of an item
        :rtype: bool
        """
        return self in _FROM_ITEM_EFFECTS

    @property
    def is_from_move(self) -> bool:
        """
        :return: Whether this effect is a result of a move
        :rtype: bool
        """
        return self in _FROM_MOVE_EFFECTS


_FROM_ABILITY_EFFECTS: Set[Effect] = {
    Effect.AFTERMATH,
    Effect.AROMA_VEIL,
    Effect.BAD_DREAMS,
    Effect.BATTLE_BOND,
    Effect.COMMANDER,
    Effect.CUD_CHEW,
    Effect.DANCER,
    Effect.DISGUISE,
    Effect.EMERGENCY_EXIT,
    Effect.FLASH_FIRE,
    Effect.FLOWER_VEIL,
    Effect.FOREWARN,
    Effect.GUARD_DOG,
    Effect.GULP_MISSILE,
    Effect.HADRON_ENGINE,
    Effect.HEALER,
    Effect.HYDRATION,
    Effect.ICE_FACE,
    Effect.ILLUSION,
    Effect.IMMUNITY,
    Effect.INNARDS_OUT,
    Effect.IRON_BARBS,
    Effect.LIGHTNING_ROD,
    Effect.LIMBER,
    Effect.LINGERING_AROMA,
    Effect.LIQUID_OOZE,
    Effect.MIMICRY,
    Effect.MUMMY,
    Effect.OBLIVIOUS,
    Effect.ORICHALCUM_PULSE,
    Effect.OWN_TEMPO,
    Effect.PASTEL_VEIL,
    Effect.POWER_CONSTRUCT,
    Effect.PROTECTIVE_PADS,
    Effect.PROTOSYNTHESIS,
    Effect.PROTOSYNTHESISATK,
    Effect.PROTOSYNTHESISDEF,
    Effect.PROTOSYNTHESISSPA,
    Effect.PROTOSYNTHESISSPD,
    Effect.PROTOSYNTHESISSPE,
    Effect.QUARK_DRIVE,
    Effect.QUARKDRIVEATK,
    Effect.QUARKDRIVEDEF,
    Effect.QUARKDRIVESPA,
    Effect.QUARKDRIVESPD,
    Effect.QUARKDRIVESPE,
    Effect.QUICK_DRAW,
    Effect.RIPEN,
    Effect.ROUGH_SKIN,
    Effect.SCREEN_CLEANER,
    Effect.SHED_SKIN,
    Effect.SLOW_START,
    Effect.STICKY_HOLD,
    Effect.STORM_DRAIN,
    Effect.SUCTION_CUPS,
    Effect.SUPREME_OVERLORD,
    Effect.SWEET_VEIL,
    Effect.SYMBIOSIS,
    Effect.SYNCHRONIZE,
    Effect.TELEPATHY,
    Effect.TERA_SHELL,
    Effect.TERA_SHIFT,
    Effect.TOXIC_DEBRIS,
    Effect.THERMAL_EXCHANGE,
    Effect.TRAPPED,
    Effect.VITAL_SPIRIT,
    Effect.WANDERING_SPIRIT,
    Effect.WATER_BUBBLE,
    Effect.WATER_VEIL,
    Effect.WIMP_OUT,
    Effect.ZERO_TO_HERO,
}

_FROM_ITEM_EFFECTS: Set[Effect] = {
    Effect.CUSTAP_BERRY,
    Effect.FOCUS_BAND,
    Effect.HEAL_BELL,
    Effect.LEPPA_BERRY,
    Effect.PROTOSYNTHESISATK,
    Effect.PROTOSYNTHESISDEF,
    Effect.PROTOSYNTHESISSPA,
    Effect.PROTOSYNTHESISSPD,
    Effect.PROTOSYNTHESISSPE,
    Effect.QUARKDRIVEATK,
    Effect.QUARKDRIVEDEF,
    Effect.QUARKDRIVESPA,
    Effect.QUARKDRIVESPD,
    Effect.QUARKDRIVESPE,
    Effect.QUICK_CLAW,
    Effect.SAFETY_GOGGLES,
}

_FROM_MOVE_EFFECTS: Set[Effect] = {
    Effect.AFTER_YOU,
    Effect.AQUA_RING,
    Effect.AROMATHERAPY,
    Effect.ATTRACT,
    Effect.AUTOTOMIZE,
    Effect.BANEFUL_BUNKER,
    Effect.BEAK_BLAST,
    Effect.BIDE,
    Effect.BIND,
    Effect.BURNING_BULWARK,
    Effect.BURN_UP,
    Effect.CELEBRATE,
    Effect.CHARGE,
    Effect.CLAMP,
    Effect.CONFUSION,
    Effect.COURT_CHANGE,
    Effect.CRAFTY_SHIELD,
    Effect.CURSE,
    Effect.DEFENSE_CURL,
    Effect.DESTINY_BOND,
    Effect.DISABLE,
    Effect.DOOM_DESIRE,
    Effect.DRAGON_CHEER,
    Effect.EERIE_SPELL,
    Effect.ELECTRIC_TERRAIN,
    Effect.ELECTRIFY,
    Effect.EMBARGO,
    Effect.ENCORE,
    Effect.ENDURE,
    Effect.FAIRY_LOCK,
    Effect.FEINT,
    Effect.FICKLE_BEAM,
    Effect.FIRE_SPIN,
    Effect.FLINCH,
    Effect.FOCUS_ENERGY,
    Effect.FOCUS_PUNCH,
    Effect.FOLLOW_ME,
    Effect.FORESIGHT,
    Effect.FUTURE_SIGHT,
    Effect.GASTRO_ACID,
    Effect.GLAIVE_RUSH,
    Effect.GRAVITY,
    Effect.GRUDGE,
    Effect.GUARD_SPLIT,
    Effect.G_MAX_CENTIFERNO,
    Effect.G_MAX_CHI_STRIKE,
    Effect.G_MAX_ONE_BLOW,
    Effect.G_MAX_RAPID_FLOW,
    Effect.G_MAX_SANDBLAST,
    Effect.HELPING_HAND,
    Effect.HYPERSPACE_FURY,
    Effect.HYPERSPACE_HOLE,
    Effect.IMPRISON,
    Effect.INFESTATION,
    Effect.INGRAIN,
    Effect.INSOMNIA,
    Effect.INSTRUCT,
    Effect.KINGS_SHIELD,
    Effect.LASER_FOCUS,
    Effect.LEECH_SEED,
    Effect.LOCKED_MOVE,
    Effect.LOCK_ON,
    Effect.MAGIC_COAT,
    Effect.MAGMA_STORM,
    Effect.MAGNET_RISE,
    Effect.MAGNITUDE,
    Effect.MAT_BLOCK,
    Effect.MAX_GUARD,
    Effect.MIMIC,
    Effect.MIND_READER,
    Effect.MINIMIZE,
    Effect.MIRACLE_EYE,
    Effect.MIST,
    Effect.MISTY_TERRAIN,
    Effect.MUST_RECHARGE,
    Effect.NIGHTMARE,
    Effect.NO_RETREAT,
    Effect.OBSTRUCT,
    Effect.OCTOLOCK,
    Effect.PARTIALLY_TRAPPED,
    Effect.PERISH0,
    Effect.PERISH1,
    Effect.PERISH2,
    Effect.PERISH3,
    Effect.PHANTOM_FORCE,
    Effect.POLTERGEIST,
    Effect.POWDER,
    Effect.POWER_SHIFT,
    Effect.POWER_SPLIT,
    Effect.POWER_TRICK,
    Effect.PROTECT,
    Effect.PSYCHIC_TERRAIN,
    Effect.PURSUIT,
    Effect.QUASH,
    Effect.QUICK_GUARD,
    Effect.RAGE,
    Effect.RAGE_POWDER,
    Effect.REFLECT,
    Effect.ROOST,
    Effect.SAFEGUARD,
    Effect.SALT_CURE,
    Effect.SAND_TOMB,
    Effect.SHADOW_FORCE,
    Effect.SILK_TRAP,
    Effect.SKETCH,
    Effect.SKILL_SWAP,
    Effect.SKY_DROP,
    Effect.SMACK_DOWN,
    Effect.SNAP_TRAP,
    Effect.SNATCH,
    Effect.SPARKLING_ARIA,
    Effect.SPEED_SWAP,
    Effect.SPIKY_SHIELD,
    Effect.SPITE,
    Effect.SPOTLIGHT,
    Effect.STICKY_WEB,
    Effect.STOCKPILE,
    Effect.STOCKPILE1,
    Effect.STOCKPILE2,
    Effect.STOCKPILE3,
    Effect.STRUGGLE,
    Effect.SUBSTITUTE,
    Effect.SYRUP_BOMB,
    Effect.TAR_SHOT,
    Effect.TAUNT,
    Effect.TELEKINESIS,
    Effect.TIDY_UP,
    Effect.THROAT_CHOP,
    Effect.THUNDER_CAGE,
    Effect.TRAPPED,
    Effect.TRICK,
    Effect.TYPEADD,
    Effect.TYPECHANGE,
    Effect.UPROAR,
    Effect.WHIRLPOOL,
    Effect.WIDE_GUARD,
    Effect.WRAP,
    Effect.YAWN,
}

_VOLATILE_STATUS_EFFECTS: Set[Effect] = {
    Effect.FORESIGHT,
    Effect.DISABLE,
    Effect.SMACK_DOWN,
    Effect.CURSE,
    Effect.NIGHTMARE,
    Effect.TAR_SHOT,
    Effect.LOCKED_MOVE,
    Effect.BIDE,
    Effect.SNATCH,
    Effect.ENCORE,
    Effect.SPOTLIGHT,
    Effect.LASER_FOCUS,
    Effect.ELECTRIFY,
    Effect.SILK_TRAP,
    Effect.HEAL_BLOCK,
    Effect.MIRACLE_EYE,
    Effect.ATTRACT,
    Effect.DESTINY_BOND,
    Effect.RAGE,
    Effect.AQUA_RING,
    Effect.TAUNT,
    Effect.TELEKINESIS,
    Effect.GRUDGE,
    Effect.SYRUP_BOMB,
    Effect.YAWN,
    Effect.IMPRISON,
    Effect.MAGIC_COAT,
    Effect.STOCKPILE,
    Effect.DEFENSE_CURL,
    Effect.EMBARGO,
    Effect.FOLLOW_ME,
    Effect.GLAIVE_RUSH,
    Effect.CONFUSION,
    Effect.INGRAIN,
    Effect.BANEFUL_BUNKER,
    Effect.PROTECT,
    Effect.GASTRO_ACID,
    Effect.POWER_TRICK,
    Effect.TORMENT,
    Effect.BURNING_BULWARK,
    Effect.DRAGON_CHEER,
    Effect.SPARKLING_ARIA,
    Effect.HELPING_HAND,
    Effect.FLINCH,
    Effect.OCTOLOCK,
    Effect.PARTIALLY_TRAPPED,
    Effect.KINGS_SHIELD,
    Effect.MINIMIZE,
    Effect.NO_RETREAT,
    Effect.CHARGE,
    Effect.MUST_RECHARGE,
    Effect.MAGNET_RISE,
    Effect.MAX_GUARD,
    Effect.POWER_SHIFT,
    Effect.SUBSTITUTE,
    Effect.RAGE_POWDER,
    Effect.ROOST,
    Effect.FOCUS_ENERGY,
    Effect.SALT_CURE,
    Effect.LEECH_SEED,
    Effect.POWDER,
    Effect.SPIKY_SHIELD,
    Effect.ENDURE,
    Effect.UPROAR,
    Effect.OBSTRUCT,
}

_PROTECT_BREAKING_EFFECTS: Set[Effect] = {
    Effect.FEINT,
    Effect.G_MAX_ONE_BLOW,
    Effect.G_MAX_RAPID_FLOW,
    Effect.SHADOW_FORCE,
    Effect.PHANTOM_FORCE,
    Effect.HYPERSPACE_FURY,
    Effect.HYPERSPACE_HOLE,
}

_TURN_COUNTER_EFFECTS: Set[Effect] = {
    Effect.BIDE,
    Effect.BIND,
    Effect.CLAMP,
    Effect.DISABLE,
    Effect.DOOM_DESIRE,
    Effect.DYNAMAX,
    Effect.EMBARGO,
    Effect.ENCORE,
    Effect.FIRE_SPIN,
    Effect.FUTURE_SIGHT,
    Effect.GRAVITY,
    Effect.G_MAX_CENTIFERNO,
    Effect.G_MAX_SANDBLAST,
    Effect.HEAL_BLOCK,
    Effect.INFESTATION,
    Effect.MAGMA_STORM,
    Effect.MAGNET_RISE,
    Effect.SAND_TOMB,
    Effect.SKY_DROP,
    Effect.SLOW_START,
    Effect.SNAP_TRAP,
    Effect.TAUNT,
    Effect.TELEKINESIS,
    Effect.THROAT_CHOP,
    Effect.THUNDER_CAGE,
    Effect.UPROAR,
    Effect.WHIRLPOOL,
    Effect.WRAP,
}

_ENDS_ON_MOVE_EFFECTS = {
    Effect.GLAIVE_RUSH,
    Effect.CHARGE,
    Effect.DANCER,
    Effect.GRUDGE,
    Effect.DESTINY_BOND,
    Effect.RAGE,
    Effect.INSTRUCT,
    Effect.FOCUS_PUNCH,
}

_ENDS_ON_SWITCH_EFFECTS = {
    Effect.MIND_READER,
    Effect.MUMMY,
    Effect.SPEED_SWAP,
    Effect.TYPECHANGE,
    Effect.SKILL_SWAP,
    Effect.PERISH0,
    Effect.PERISH1,
    Effect.PERISH2,
    Effect.PERISH3,
    Effect.FLASH_FIRE,
}

_ENDS_ON_TURN_EFFECTS = {
    Effect.AFTER_YOU,
    Effect.BANEFUL_BUNKER,
    Effect.BEAK_BLAST,
    Effect.BURNING_BULWARK,
    Effect.CRAFTY_SHIELD,
    Effect.FEINT,
    Effect.FLINCH,
    Effect.FOCUS_PUNCH,
    Effect.FOLLOW_ME,
    Effect.KINGS_SHIELD,
    Effect.CUSTAP_BERRY,
    Effect.MIND_READER,
    Effect.MAGIC_COAT,
    Effect.OBSTRUCT,
    Effect.PROTECT,
    Effect.QUASH,
    Effect.QUICK_CLAW,
    Effect.QUICK_DRAW,
    Effect.QUICK_GUARD,
    Effect.RAGE_POWDER,
    Effect.ROOST,
    Effect.SPIKY_SHIELD,
    Effect.SPOTLIGHT,
    Effect.WIDE_GUARD,
    Effect.INSTRUCT,
    Effect.FOCUS_PUNCH,
}

_ACTION_COUNTER_EFFECTS: Set[Effect] = {Effect.RAGE, Effect.STOCKPILE}

_FROM_DATA: Dict[str, Effect] = {
    "UNKNOWN": Effect.UNKNOWN,
    "AFTERYOU": Effect.AFTER_YOU,
    "AFTERMATH": Effect.AFTERMATH,
    "AQUARING": Effect.AQUA_RING,
    "AROMATHERAPY": Effect.AROMATHERAPY,
    "AROMAVEIL": Effect.AROMA_VEIL,
    "ATTRACT": Effect.ATTRACT,
    "AUTOTOMIZE": Effect.AUTOTOMIZE,
    "BADDREAMS": Effect.BAD_DREAMS,
    "BANEFULBUNKER": Effect.BANEFUL_BUNKER,
    "BATTLEBOND": Effect.BATTLE_BOND,
    "BIDE": Effect.BIDE,
    "BIND": Effect.BIND,
    "BURNINGBULWARK": Effect.BURNING_BULWARK,
    "BURNUP": Effect.BURN_UP,
    "CELEBRATE": Effect.CELEBRATE,
    "CHARGE": Effect.CHARGE,
    "CLAMP": Effect.CLAMP,
    "COMMANDER": Effect.COMMANDER,
    "CONFUSION": Effect.CONFUSION,
    "COURTCHANGE": Effect.COURT_CHANGE,
    "CRAFTYSHIELD": Effect.CRAFTY_SHIELD,
    "CUDCHEW": Effect.CUD_CHEW,
    "CURSE": Effect.CURSE,
    "CUSTAPBERRY": Effect.CUSTAP_BERRY,
    "DANCER": Effect.DANCER,
    "DEFENSECURL": Effect.DEFENSE_CURL,
    "DESTINYBOND": Effect.DESTINY_BOND,
    "DISABLE": Effect.DISABLE,
    "DISGUISE": Effect.DISGUISE,
    "DOOMDESIRE": Effect.DOOM_DESIRE,
    "DRAGONCHEER": Effect.DRAGON_CHEER,
    "DYNAMAX": Effect.DYNAMAX,
    "EERIESPELL": Effect.EERIE_SPELL,
    "ELECTRICTERRAIN": Effect.ELECTRIC_TERRAIN,
    "ELECTRIFY": Effect.ELECTRIFY,
    "EMBARGO": Effect.EMBARGO,
    "EMERGENCYEXIT": Effect.EMERGENCY_EXIT,
    "ENCORE": Effect.ENCORE,
    "ENDURE": Effect.ENDURE,
    "FALLEN": Effect.FALLEN,
    "FALLEN1": Effect.FALLEN1,
    "FALLEN2": Effect.FALLEN2,
    "FALLEN3": Effect.FALLEN3,
    "FALLEN4": Effect.FALLEN4,
    "FALLEN5": Effect.FALLEN5,
    "FAIRYLOCK": Effect.FAIRY_LOCK,
    "FEINT": Effect.FEINT,
    "FICKLEBEAM": Effect.FICKLE_BEAM,
    "FIRESPIN": Effect.FIRE_SPIN,
    "FLASHFIRE": Effect.FLASH_FIRE,
    "FLINCH": Effect.FLINCH,
    "FLOWERVEIL": Effect.FLOWER_VEIL,
    "FOCUSBAND": Effect.FOCUS_BAND,
    "FOCUSENERGY": Effect.FOCUS_ENERGY,
    "FOCUSPUNCH": Effect.FOCUS_PUNCH,
    "FOLLOWME": Effect.FOLLOW_ME,
    "FORESIGHT": Effect.FORESIGHT,
    "FOREWARN": Effect.FOREWARN,
    "FUTURESIGHT": Effect.FUTURE_SIGHT,
    "GASTROACID": Effect.GASTRO_ACID,
    "GUARDDOG": Effect.GUARD_DOG,
    "GLAIVERUSH": Effect.GLAIVE_RUSH,
    "GRAVITY": Effect.GRAVITY,
    "GRUDGE": Effect.GRUDGE,
    "GUARDSPLIT": Effect.GUARD_SPLIT,
    "GULPMISSILE": Effect.GULP_MISSILE,
    "GMAXCENTIFERNO": Effect.G_MAX_CENTIFERNO,
    "GMAXCHISTRIKE": Effect.G_MAX_CHI_STRIKE,
    "GMAXONEBLOW": Effect.G_MAX_ONE_BLOW,
    "GMAXRAPIDFLOW": Effect.G_MAX_RAPID_FLOW,
    "GMAXSANDBLAST": Effect.G_MAX_SANDBLAST,
    "HADRONENGINE": Effect.HADRON_ENGINE,
    "HEALBELL": Effect.HEAL_BELL,
    "HEALBLOCK": Effect.HEAL_BLOCK,
    "HEALER": Effect.HEALER,
    "HELPINGHAND": Effect.HELPING_HAND,
    "HYDRATION": Effect.HYDRATION,
    "HYPERSPACEFURY": Effect.HYPERSPACE_FURY,
    "HYPERSPACEHOLE": Effect.HYPERSPACE_HOLE,
    "ICEFACE": Effect.ICE_FACE,
    "ILLUSION": Effect.ILLUSION,
    "IMMUNITY": Effect.IMMUNITY,
    "IMPRISON": Effect.IMPRISON,
    "INFESTATION": Effect.INFESTATION,
    "INGRAIN": Effect.INGRAIN,
    "INNARDSOUT": Effect.INNARDS_OUT,
    "INSTRUCT": Effect.INSTRUCT,
    "INSOMNIA": Effect.INSOMNIA,
    "IRONBARBS": Effect.IRON_BARBS,
    "KINGSSHIELD": Effect.KINGS_SHIELD,
    "LASERFOCUS": Effect.LASER_FOCUS,
    "LEECHSEED": Effect.LEECH_SEED,
    "LEPPABERRY": Effect.LEPPA_BERRY,
    "LIGHTNINGROD": Effect.LIGHTNING_ROD,
    "LIMBER": Effect.LIMBER,
    "LINGERINGAROMA": Effect.LINGERING_AROMA,
    "LIQUIDOOZE": Effect.LIQUID_OOZE,
    "LOCKEDMOVE": Effect.LOCKED_MOVE,
    "LOCKON": Effect.LOCK_ON,
    "MAGICCOAT": Effect.MAGIC_COAT,
    "MAGMASTORM": Effect.MAGMA_STORM,
    "MAGNETRISE": Effect.MAGNET_RISE,
    "MAGNITUDE": Effect.MAGNITUDE,
    "MATBLOCK": Effect.MAT_BLOCK,
    "MAXGUARD": Effect.MAX_GUARD,
    "MIMIC": Effect.MIMIC,
    "MIMICRY": Effect.MIMICRY,
    "MINDREADER": Effect.MIND_READER,
    "MINIMIZE": Effect.MINIMIZE,
    "MIRACLEEYE": Effect.MIRACLE_EYE,
    "MIST": Effect.MIST,
    "MISTYTERRAIN": Effect.MISTY_TERRAIN,
    "MUMMY": Effect.MUMMY,
    "MUSTRECHARGE": Effect.MUST_RECHARGE,
    "NIGHTMARE": Effect.NIGHTMARE,
    "NORETREAT": Effect.NO_RETREAT,
    "OBLIVIOUS": Effect.OBLIVIOUS,
    "OBSTRUCT": Effect.OBSTRUCT,
    "OCTOLOCK": Effect.OCTOLOCK,
    "ORICHALCUMPULSE": Effect.ORICHALCUM_PULSE,
    "OWNTEMPO": Effect.OWN_TEMPO,
    "PARTIALLYTRAPPED": Effect.PARTIALLY_TRAPPED,
    "PASTELVEIL": Effect.PASTEL_VEIL,
    "PERISH0": Effect.PERISH0,
    "PERISH1": Effect.PERISH1,
    "PERISH2": Effect.PERISH2,
    "PERISH3": Effect.PERISH3,
    "PHANTOMFORCE": Effect.PHANTOM_FORCE,
    "POLTERGEIST": Effect.POLTERGEIST,
    "POWDER": Effect.POWDER,
    "POWERCONSTRUCT": Effect.POWER_CONSTRUCT,
    "POWERSHIFT": Effect.POWER_SHIFT,
    "POWERSPLIT": Effect.POWER_SPLIT,
    "POWERTRICK": Effect.POWER_TRICK,
    "PROTECT": Effect.PROTECT,
    "PROTECTIVEPADS": Effect.PROTECTIVE_PADS,
    "PROTOSYNTHESIS": Effect.PROTOSYNTHESIS,
    "PROTOSYNTHESISATK": Effect.PROTOSYNTHESISATK,
    "PROTOSYNTHESISDEF": Effect.PROTOSYNTHESISDEF,
    "PROTOSYNTHESISSPA": Effect.PROTOSYNTHESISSPA,
    "PROTOSYNTHESISSPD": Effect.PROTOSYNTHESISSPD,
    "PROTOSYNTHESISSPE": Effect.PROTOSYNTHESISSPE,
    "PSYCHICTERRAIN": Effect.PSYCHIC_TERRAIN,
    "PURSUIT": Effect.PURSUIT,
    "QUARKDRIVE": Effect.QUARK_DRIVE,
    "QUARKDRIVEATK": Effect.QUARKDRIVEATK,
    "QUARKDRIVEDEF": Effect.QUARKDRIVEDEF,
    "QUARKDRIVESPA": Effect.QUARKDRIVESPA,
    "QUARKDRIVESPD": Effect.QUARKDRIVESPD,
    "QUARKDRIVESPE": Effect.QUARKDRIVESPE,
    "QUASH": Effect.QUASH,
    "QUICKCLAW": Effect.QUICK_CLAW,
    "QUICKDRAW": Effect.QUICK_DRAW,
    "QUICKGUARD": Effect.QUICK_GUARD,
    "RAGE": Effect.RAGE,
    "RAGEPOWDER": Effect.RAGE_POWDER,
    "REFLECT": Effect.REFLECT,
    "RIPEN": Effect.RIPEN,
    "ROOST": Effect.ROOST,
    "ROUGHSKIN": Effect.ROUGH_SKIN,
    "SAFEGUARD": Effect.SAFEGUARD,
    "SAFETYGOGGLES": Effect.SAFETY_GOGGLES,
    "SALTCURE": Effect.SALT_CURE,
    "SANDTOMB": Effect.SAND_TOMB,
    "SCREENCLEANER": Effect.SCREEN_CLEANER,
    "SHADOWFORCE": Effect.SHADOW_FORCE,
    "SHEDSKIN": Effect.SHED_SKIN,
    "SILKTRAP": Effect.SILK_TRAP,
    "SKETCH": Effect.SKETCH,
    "SKILLSWAP": Effect.SKILL_SWAP,
    "SKYDROP": Effect.SKY_DROP,
    "SLOWSTART": Effect.SLOW_START,
    "SMACKDOWN": Effect.SMACK_DOWN,
    "SNAPTRAP": Effect.SNAP_TRAP,
    "SNATCH": Effect.SNATCH,
    "SPARKLINGARIA": Effect.SPARKLING_ARIA,
    "SPEEDSWAP": Effect.SPEED_SWAP,
    "SPIKYSHIELD": Effect.SPIKY_SHIELD,
    "SPITE": Effect.SPITE,
    "SPOTLIGHT": Effect.SPOTLIGHT,
    "STICKY_HOLD": Effect.STICKY_HOLD,
    "STICKY_WEB": Effect.STICKY_WEB,
    "STOCKPILE": Effect.STOCKPILE,
    "STOCKPILE1": Effect.STOCKPILE1,
    "STOCKPILE2": Effect.STOCKPILE2,
    "STOCKPILE3": Effect.STOCKPILE3,
    "STORMDRAIN": Effect.STORM_DRAIN,
    "STRUGGLE": Effect.STRUGGLE,
    "SUBSTITUTE": Effect.SUBSTITUTE,
    "SUCTIONCUPS": Effect.SUCTION_CUPS,
    "SUPREMEOVERLORD": Effect.SUPREME_OVERLORD,
    "SYRUPBOMB": Effect.SYRUP_BOMB,
    "SWEETVEIL": Effect.SWEET_VEIL,
    "SYMBIOSIS": Effect.SYMBIOSIS,
    "SYNCHRONIZE": Effect.SYNCHRONIZE,
    "TARSHOT": Effect.TAR_SHOT,
    "TAUNT": Effect.TAUNT,
    "TELEKINESIS": Effect.TELEKINESIS,
    "TELEPATHY": Effect.TELEPATHY,
    "TERASHELL": Effect.TERA_SHELL,
    "TERASHIFT": Effect.TERA_SHIFT,
    "TIDYUP": Effect.TIDY_UP,
    "TOXICDEBRIS": Effect.TOXIC_DEBRIS,
    "THERMALEXCHANGE": Effect.THERMAL_EXCHANGE,
    "THROATCHOP": Effect.THROAT_CHOP,
    "THUNDERCAGE": Effect.THUNDER_CAGE,
    "TORMENT": Effect.TORMENT,
    "TRAPPED": Effect.TRAPPED,
    "TRICK": Effect.TRICK,
    "TYPEADD": Effect.TYPEADD,
    "TYPECHANGE": Effect.TYPECHANGE,
    "UPROAR": Effect.UPROAR,
    "VITALSPIRIT": Effect.VITAL_SPIRIT,
    "WANDERINGSPIRIT": Effect.WANDERING_SPIRIT,
    "WATERBUBBLE": Effect.WATER_BUBBLE,
    "WATERVEIL": Effect.WATER_VEIL,
    "WHIRLPOOL": Effect.WHIRLPOOL,
    "WIDEGUARD": Effect.WIDE_GUARD,
    "WIMPOUT": Effect.WIMP_OUT,
    "WRAP": Effect.WRAP,
    "YAWN": Effect.YAWN,
    "ZERO_TO_HERO": Effect.ZERO_TO_HERO,
}
