"""
Common options and arguments
"""
import functools
from pathlib import Path

import click

from .utils import parse_date_option

option_config = click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default="config.yaml",
    show_default=True,
    show_envvar=True,
    envvar="FATSECRET_SYNC_CONFIG",
    is_eager=True,
    help="Application's configuration file path",
)

option_from_date = click.option(
    "--from-date",
    required=True,
    type=str,
    help="Start date for the sync",
    callback=functools.partial(
        parse_date_option, prefer_incomplete_current_month_dates="past", prefer_incomplete_month_day="first"
    ),
)
option_to_date = click.option(
    "--to-date",
    default=None,
    required=False,
    type=str,
    help="End date for the sync (inclusive)",
    callback=functools.partial(
        parse_date_option, prefer_incomplete_current_month_dates="future", prefer_incomplete_month_day="last"
    ),
)
