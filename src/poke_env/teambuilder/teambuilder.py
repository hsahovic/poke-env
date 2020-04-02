# -*- coding: utf-8 -*-
"""This module defines the Teambuilder abstract class, which represents objects yielding
Pokemon Showdown teams in the context of communicating with Pokemon Showdown.
"""
from abc import ABC, abstractmethod


class Teambuilder(ABC):
    @abstractmethod
    def yield_team(self):
        pass
