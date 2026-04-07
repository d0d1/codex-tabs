from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


DEFAULT_CONFIG_PATH = Path("~/.config/codex-tabs/sessions.toml").expanduser()
DEFAULT_CODEX_HOME = Path("~/.codex").expanduser()
LAUNCHER_CHOICES = ("auto", "wt", "tmux", "direct")
SESSION_ID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


@dataclass(slots=True)
class SessionEntry:
    name: str
    session_id: str
    cwd: str | None = None
    notes: str | None = None
    tags: list[str] = field(default_factory=list)


@dataclass(slots=True)
class CodexThread:
    session_id: str
    title: str
    cwd: str
    created_at: int
    updated_at: int
    first_user_message: str
    last_user_message: str = ""
    last_codex_message: str = ""


@dataclass(slots=True)
class RegistryData:
    sessions: dict[str, SessionEntry]
    ignored_session_ids: set[str]
    wt_profile: str | None = None
    launcher: str | None = None
