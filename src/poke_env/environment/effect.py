# -*- coding: utf-8 -*-
"""This module defines the Effect class, which represents in-game effects.
"""
# pyre-ignore-all-errors[45]

import logging
from enum import Enum, unique, auto
from typing import Set


@unique
class Effect(Enum):
    """Enumeration, represent an effect a Pokemon can be affected by."""

    _UNKNOWN = auto()
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
    BIDE = auto()
    BIND = auto()
    BURN_UP = auto()
    CELEBRATE = auto()
    CHARGE = auto()
    CLAMP = auto()
    CONFUSION = auto()
    COURT_CHANGE = auto()
    CRAFTY_SHIELD = auto()
    CURSE = auto()
    CUSTAP_BERRY = auto()
    DANCER = auto()
    DESTINY_BOND = auto()
    DISABLE = auto()
    DISGUISE = auto()
    DOOM_DESIRE = auto()
    DYNAMAX = auto()
    EERIE_SPELL = auto()
    ELECTRIC_TERRAIN = auto()
    EMBARGO = auto()
    EMERGENCY_EXIT = auto()
    ENCORE = auto()
    ENDURE = auto()
    FAIRY_LOCK = auto()
    FEINT = auto()
    FIRE_SPIN = auto()
    FLASH_FIRE = auto()
    FLOWER_VEIL = auto()
    FOCUS_BAND = auto()
    FOCUS_ENERGY = auto()
    FORESIGHT = auto()
    FOREWARN = auto()
    FUTURE_SIGHT = auto()
    G_MAX_CENTIFERNO = auto()
    G_MAX_CHI_STRIKE = auto()
    G_MAX_ONE_BLOW = auto()
    G_MAX_RAPID_FLOW = auto()
    G_MAX_SANDBLAST = auto()
    GRAVITY = auto()
    GRUDGE = auto()
    GUARD_SPLIT = auto()
    GULP_MISSILE = auto()
    HEAL_BELL = auto()
    HEAL_BLOCK = auto()
    HEALER = auto()
    HYDRATION = auto()
    HYPERSPACE_FURY = auto()
    HYPERSPACE_HOLE = auto()
    ICE_FACE = auto()
    ILLUSION = auto()
    IMMUNITY = auto()
    IMPRISON = auto()
    INFESTATION = auto()
    INGRAIN = auto()
    INNARDS_OUT = auto
    INSOMNIA = auto()
    IRON_BARBS = auto()
    LASER_FOCUS = auto()
    LEECH_SEED = auto()
    LIGHTNING_ROD = auto()
    LIMBER = auto()
    LOCK_ON = auto()
    MAGMA_STORM = auto()
    MAGNET_RISE = auto()
    MAGNITUDE = auto()
    MAT_BLOCK = auto()
    MAX_GUARD = auto()
    MIMIC = auto()
    MIMICRY = auto()
    MIND_READER = auto()
    MIRACLE_EYE = auto()
    MIST = auto()
    MISTY_TERRAIN = auto()
    MUMMY = auto()
    NEUTRALIZING_GAS = auto()
    NIGHTMARE = auto()
    NO_RETREAT = auto()
    OBLIVIOUS = auto()
    OCTOLOCK = auto()
    OWN_TEMPO = auto()
    PASTEL_VEIL = auto()
    PERISH0 = auto()
    PERISH1 = auto()
    PERISH2 = auto()
    PERISH3 = auto()
    PHANTOM_FORCE = auto()
    POLTERGEIST = auto()
    POWDER = auto()
    POWER_CONSTRUCT = auto()
    POWER_SPLIT = auto()
    POWER_TRICK = auto()
    PROTECT = auto()
    PROTECTIVE_PADS = auto()
    PSYCHIC_TERRAIN = auto()
    PURSUIT = auto()
    QUASH = auto()
    QUICK_CLAW = auto()
    QUICK_GUARD = auto()
    REFLECT = auto()
    RIPEN = auto()
    ROUGH_SKIN = auto()
    SAFEGUARD = auto()
    SAFETY_GOGGLES = auto()
    SAND_TOMB = auto()
    SCREEN_CLEANER = auto()
    SHADOW_FORCE = auto()
    SHED_SKIN = auto()
    SKETCH = auto()
    SKILL_SWAP = auto()
    SKY_DROP = auto()
    SLOW_START = auto()
    SMACK_DOWN = auto()
    SNAP_TRAP = auto()
    SNATCH = auto()
    SPEED_SWAP = auto()
    SPITE = auto()
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
    SWEET_VEIL = auto()
    SYMBIOSIS = auto()
    SYNCHRONIZE = auto()
    TAR_SHOT = auto()
    TAUNT = auto()
    TELEKINESIS = auto()
    TELEPATHY = auto()
    THROAT_CHOP = auto()
    THUNDER_CAGE = auto()
    TORMENT = auto()
    TRAPPED = auto()
    TRICK = auto()
    TYPEADD = auto()
    TYPECHANGE = auto()
    TYPE_CHANGE = auto()
    UPROAR = auto()
    WANDERING_SPIRIT = auto()
    WATER_BUBBLE = auto()
    WATER_VEIL = auto()
    WHIRLPOOL = auto()
    WIDE_GUARD = auto()
    WIMP_OUT = auto()
    WRAP = auto()
    YAWN = auto()

    def __str__(self) -> str:
        return f"{self.name} (effect) object"

    @staticmethod
    def from_showdown_message(message: str) -> "Effect":
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
        try:
            return Effect[message.upper()]
        except KeyError:
            logging.getLogger("poke-env").warning(
                "Unexpected effect '%s' received. Effect._UNKNOWN will be used instead. "
                "If this is unexpected, please open an issue at "
                "https://github.com/hsahovic/poke-env/issues/ along with this error "
                "message and a description of your program.",
                message,
            )
            return Effect._UNKNOWN

    @property
    def breaks_protect(self):
        """
        :return: Wheter this effects breaks protect-like states.
        :rtype: bool
        """
        return self in _PROTECT_BREAKING_EFFECTS

    @property
    def is_turn_countable(self) -> bool:
        """
        :return: Wheter it is useful to keep track of the number of turns this effect
            has been active for.
        :rtype: bool
        """
        return self in _TURN_COUNTER_EFFECTS

    @property
    def is_action_countable(self) -> bool:
        """
        :return: Wheter it is useful to keep track of the number of times this effect
            has been activated.
        :rtype: bool
        """
        return self in _TURN_COUNTER_EFFECTS


_PROTECT_BREAKING_EFFECTS: Set[Effect] = {
    Effect.FEINT,
    Effect.SHADOW_FORCE,
    Effect.PHANTOM_FORCE,
    Effect.HYPERSPACE_FURY,
    Effect.HYPERSPACE_HOLE,
}

_TURN_COUNTER_EFFECTS: Set[Effect] = {
    Effect.BIND,
    Effect.CLAMP,
    Effect.DISABLE,
    Effect.DYNAMAX,
    Effect.EMBARGO,
    Effect.ENCORE,
    Effect.FIRE_SPIN,
    Effect.HEAL_BLOCK,
    Effect.INFESTATION,
    Effect.MAGMA_STORM,
    Effect.MAGNET_RISE,
    Effect.SAND_TOMB,
    Effect.SKY_DROP,
    Effect.SLOW_START,
    Effect.TAUNT,
    Effect.WHIRLPOOL,
    Effect.WRAP,
}

_ACTION_COUNTER_EFFECTS: Set[Effect] = {Effect.CONFUSION, Effect.TORMENT}
