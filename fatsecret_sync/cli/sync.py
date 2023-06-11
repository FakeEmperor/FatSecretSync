"""
Sync commands
"""
import datetime
from pathlib import Path
from typing import Optional

import click
from kily.common.utils.config_loader import ConfigLoader
from kily.common.utils.dt import get_now

from ..api.models.common import DateInt
from ..core.models.config import AppConfig
from .common import option_config, option_from_date, option_to_date


@click.group()
def sync_group():
    """
    Commands related to synchronization of food diary between users.
    """


@sync_group.command()
@click.option("--from-user", "-s", required=True, type=str, help="User with entries to sync from")
@click.option("--to-user", "-t", required=True, type=str, help="User to sync entries to")
@option_from_date
@option_to_date
@option_config
def sync_diary(from_user: str, to_user: str, from_date: str, config: Path, to_date: Optional[str] = None):
    """
    Synchronizes diary of one user to another starting from requested date until (inclusive) end date.

    Args:
        from_user:
            User with entries to sync from.
        to_user:
            User to sync entries to.
        from_date:
            Start sync date.
        to_date:
            Inclusive end date.
    """
    if to_date is None:
        now: datetime.datetime = get_now()
        to_date = DateInt(year=now.year, month=now.month, day=now.day)
    config = ConfigLoader.load(AppConfig, path=config)
