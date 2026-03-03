from __future__ import annotations

import os
from pathlib import Path

import tomllib

from codex_tabs.models import (
    DEFAULT_CONFIG_PATH,
    NAME_RE,
    SESSION_ID_RE,
    RegistryData,
    SessionEntry,
)


def get_config_path() -> Path:
    override = os.environ.get("CODEX_TABS_CONFIG")
    if override:
        return Path(override).expanduser()
    return DEFAULT_CONFIG_PATH


def load_registry_data(path: Path) -> RegistryData:
    if not path.exists():
        return RegistryData(sessions={}, ignored_session_ids=set())

    with path.open("rb") as f:
        data = tomllib.load(f)

    sessions = data.get("sessions", {})
    entries: dict[str, SessionEntry] = {}
    for name, raw in sessions.items():
        if not isinstance(raw, dict):
            continue
        session_id = raw.get("session_id")
        if not isinstance(session_id, str) or not session_id.strip():
            continue

        tags = raw.get("tags", [])
        if not isinstance(tags, list):
            tags = []

        entries[name] = SessionEntry(
            name=name,
            session_id=session_id.strip(),
            cwd=raw.get("cwd"),
            notes=raw.get("notes"),
            tags=[str(tag) for tag in tags],
        )
    ignored = data.get("ignored_session_ids", [])
    ignored_session_ids = {
        validate_session_id(str(session_id).strip().lower())
        for session_id in ignored
        if isinstance(session_id, str) and session_id.strip()
    }
    return RegistryData(sessions=entries, ignored_session_ids=ignored_session_ids)


def load_registry(path: Path) -> dict[str, SessionEntry]:
    return load_registry_data(path).sessions


def load_ignored_session_ids(path: Path) -> set[str]:
    return load_registry_data(path).ignored_session_ids


def write_registry(
    path: Path,
    entries: dict[str, SessionEntry],
    ignored_session_ids: set[str] | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if ignored_session_ids is None:
        ignored_session_ids = load_ignored_session_ids(path)

    lines: list[str] = [
        "# codex-tabs session registry",
        "# Generated and updated by codex-tabs.",
        "",
    ]
    if ignored_session_ids:
        rendered_ids = ", ".join(
            f'"{escape_toml(session_id)}"'
            for session_id in sorted(ignored_session_ids)
        )
        lines.append(f"ignored_session_ids = [{rendered_ids}]")
        lines.append("")

    for name in sorted(entries):
        entry = entries[name]
        lines.append(f"[sessions.{entry.name}]")
        lines.append(f'session_id = "{escape_toml(entry.session_id)}"')
        if entry.cwd:
            lines.append(f'cwd = "{escape_toml(entry.cwd)}"')
        if entry.notes:
            lines.append(f'notes = "{escape_toml(entry.notes)}"')
        if entry.tags:
            rendered_tags = ", ".join(f'"{escape_toml(tag)}"' for tag in entry.tags)
            lines.append(f"tags = [{rendered_tags}]")
        lines.append("")

    content = "\n".join(lines).rstrip() + "\n"
    path.write_text(content, encoding="utf-8")


def escape_toml(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def validate_name(name: str) -> str:
    if not NAME_RE.fullmatch(name):
        raise ValueError("session names must match ^[a-z0-9][a-z0-9._-]*$")
    return name


def validate_session_id(session_id: str) -> str:
    if not SESSION_ID_RE.fullmatch(session_id):
        raise ValueError(
            "session IDs must look like 01234567-89ab-cdef-0123-456789abcdef"
        )
    return session_id


def create_example_entries() -> dict[str, SessionEntry]:
    return {
        "personal": SessionEntry(
            name="personal",
            session_id="01234567-89ab-cdef-0123-456789abcdef",
            cwd="/home/example/notes",
            notes="Replace with a real session ID",
            tags=["notes", "personal"],
        ),
        "work": SessionEntry(
            name="work",
            session_id="89abcdef-0123-4567-89ab-cdef01234567",
            cwd="/home/example/code/project",
            notes="Replace with a real session ID",
            tags=["project"],
        ),
    }


def require_entry(entries: dict[str, SessionEntry], name: str) -> SessionEntry:
    try:
        return entries[name]
    except KeyError as exc:
        raise ValueError(f"unknown session name: {name}") from exc


def normalize_tags(tags: list[str]) -> list[str]:
    normalized = []
    seen = set()
    for tag in tags:
        cleaned = tag.strip().lower()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        normalized.append(cleaned)
    return normalized
