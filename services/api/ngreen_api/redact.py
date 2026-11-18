"""Remove addresses and phone numbers from operational logs."""

from __future__ import annotations

import re

_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE = re.compile(r"\+[1-9]\d{7,14}")


def scrub(text: str) -> str:
    cleaned = _EMAIL.sub("[email]", text)
    return _PHONE.sub("[phone]", cleaned)
