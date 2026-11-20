"""Prospective activation boundary, explicitly in Pakistan time."""

from datetime import datetime
from zoneinfo import ZoneInfo

PAKISTAN = ZoneInfo("Asia/Karachi")
# User requested AFTER 10 November, i.e. the start of 11 November in Pakistan.
AUTO_SUBMISSION_START = datetime(2026, 11, 11, tzinfo=PAKISTAN)
AUTO_SUBMISSION_START_LOCAL = "2026-11-11 00:00:00"


# Automatic submission is switched off. Clients now save, or use Save and Submit; nothing is submitted by a timer.
AUTO_SUBMISSION_ENABLED = False


def auto_submission_enabled(at=None):
    if not AUTO_SUBMISSION_ENABLED:
        return False
    at = at or datetime.now(PAKISTAN)
    if isinstance(at, str):
        at = datetime.fromisoformat(at)
    if at.tzinfo is None:
        at = at.replace(tzinfo=PAKISTAN)
    return at >= AUTO_SUBMISSION_START
