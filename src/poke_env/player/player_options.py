"""Options shared by player and environment configuration."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Optional, Union

from poke_env.ps_client.account_configuration import AccountConfiguration
from poke_env.ps_client.server_configuration import (
    LocalhostServerConfiguration,
    ServerConfiguration,
)
from poke_env.teambuilder.teambuilder import Teambuilder


@dataclass(frozen=True)
class PlayerOptions:
    """Configuration shared by players created for the same environment.

    Pass an instance through the ``player_options`` argument of ``PokeEnv``,
    ``SinglesEnv``, or ``DoublesEnv`` to configure both environment agents.
    Account configuration and the event loop are supplied by the owner creating a
    player. They are intentionally not stored here because environments use one set
    of options for two accounts and recreate their loop when unpickled.
    """

    avatar: Optional[Union[str, int]] = None
    battle_format: str = "gen9randombattle"
    log_level: Optional[int] = None
    max_concurrent_battles: int = 1
    accept_open_team_sheet: Optional[bool] = False
    save_replays: Union[bool, str] = False
    server_configuration: Optional[ServerConfiguration] = LocalhostServerConfiguration
    start_timer_on_battle_start: bool = False
    start_listening: bool = True
    open_timeout: Optional[float] = 10.0
    ping_interval: Optional[float] = 20.0
    ping_timeout: Optional[float] = 20.0
    team: Optional[Union[str, Teambuilder]] = None
    strict_battle_tracking: bool = False

    def to_player_kwargs(
        self,
        *,
        account_configuration: Optional[AccountConfiguration],
        loop: asyncio.AbstractEventLoop,
    ) -> dict[str, Any]:
        """Return keyword arguments for constructing a :class:`Player`."""
        return {
            "account_configuration": account_configuration,
            "avatar": self.avatar,
            "battle_format": self.battle_format,
            "log_level": self.log_level,
            "max_concurrent_battles": self.max_concurrent_battles,
            "accept_open_team_sheet": self.accept_open_team_sheet,
            "save_replays": self.save_replays,
            "server_configuration": self.server_configuration,
            "start_timer_on_battle_start": self.start_timer_on_battle_start,
            "start_listening": self.start_listening,
            "open_timeout": self.open_timeout,
            "ping_interval": self.ping_interval,
            "ping_timeout": self.ping_timeout,
            "loop": loop,
            "team": self.team,
            "strict_battle_tracking": self.strict_battle_tracking,
        }
