from __future__ import annotations

import io
import sqlite3
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta
from pathlib import Path

from codex_tabs.cli import (
    CodexThread,
    filter_ignored_threads,
    format_relative_age,
    format_timestamp,
    load_codex_threads,
    load_codex_threads_by_session_ids,
    print_import_candidates,
    search_codex_threads,
)


class ImportTests(unittest.TestCase):
    def test_load_codex_threads_from_sqlite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "state_5.sqlite"
            conn = sqlite3.connect(db_path)
            try:
                conn.execute(
                    """
                    CREATE TABLE threads (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        created_at INTEGER NOT NULL,
                        updated_at INTEGER NOT NULL,
                        source TEXT NOT NULL,
                        model_provider TEXT NOT NULL,
                        cwd TEXT NOT NULL,
                        sandbox_policy TEXT NOT NULL,
                        approval_mode TEXT NOT NULL,
                        tokens_used INTEGER NOT NULL DEFAULT 0,
                        has_user_event INTEGER NOT NULL DEFAULT 0,
                        archived INTEGER NOT NULL DEFAULT 0,
                        first_user_message TEXT NOT NULL DEFAULT ''
                    )
                    """
                )
                conn.execute(
                    """
                    INSERT INTO threads (
                        id, title, created_at, updated_at, source, model_provider, cwd,
                        sandbox_policy, approval_mode, archived, first_user_message
                    ) VALUES (?, ?, 0, ?, 'local', 'openai', ?, 'danger-full-access', 'never', ?, ?)
                    """,
                    (
                        "01234567-89ab-cdef-0123-456789abcdef",
                        "Personal notes",
                        200,
                        "/home/example/notes",
                        0,
                        "first message",
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO threads (
                        id, title, created_at, updated_at, source, model_provider, cwd,
                        sandbox_policy, approval_mode, archived, first_user_message
                    ) VALUES (?, ?, 0, ?, 'local', 'openai', ?, 'danger-full-access', 'never', ?, ?)
                    """,
                    (
                        "89abcdef-0123-4567-89ab-cdef01234567",
                        "Archived",
                        100,
                        "/home/example/project",
                        1,
                        "older message",
                    ),
                )
                conn.commit()
            finally:
                conn.close()

            import os

            old = os.environ.get("CODEX_TABS_CODEX_STATE")
            os.environ["CODEX_TABS_CODEX_STATE"] = str(db_path)
            try:
                threads = load_codex_threads(limit=10)
                self.assertEqual(len(threads), 1)
                self.assertEqual(threads[0].title, "Personal notes")

                all_threads = load_codex_threads(limit=10, include_archived=True)
                self.assertEqual(len(all_threads), 2)

                filtered = load_codex_threads(limit=10, contains="notes")
                self.assertEqual(len(filtered), 1)
                self.assertEqual(
                    filtered[0].session_id,
                    "01234567-89ab-cdef-0123-456789abcdef",
                )
            finally:
                if old is None:
                    del os.environ["CODEX_TABS_CODEX_STATE"]
                else:
                    os.environ["CODEX_TABS_CODEX_STATE"] = old

    def test_print_import_candidates_formats_recent_threads(self) -> None:
        threads = [
            CodexThread(
                session_id="01234567-89ab-cdef-0123-456789abcdef",
                title="Personal notes",
                cwd="/home/example/notes",
                created_at=1_699_999_000,
                updated_at=1_700_000_000,
                first_user_message="first text",
                last_user_message="last user text",
                last_codex_message="last codex text",
            )
        ]

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = print_import_candidates(threads)

        rendered = buf.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("[1]", rendered)
        self.assertIn("last updated:", rendered)
        self.assertIn("cwd: /home/example/notes", rendered)
        self.assertIn("first user message: first text", rendered)
        self.assertIn("last user message: last user text", rendered)
        self.assertIn("last Codex message: last codex text", rendered)

    def test_load_codex_threads_by_session_ids_from_sqlite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "state_5.sqlite"
            conn = sqlite3.connect(db_path)
            try:
                conn.execute(
                    """
                    CREATE TABLE threads (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        created_at INTEGER NOT NULL,
                        updated_at INTEGER NOT NULL,
                        source TEXT NOT NULL,
                        model_provider TEXT NOT NULL,
                        cwd TEXT NOT NULL,
                        sandbox_policy TEXT NOT NULL,
                        approval_mode TEXT NOT NULL,
                        tokens_used INTEGER NOT NULL DEFAULT 0,
                        has_user_event INTEGER NOT NULL DEFAULT 0,
                        archived INTEGER NOT NULL DEFAULT 0,
                        first_user_message TEXT NOT NULL DEFAULT ''
                    )
                    """
                )
                conn.execute(
                    """
                    INSERT INTO threads (
                        id, title, created_at, updated_at, source, model_provider, cwd,
                        sandbox_policy, approval_mode, archived, first_user_message
                    ) VALUES (?, ?, 0, ?, 'local', 'openai', ?, 'danger-full-access', 'never', 0, ?)
                    """,
                    (
                        "01234567-89ab-cdef-0123-456789abcdef",
                        "One",
                        200,
                        "/tmp/one",
                        "first one",
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO threads (
                        id, title, created_at, updated_at, source, model_provider, cwd,
                        sandbox_policy, approval_mode, archived, first_user_message
                    ) VALUES (?, ?, 0, ?, 'local', 'openai', ?, 'danger-full-access', 'never', 0, ?)
                    """,
                    (
                        "89abcdef-0123-4567-89ab-cdef01234567",
                        "Two",
                        100,
                        "/tmp/two",
                        "first two",
                    ),
                )
                conn.commit()
            finally:
                conn.close()

            import os

            old = os.environ.get("CODEX_TABS_CODEX_STATE")
            os.environ["CODEX_TABS_CODEX_STATE"] = str(db_path)
            try:
                threads = load_codex_threads_by_session_ids(
                    {
                        "89abcdef-0123-4567-89ab-cdef01234567",
                        "01234567-89ab-cdef-0123-456789abcdef",
                    }
                )
                self.assertEqual(
                    [thread.session_id for thread in threads],
                    [
                        "01234567-89ab-cdef-0123-456789abcdef",
                        "89abcdef-0123-4567-89ab-cdef01234567",
                    ],
                )
            finally:
                if old is None:
                    del os.environ["CODEX_TABS_CODEX_STATE"]
                else:
                    os.environ["CODEX_TABS_CODEX_STATE"] = old

    def test_search_codex_threads_matches_history_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "state_5.sqlite"
            sessions_root = Path(tmp) / "sessions" / "2026" / "03" / "03"
            sessions_root.mkdir(parents=True)
            session_path = sessions_root / "rollout-2026-03-03T00-00-00-01234567-89ab-cdef-0123-456789abcdef.jsonl"
            conn = sqlite3.connect(db_path)
            try:
                conn.execute(
                    """
                    CREATE TABLE threads (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        created_at INTEGER NOT NULL,
                        updated_at INTEGER NOT NULL,
                        source TEXT NOT NULL,
                        model_provider TEXT NOT NULL,
                        cwd TEXT NOT NULL,
                        sandbox_policy TEXT NOT NULL,
                        approval_mode TEXT NOT NULL,
                        tokens_used INTEGER NOT NULL DEFAULT 0,
                        has_user_event INTEGER NOT NULL DEFAULT 0,
                        archived INTEGER NOT NULL DEFAULT 0,
                        first_user_message TEXT NOT NULL DEFAULT ''
                    )
                    """
                )
                conn.execute(
                    """
                    INSERT INTO threads (
                        id, title, created_at, updated_at, source, model_provider, cwd,
                        sandbox_policy, approval_mode, archived, first_user_message
                    ) VALUES (?, ?, 0, ?, 'local', 'openai', ?, 'danger-full-access', 'never', 0, ?)
                    """,
                    (
                        "01234567-89ab-cdef-0123-456789abcdef",
                        "Calendar setup",
                        200,
                        "/tmp/one",
                        "first one",
                    ),
                )
                conn.commit()
            finally:
                conn.close()

            session_path.write_text(
                "\n".join(
                    [
                        '{"type":"response_item","payload":{"type":"message","role":"user","content":[{"type":"input_text","text":"In Google Calendar, paste your Google OAuth Client ID."}]}}',
                        '{"type":"response_item","payload":{"type":"message","role":"assistant","content":[{"type":"output_text","text":"assistant reply"}]}}',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            import os

            old_state = os.environ.get("CODEX_TABS_CODEX_STATE")
            old_home = os.environ.get("CODEX_HOME")
            os.environ["CODEX_TABS_CODEX_STATE"] = str(db_path)
            os.environ["CODEX_HOME"] = str(Path(tmp))
            try:
                threads = search_codex_threads("oauth", limit=10)
                self.assertEqual(len(threads), 1)
                self.assertEqual(
                    threads[0].session_id,
                    "01234567-89ab-cdef-0123-456789abcdef",
                )
                self.assertEqual(
                    threads[0].last_user_message,
                    "In Google Calendar, paste your Google OAuth Client ID.",
                )
                self.assertEqual(threads[0].last_codex_message, "assistant reply")
            finally:
                if old_state is None:
                    del os.environ["CODEX_TABS_CODEX_STATE"]
                else:
                    os.environ["CODEX_TABS_CODEX_STATE"] = old_state
                if old_home is None:
                    del os.environ["CODEX_HOME"]
                else:
                    os.environ["CODEX_HOME"] = old_home

    def test_format_timestamp_returns_text(self) -> None:
        rendered = format_timestamp(1_700_000_000)
        self.assertIn("(", rendered)
        self.assertIn("ago)", rendered)

    def test_format_relative_age_compact_units(self) -> None:
        now = datetime.now().astimezone()
        self.assertEqual(format_relative_age(now), "0s ago")
        self.assertEqual(
            format_relative_age(now - timedelta(minutes=5)),
            "5m ago",
        )

    def test_filter_ignored_threads_excludes_ignored_by_default(self) -> None:
        threads = [
            CodexThread(
                session_id="01234567-89ab-cdef-0123-456789abcdef",
                title="One",
                cwd="/tmp/one",
                created_at=1,
                updated_at=2,
                first_user_message="one",
            ),
            CodexThread(
                session_id="89abcdef-0123-4567-89ab-cdef01234567",
                title="Two",
                cwd="/tmp/two",
                created_at=1,
                updated_at=2,
                first_user_message="two",
            ),
        ]

        filtered = filter_ignored_threads(
            threads,
            ignored_session_ids={"89abcdef-0123-4567-89ab-cdef01234567"},
            include_ignored=False,
        )
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].session_id, "01234567-89ab-cdef-0123-456789abcdef")
