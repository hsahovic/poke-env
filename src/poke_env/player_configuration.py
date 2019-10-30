# -*- coding: utf-8 -*-
"""This module contains objects related to player configuration.
"""
from collections import namedtuple

PlayerConfiguration = namedtuple("PlayerConfiguration", ["username", "password"])
"""Player configuration object. Represented with a tuple with two entries: username and
password."""
