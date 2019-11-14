# -*- coding: utf-8 -*-


def pytest_configure(config):
    """Adds the module's root directory to PYTHONPATH for tests.
    """
    import os
    import sys

    sys.path.append(os.path.realpath(os.path.dirname(__file__) + "/../src"))
