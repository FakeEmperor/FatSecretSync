"""
Utility functions for command-line functions.
"""
import datetime
from typing import Literal, Optional, cast

import click
from kily.common.utils.dt import parse_human_date


def parse_date_option(
    ctx: click.Context,
    param: str,
    value: Optional[str],
    prefer_incomplete_current_month_dates: Literal["past", "future"],
    prefer_incomplete_month_day: Literal["first", "last"],
) -> Optional[datetime.datetime]:
    if value is None:
        return None
    try:
        return cast(
            datetime.datetime,
            parse_human_date(
                value,
                prefer_incomplete_current_month_dates=prefer_incomplete_current_month_dates,
                prefer_incomplete_month_day=prefer_incomplete_month_day,
                unknown_date_order="DMY",
            ),
        )
    except Exception:
        raise click.exceptions.BadOptionUsage(param, "Could not parse date", ctx)
