# -*- coding: utf-8 -*-
"""This module contains exceptions.
"""


class ShowdownException(Exception):
    """This exception is raised when a non-managed message is received from the server."""

    pass


class UnexpectedEffectException(Exception):
    """This exception is raised when a non-managed effect is received from the server."""

    pass
