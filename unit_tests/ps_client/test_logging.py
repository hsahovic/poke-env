import subprocess
import sys
import textwrap

import pytest


@pytest.mark.parametrize(
    "script, expected",
    [
        (
            """
            logging.basicConfig(format="APP %(message)s", level=logging.INFO)
            player = RandomPlayer(start_listening=False)
            player.logger.info("client")
            logging.getLogger("poke-env").warning("package")
            """,
            "APP client\nAPP package\n",
        ),
        (
            """
            logging.basicConfig(format="APP %(message)s", level=logging.INFO)
            for username in ("first", "first", "second"):
                player = RandomPlayer(
                    account_configuration=AccountConfiguration(username, None),
                    start_listening=False,
                )
                player.logger.info(username)
            """,
            "APP first\nAPP first\nAPP second\n",
        ),
        (
            """
            player = RandomPlayer(start_listening=False, log_level=logging.DEBUG)
            player.logger.error("client")
            logging.getLogger("poke-env").error("package")
            """,
            "",
        ),
        (
            """
            player = RandomPlayer(start_listening=False)
            logging.basicConfig(format="APP %(message)s", level=logging.INFO)
            player.logger.info("late configuration")
            """,
            "APP late configuration\n",
        ),
        (
            """
            logger = logging.getLogger("poke-env.configured")
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("CUSTOM %(message)s"))
            handler.setLevel(logging.WARNING)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
            logger.propagate = False
            player = RandomPlayer(
                account_configuration=AccountConfiguration("configured", None),
                start_listening=False,
            )
            player.logger.info("hidden")
            player.logger.warning("visible")
            """,
            "CUSTOM visible\n",
        ),
        (
            """
            logger = logging.getLogger("poke-env")
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("PACKAGE %(message)s"))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
            player = RandomPlayer(start_listening=False)
            player.logger.info("client")
            logger.warning("package")
            """,
            "PACKAGE client\nPACKAGE package\n",
        ),
        (
            """
            logging.basicConfig(format="APP %(message)s", level=logging.WARNING)
            player = RandomPlayer(start_listening=False, log_level=logging.INFO)
            player.logger.info("explicit level")
            player.logger.debug("hidden")
            """,
            "APP explicit level\n",
        ),
    ],
)
def test_application_logging(script, expected):
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import logging\nfrom poke_env import AccountConfiguration, RandomPlayer\n"
            + textwrap.dedent(script),
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    assert result.stderr == expected
    assert result.stdout == ""
