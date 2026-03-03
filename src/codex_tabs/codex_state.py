from __future__ import annotations

import json
import os
import re
import sqlite3
from pathlib import Path

from codex_tabs.models import CodexThread, DEFAULT_CODEX_HOME


def get_codex_home() -> Path:
    override = os.environ.get("CODEX_HOME")
    if override:
        return Path(override).expanduser()
    return DEFAULT_CODEX_HOME


def get_codex_state_db_path() -> Path:
    override = os.environ.get("CODEX_TABS_CODEX_STATE")
    if override:
        return Path(override).expanduser()

    codex_home = get_codex_home()
    candidates = sorted(codex_home.glob("state_*.sqlite"))
    if not candidates:
        raise ValueError(f"could not find a Codex state database under {codex_home}")
    return candidates[-1]


def load_codex_threads(
    *,
    limit: int,
    contains: str | None = None,
    include_archived: bool = False,
) -> list[CodexThread]:
    db_path = get_codex_state_db_path()
    where: list[str] = []
    params: list[object] = []

    if not include_archived:
        where.append("archived = 0")
    if contains:
        needle = f"%{contains.lower()}%"
        where.append(
            "("
            "lower(id) LIKE ? OR "
            "lower(title) LIKE ? OR "
            "lower(cwd) LIKE ? OR "
            "lower(first_user_message) LIKE ?"
            ")"
        )
        params.extend([needle, needle, needle, needle])

    sql = (
        "SELECT id, title, cwd, created_at, updated_at, first_user_message "
        "FROM threads "
    )
    if where:
        sql += "WHERE " + " AND ".join(where) + " "
    sql += "ORDER BY updated_at DESC LIMIT ?"
    params.append(limit)

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
    finally:
        conn.close()

    return [
        CodexThread(
            session_id=row[0],
            title=row[1] or "",
            cwd=row[2] or "",
            created_at=int(row[3] or 0),
            updated_at=int(row[4] or 0),
            first_user_message=row[5] or "",
        )
        for row in rows
    ]


def load_codex_threads_by_session_ids(
    session_ids: set[str],
    *,
    include_archived: bool = False,
) -> list[CodexThread]:
    if not session_ids:
        return []

    db_path = get_codex_state_db_path()
    placeholders = ", ".join("?" for _ in session_ids)
    params: list[object] = list(session_ids)
    sql = (
        "SELECT id, title, cwd, created_at, updated_at, first_user_message "
        "FROM threads "
        f"WHERE id IN ({placeholders}) "
    )
    if not include_archived:
        sql += "AND archived = 0 "
    sql += "ORDER BY updated_at DESC"

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
    finally:
        conn.close()

    return [
        CodexThread(
            session_id=row[0],
            title=row[1] or "",
            cwd=row[2] or "",
            created_at=int(row[3] or 0),
            updated_at=int(row[4] or 0),
            first_user_message=row[5] or "",
        )
        for row in rows
    ]


def get_codex_sessions_root() -> Path:
    return get_codex_home() / "sessions"


def extract_message_text(payload: object) -> str:
    if not isinstance(payload, dict):
        return ""
    content = payload.get("content")
    if not isinstance(content, list):
        return ""

    parts: list[str] = []
    for item in content:
        if not isinstance(item, dict):
            continue
        text = item.get("text")
        if isinstance(text, str) and text.strip():
            parts.append(text.strip())
            continue
        if item.get("type") == "output_text":
            inner = item.get("text")
            if isinstance(inner, str) and inner.strip():
                parts.append(inner.strip())
    return re.sub(r"\s+", " ", " ".join(parts)).strip()


def build_session_file_index() -> dict[str, Path]:
    sessions_root = get_codex_sessions_root()
    if not sessions_root.exists():
        return {}

    indexed: dict[str, tuple[float, Path]] = {}
    for path in sessions_root.rglob("*.jsonl"):
        match = re.search(
            r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
            path.name,
        )
        if not match:
            continue
        session_id = match.group(1)
        mtime = path.stat().st_mtime
        current = indexed.get(session_id)
        if current is None or mtime > current[0]:
            indexed[session_id] = (mtime, path)
    return {session_id: path for session_id, (_mtime, path) in indexed.items()}


def enrich_threads_with_last_messages(threads: list[CodexThread]) -> None:
    if not threads:
        return

    session_files = build_session_file_index()
    if not session_files:
        return

    for thread in threads:
        session_file = session_files.get(thread.session_id)
        if session_file is None:
            continue
        last_user = ""
        last_codex = ""
        with session_file.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if obj.get("type") != "response_item":
                    continue
                payload = obj.get("payload")
                if not isinstance(payload, dict) or payload.get("type") != "message":
                    continue
                role = payload.get("role")
                text = extract_message_text(payload)
                if not text:
                    continue
                if role == "user":
                    last_user = text
                elif role == "assistant":
                    last_codex = text
        thread.last_user_message = last_user
        thread.last_codex_message = last_codex


def search_codex_threads(
    query: str,
    *,
    limit: int,
    include_archived: bool = False,
) -> list[CodexThread]:
    query = query.strip()
    if not query:
        threads = load_codex_threads(limit=limit, include_archived=include_archived)
        enrich_threads_with_last_messages(threads)
        return threads

    lowered = query.lower()
    matched_session_ids: set[str] = set()

    session_files = build_session_file_index()
    for session_id, path in session_files.items():
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                text = ""
                if obj.get("type") == "response_item":
                    payload = obj.get("payload")
                    text = extract_message_text(payload)
                elif obj.get("type") == "event_msg":
                    payload = obj.get("payload")
                    if isinstance(payload, dict):
                        message = payload.get("message")
                        if isinstance(message, str):
                            text = re.sub(r"\s+", " ", message.strip())
                if text and lowered in text.lower():
                    matched_session_ids.add(session_id)
                    break

    threads = load_codex_threads(limit=max(limit, 200), include_archived=include_archived)
    metadata_matches = [
        thread
        for thread in threads
        if lowered in thread.session_id.lower()
        or lowered in thread.title.lower()
        or lowered in thread.cwd.lower()
        or lowered in thread.first_user_message.lower()
    ]
    for thread in metadata_matches:
        matched_session_ids.add(thread.session_id)

    if not matched_session_ids:
        return []

    matched_threads = load_codex_threads_by_session_ids(
        matched_session_ids,
        include_archived=include_archived,
    )
    enrich_threads_with_last_messages(matched_threads)
    return matched_threads[:limit]
