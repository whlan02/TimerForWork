from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time, datetime, timedelta
from typing import Optional


@dataclass
class TimeRecord:
    date: date
    start_time: time
    end_time: time
    duration_min: int
    duration_sec: int
    note: str = ""

    @classmethod
    def from_datetimes(
        cls,
        start_dt: datetime,
        end_dt: datetime,
        note: str = "",
    ) -> "TimeRecord":
        duration: timedelta = end_dt - start_dt
        total_seconds = int(round(duration.total_seconds()))
        duration_min = int(round(total_seconds / 60.0))
        return cls(
            date=start_dt.date(),
            start_time=start_dt.time().replace(microsecond=0),
            end_time=end_dt.time().replace(microsecond=0),
            duration_min=duration_min,
            duration_sec=total_seconds,
            note=note or "",
        )

    @classmethod
    def from_datetimes_with_elapsed(
        cls,
        start_dt: datetime,
        end_dt: datetime,
        elapsed_seconds: int,
        note: str = "",
    ) -> "TimeRecord":
        total_seconds = max(int(elapsed_seconds), 0)
        duration_min = int(round(total_seconds / 60.0))
        return cls(
            date=start_dt.date(),
            start_time=start_dt.time().replace(microsecond=0),
            end_time=end_dt.time().replace(microsecond=0),
            duration_min=duration_min,
            duration_sec=total_seconds,
            note=note or "",
        )



