# -*- coding: utf-8 -*-
"""This module defines the Effect class, which represents in-game effects.
"""
from enum import Enum, unique, auto


@unique
class Effect(Enum):
    """Enumeration, represent an effect a Pokemon can be affected by."""

    AROMATHERAPY = auto()
    AROMA_VEIL = auto()
    AUTOTOMIZE = auto()
    BAD_DREAMS = auto()
    BATTLE_BOND = auto()
    CONFUSION = auto()
    CUSTAP_BERRY = auto()
    DANCER = auto()
    DESTINY_BOND = auto()
    DISABLE = auto()
    DISGUISE = auto()
    ELECTRIC_TERRAIN = auto()
    EMERGENCY_EXIT = auto()
    ENCORE = auto()
    FLASH_FIRE = auto()
    FOCUS_ENERGY = auto()
    HEAL_BELL = auto()
    HYDRATION = auto()
    HYPERSPACE_FURY = auto()
    ILLUSION = auto()
    IMMUNITY = auto()
    INSOMNIA = auto()
    INFESTATION = auto()
    LEECH_SEED = auto()
    MAGNET_RISE = auto()
    MAGMA_STORM = auto()
    MISTY_TERRAIN = auto()
    MUMMY = auto()
    OBLIVIOUS = auto()
    PERISH0 = auto()
    PERISH1 = auto()
    PERISH2 = auto()
    PERISH3 = auto()
    PHANTOM_FORCE = auto()
    POWER_CONSTRUCT = auto()
    PROTECT = auto()
    PSYCHIC_TERRAIN = auto()
    PURSUIT = auto()
    SAFEGUARD = auto()
    SHADOW_FORCE = auto()
    SHED_SKIN = auto()
    SLOW_START = auto()
    SMACK_DOWN = auto()
    SWEET_VEIL = auto()
    STICKY_HOLD = auto()
    STICKY_WEB = auto()
    STRUGGLE = auto()
    SUBSTITUTE = auto()
    SYNCHRONIZE = auto()
    TAUNT = auto()
    TRAPPED = auto()
    TRICK = auto()
    TYPE_CHANGE = auto()
    TYPECHANGE = auto()
    WATER_BUBBLE = auto()
    WATER_VEIL = auto()
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
        return Effect[message.upper()]
