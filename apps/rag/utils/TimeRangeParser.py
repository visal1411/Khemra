"""TimeRangeParser - converts between "00:10 - 00:19" strings and timedeltas.

The DB stores start_time / end_time as Postgres `interval`; the JSON / API
keeps using the human-readable "MM:SS - MM:SS" form.
"""
import re
from datetime import timedelta


class TimeRangeParser:
    _SEPARATOR = re.compile(r"\s*[-\u2013\u2014]\s*")

    @classmethod
    def parse(cls, text):
        """'00:10 - 00:19' -> (timedelta, timedelta).  '' -> (None, None).
        Raises ValueError when the text is not a valid range."""
        text = (text or "").strip()
        if not text:
            return None, None
        parts = cls._SEPARATOR.split(text)
        if len(parts) != 2:
            raise ValueError(f"Invalid time range '{text}' (expected 'MM:SS - MM:SS').")
        return cls._parse_clock(parts[0]), cls._parse_clock(parts[1])

    @classmethod
    def format(cls, start, end):
        """(timedelta, timedelta) -> '00:10 - 00:19'.  (None, None) -> ''."""
        if start is None or end is None:
            return ""
        return f"{cls._format_clock(start)} - {cls._format_clock(end)}"

    @staticmethod
    def to_seconds(value):
        return 0 if value is None else int(value.total_seconds())

    # ---- internals -------------------------------------------------------
    @staticmethod
    def _parse_clock(clock):
        try:
            nums = [int(p) for p in clock.strip().split(":")]
        except ValueError:
            raise ValueError(f"Invalid clock value '{clock}'.")
        if not 1 <= len(nums) <= 3 or any(n < 0 for n in nums):
            raise ValueError(f"Invalid clock value '{clock}'.")
        nums = [0] * (3 - len(nums)) + nums  # pad to H, M, S
        hours, minutes, seconds = nums
        return timedelta(hours=hours, minutes=minutes, seconds=seconds)

    @staticmethod
    def _format_clock(value):
        total = int(value.total_seconds())
        hours, rest = divmod(total, 3600)
        minutes, seconds = divmod(rest, 60)
        if hours:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"
