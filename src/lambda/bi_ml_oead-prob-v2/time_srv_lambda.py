from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Optional, Union
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pandas as pd


def compute_time_features(
    start_time: Union[str, datetime],
    time_zone: str,
    now: Optional[datetime] = None,
) -> Dict[str, Union[str, int]]:
    """Derive time-based features from a UTC startTime and an IANA timezone.

    Args:
        start_time: UTC timestamp — ISO-8601 string or timezone-aware datetime.
        time_zone:  IANA timezone name, e.g. "America/New_York".
        now:        Current UTC time; defaults to datetime.now(timezone.utc).
                    Inject a fixed value for deterministic tests.

    Returns:
        dow          – day of week in local time, "1" (Mon) to "7" (Sun)
        deltaDays    – local_now.date() - local_start.date()  (negative = future)
        deltaHours   – local_now.hour  - local_start.hour     (time-of-day only)
        hourOfDay    – hour of startTime in local tz, 0-23
        minuteOfHour – minute of startTime in local tz, 0-59

    Raises:
        ValueError: if time_zone is not a valid IANA name or start_time cannot
                    be parsed as a date/time.
    """
    try:
        tz = ZoneInfo(time_zone)
    except (ZoneInfoNotFoundError, KeyError) as exc:
        raise ValueError(f"Unknown timezone: {time_zone!r}") from exc

    if isinstance(start_time, str):
        try:
            dt_utc = pd.to_datetime(start_time, utc=True).to_pydatetime()
        except Exception as exc:
            raise ValueError(f"Cannot parse startTime: {start_time!r}") from exc
    else:
        dt_utc = start_time if start_time.tzinfo else start_time.replace(tzinfo=timezone.utc)

    if now is None:
        now = datetime.now(timezone.utc)

    local_start = dt_utc.astimezone(tz)
    local_now = now.astimezone(tz)

    weekday = local_start.isoweekday()   # 1=Mon … 7=Sun
    return {
        "dow":          str(weekday),
        "deltaDays":    (local_now.date() - local_start.date()).days,
        "deltaHours":   local_now.hour - local_start.hour,
        "hourOfDay":    local_start.hour,
        "minuteOfHour": local_start.minute,
        "isWeekend":    1 if weekday >= 6 else 0,
    }
