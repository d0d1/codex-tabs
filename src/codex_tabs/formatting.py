from __future__ import annotations

import re
from datetime import datetime, timezone

from codex_tabs.models import CodexThread


def summarize_thread(thread: CodexThread) -> str:
    text = (thread.title or thread.first_user_message or thread.last_user_message).strip()
    return truncate_text(re.sub(r"\s+", " ", text), 120)


def format_timestamp(timestamp: int) -> str:
    if timestamp <= 0:
        return ""
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc).astimezone()
    absolute = dt.strftime("%Y-%m-%d %H:%M:%S %Z")
    relative = format_relative_age(dt)
    if not relative:
        return absolute
    return f"{absolute} ({relative})"


def format_relative_age(dt: datetime) -> str:
    now = datetime.now(tz=dt.tzinfo or timezone.utc)
    delta_seconds = int((now - dt).total_seconds())
    if delta_seconds < 0:
        delta_seconds = 0

    if delta_seconds < 60:
        return f"{delta_seconds}s ago"

    minutes, _seconds = divmod(delta_seconds, 60)
    if minutes < 60:
        return f"{minutes}m ago"

    hours, minutes = divmod(minutes, 60)
    if hours < 24:
        if minutes == 0:
            return f"{hours}h ago"
        return f"{hours}h {minutes}m ago"

    days, hours = divmod(hours, 24)
    if days < 7 and hours > 0:
        return f"{days}d {hours}h ago"
    return f"{days}d ago"


def truncate_text(text: str, limit: int) -> str:
    if len(text) > limit:
        return text[: limit - 3] + "..."
    return text
