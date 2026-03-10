from __future__ import annotations

import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from codex_tabs.cli import (
    CodexThread,
    SessionEntry,
    browse_recent_threads,
    handle_wizard_add,
    ignore_other_untracked_previous_sessions,
    load_registry_data,
    parse_saved_tab_selection,
    prompt_main_action,
    resolve_single_saved_tab_selection,
    run_wizard,
)
from codex_tabs.wizard import handle_wizard_ignore_other, process_selected_thread


class WizardTests(unittest.TestCase):
    def test_prompt_main_action_shows_codex_tabs_only_options(self) -> None:
        output = io.StringIO()
        action = prompt_main_action(
            {
                "alpha": SessionEntry(
                    name="alpha",
                    session_id="01234567-89ab-cdef-0123-456789abcdef",
                )
            },
            input_fn=lambda _prompt: "q",
            output=output,
        )

        rendered = output.getvalue()
        self.assertEqual(action, "quit")
        self.assertIn("[W] Open all saved tabs", rendered)
        self.assertIn("Rename a saved tab alias", rendered)
        self.assertIn("Delete a saved tab alias", rendered)
        self.assertIn("Ignore other untracked previous sessions", rendered)

    def test_run_wizard_quit_when_no_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "sessions.toml"
            output = io.StringIO()

            with patch("codex_tabs.wizard.get_config_path", return_value=config), patch(
                "codex_tabs.wizard.detect_windows_admin_context",
                return_value=False,
            ):
                code = run_wizard(
                    input_fn=lambda _prompt: "q",
                    output=output,
                )

            rendered = output.getvalue()
            self.assertEqual(code, 0)
            self.assertIn("No saved tabs yet.", rendered)
            self.assertIn(
                "Everything here affects codex-tabs only. Your Codex setup and data stay unchanged.",
                rendered,
            )
            self.assertIn("Graceful shutdown complete", rendered)

    def test_run_wizard_can_clear_screen(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "sessions.toml"
            output = io.StringIO()
            responses = iter(["c", "q"])

            with patch("codex_tabs.wizard.get_config_path", return_value=config), patch(
                "codex_tabs.wizard.detect_windows_admin_context",
                return_value=False,
            ):
                code = run_wizard(
                    input_fn=lambda _prompt: next(responses),
                    output=output,
                )

            rendered = output.getvalue()
            self.assertEqual(code, 0)
            self.assertIn("\033[2J\033[H", rendered)
            self.assertGreaterEqual(rendered.count("Welcome to codex-tabs."), 2)

    def test_run_wizard_prompts_for_admin_setup_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "sessions.toml"
            output = io.StringIO()
            responses = iter(["", "q"])

            with patch("codex_tabs.wizard.get_config_path", return_value=config), patch(
                "codex_tabs.wizard.detect_windows_admin_context",
                return_value=True,
            ), patch(
                "codex_tabs.wizard.has_valid_wt_profile_setup",
                return_value=False,
            ), patch(
                "codex_tabs.wizard.setup_wt_admin",
                return_value=("Codex Tabs (Admin)", True, Path("/tmp/settings.json")),
            ):
                code = run_wizard(
                    input_fn=lambda _prompt: next(responses),
                    output=output,
                )

            rendered = output.getvalue()
            self.assertEqual(code, 0)
            self.assertIn("Admin mode detected.", rendered)
            self.assertIn("Configured elevated Windows Terminal profile", rendered)

    def test_ignore_other_untracked_previous_sessions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "sessions.toml"
            entries = {
                "personal": SessionEntry(
                    name="personal",
                    session_id="01234567-89ab-cdef-0123-456789abcdef",
                )
            }
            ignored_session_ids = {"11111111-2222-3333-4444-555555555555"}

            with patch(
                "codex_tabs.commands.load_codex_threads",
                return_value=[
                    CodexThread(
                        session_id="01234567-89ab-cdef-0123-456789abcdef",
                        title="Tracked",
                        cwd="/tmp/one",
                        created_at=1,
                        updated_at=3,
                        first_user_message="tracked",
                    ),
                    CodexThread(
                        session_id="89abcdef-0123-4567-89ab-cdef01234567",
                        title="Untracked",
                        cwd="/tmp/two",
                        created_at=1,
                        updated_at=2,
                        first_user_message="untracked",
                    ),
                    CodexThread(
                        session_id="11111111-2222-3333-4444-555555555555",
                        title="Ignored",
                        cwd="/tmp/three",
                        created_at=1,
                        updated_at=1,
                        first_user_message="ignored",
                    ),
                ],
            ), patch("codex_tabs.commands.enrich_threads_with_last_messages", return_value=None):
                count = ignore_other_untracked_previous_sessions(
                    entries,
                    ignored_session_ids,
                    current_session_id="01234567-89ab-cdef-0123-456789abcdef",
                    config_path=config,
                )

            self.assertEqual(count, 1)
            self.assertEqual(
                ignored_session_ids,
                {
                    "11111111-2222-3333-4444-555555555555",
                    "89abcdef-0123-4567-89ab-cdef01234567",
                },
            )
            registry = load_registry_data(config)
            self.assertEqual(registry.ignored_session_ids, ignored_session_ids)

    def test_handle_wizard_ignore_other_runs_from_main_menu_action(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "sessions.toml"
            output = io.StringIO()
            entries = {
                "personal": SessionEntry(
                    name="personal",
                    session_id="01234567-89ab-cdef-0123-456789abcdef",
                )
            }
            ignored_session_ids = set()

            with patch("codex_tabs.wizard.prompt_yes_no", return_value=True), patch(
                "codex_tabs.wizard.ignore_other_untracked_previous_sessions",
                return_value=2,
            ) as ignore_mock:
                handle_wizard_ignore_other(
                    entries,
                    ignored_session_ids,
                    config,
                    input_fn=lambda _prompt: "y",
                    output=output,
                )

            ignore_mock.assert_called_once_with(
                entries,
                ignored_session_ids,
                current_session_id=None,
                config_path=config,
            )
            rendered = output.getvalue()
            self.assertIn("This can take a moment", rendered)
            self.assertIn("Ignored 2 previous untracked sessions.", rendered)

    def test_parse_saved_tab_selection_accepts_indices_and_names(self) -> None:
        entries = {
            "alpha": SessionEntry(
                name="alpha",
                session_id="01234567-89ab-cdef-0123-456789abcdef",
            ),
            "beta": SessionEntry(
                name="beta",
                session_id="89abcdef-0123-4567-89ab-cdef01234567",
            ),
        }

        self.assertEqual(parse_saved_tab_selection("1 beta", entries), ["alpha", "beta"])

    def test_resolve_single_saved_tab_selection_requires_exactly_one(self) -> None:
        entries = {
            "alpha": SessionEntry(
                name="alpha",
                session_id="01234567-89ab-cdef-0123-456789abcdef",
            ),
            "beta": SessionEntry(
                name="beta",
                session_id="89abcdef-0123-4567-89ab-cdef01234567",
            ),
        }

        self.assertEqual(resolve_single_saved_tab_selection("2", entries), "beta")
        with self.assertRaises(ValueError):
            resolve_single_saved_tab_selection("1 2", entries)

    def test_search_flow_retries_after_no_matches(self) -> None:
        output = io.StringIO()
        entries = {}

        responses = iter(["3", "missing", "oauth", ""])
        with patch("codex_tabs.wizard.search_codex_threads", side_effect=[[], []]):
            handle_result = None
            with patch("codex_tabs.wizard.process_selected_thread") as process_mock:
                handle_wizard_add(
                    entries,
                    set(),
                    Path("/tmp/sessions.toml"),
                    input_fn=lambda _prompt: next(responses),
                    output=output,
                )
                handle_result = process_mock.called

        rendered = output.getvalue()
        self.assertFalse(handle_result)
        self.assertIn("No matching unsaved sessions found.", rendered)

    def test_browse_recent_threads_can_show_more(self) -> None:
        output = io.StringIO()
        threads_ten = [
            CodexThread(
                session_id=f"00000000-0000-0000-0000-{i:012d}",
                title=f"Thread {i}",
                cwd=f"/tmp/{i}",
                created_at=1,
                updated_at=100 - i,
                first_user_message=f"first {i}",
            )
            for i in range(10)
        ]
        threads_twenty = threads_ten + [
            CodexThread(
                session_id=f"11111111-1111-1111-1111-{i:012d}",
                title=f"More {i}",
                cwd=f"/more/{i}",
                created_at=1,
                updated_at=50 - i,
                first_user_message=f"more {i}",
            )
            for i in range(10)
        ]

        responses = iter(["m", "12"])
        with patch(
            "codex_tabs.wizard.load_codex_threads",
            side_effect=[threads_ten, threads_twenty],
        ), patch("codex_tabs.wizard.enrich_threads_with_last_messages", return_value=None):
            selected = browse_recent_threads(
                set(),
                set(),
                input_fn=lambda _prompt: next(responses),
                output=output,
            )

        self.assertIsNotNone(selected)
        self.assertEqual(selected.session_id, threads_twenty[11].session_id)

    def test_browse_recent_threads_hides_saved_sessions(self) -> None:
        output = io.StringIO()
        threads = [
            CodexThread(
                session_id="01234567-89ab-cdef-0123-456789abcdef",
                title="Saved",
                cwd="/tmp/saved",
                created_at=1,
                updated_at=3,
                first_user_message="saved",
            ),
            CodexThread(
                session_id="89abcdef-0123-4567-89ab-cdef01234567",
                title="Unsaved",
                cwd="/tmp/unsaved",
                created_at=1,
                updated_at=2,
                first_user_message="unsaved",
            ),
        ]

        with patch(
            "codex_tabs.wizard.load_codex_threads",
            return_value=threads,
        ), patch("codex_tabs.wizard.enrich_threads_with_last_messages", return_value=None):
            selected = browse_recent_threads(
                set(),
                {"01234567-89ab-cdef-0123-456789abcdef"},
                input_fn=lambda _prompt: "1",
                output=output,
            )

        self.assertIsNotNone(selected)
        self.assertEqual(selected.session_id, "89abcdef-0123-4567-89ab-cdef01234567")
        self.assertNotIn("/tmp/saved", output.getvalue())

    def test_handle_wizard_add_uses_most_recent_unsaved_session(self) -> None:
        output = io.StringIO()
        entries = {
            "saved": SessionEntry(
                name="saved",
                session_id="01234567-89ab-cdef-0123-456789abcdef",
            )
        }
        threads = [
            CodexThread(
                session_id="01234567-89ab-cdef-0123-456789abcdef",
                title="Saved",
                cwd="/tmp/saved",
                created_at=1,
                updated_at=3,
                first_user_message="saved",
            ),
            CodexThread(
                session_id="89abcdef-0123-4567-89ab-cdef01234567",
                title="Unsaved",
                cwd="/tmp/unsaved",
                created_at=1,
                updated_at=2,
                first_user_message="unsaved",
            ),
        ]

        with patch("codex_tabs.wizard.load_codex_threads", return_value=threads), patch(
            "codex_tabs.wizard.enrich_threads_with_last_messages",
            return_value=None,
        ), patch("codex_tabs.wizard.process_selected_thread") as process_mock:
            handle_wizard_add(
                entries,
                set(),
                Path("/tmp/sessions.toml"),
                input_fn=lambda _prompt: "1",
                output=output,
            )

        process_mock.assert_called_once()
        selected_thread = process_mock.call_args.args[0]
        self.assertEqual(selected_thread.session_id, "89abcdef-0123-4567-89ab-cdef01234567")

    def test_search_flow_hides_saved_sessions(self) -> None:
        output = io.StringIO()
        entries = {
            "saved": SessionEntry(
                name="saved",
                session_id="01234567-89ab-cdef-0123-456789abcdef",
            )
        }
        threads = [
            CodexThread(
                session_id="01234567-89ab-cdef-0123-456789abcdef",
                title="Saved",
                cwd="/tmp/saved",
                created_at=1,
                updated_at=3,
                first_user_message="saved",
            ),
            CodexThread(
                session_id="89abcdef-0123-4567-89ab-cdef01234567",
                title="Unsaved",
                cwd="/tmp/unsaved",
                created_at=1,
                updated_at=2,
                first_user_message="unsaved",
            ),
        ]

        responses = iter(["3", "oauth", "1"])
        with patch("codex_tabs.wizard.search_codex_threads", return_value=threads), patch(
            "codex_tabs.wizard.process_selected_thread"
        ) as process_mock:
            handle_wizard_add(
                entries,
                set(),
                Path("/tmp/sessions.toml"),
                input_fn=lambda _prompt: next(responses),
                output=output,
            )

        process_mock.assert_called_once()
        selected_thread = process_mock.call_args.args[0]
        self.assertEqual(selected_thread.session_id, "89abcdef-0123-4567-89ab-cdef01234567")
        self.assertNotIn("/tmp/saved", output.getvalue())

    def test_process_selected_thread_retries_invalid_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "sessions.toml"
            output = io.StringIO()
            responses = iter(["!!!", "Obsidian"])
            thread = CodexThread(
                session_id="01234567-89ab-cdef-0123-456789abcdef",
                title="Thread",
                cwd="/tmp/work",
                created_at=1,
                updated_at=2,
                first_user_message="first",
                last_user_message="last",
                last_codex_message="assistant",
            )

            with patch("codex_tabs.wizard.prompt_yes_no", return_value=False):
                entries: dict[str, SessionEntry] = {}
                process_selected_thread(
                    thread,
                    entries,
                    config,
                    input_fn=lambda _prompt: next(responses),
                output=output,
            )

            self.assertIn("obsidian", entries)
            self.assertEqual(entries["obsidian"].session_id, thread.session_id)
            self.assertIn(
                "Choose a name that includes at least one letter or number.",
                output.getvalue(),
            )

    def test_process_selected_thread_no_longer_prompts_bulk_ignore(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "sessions.toml"
            output = io.StringIO()
            thread = CodexThread(
                session_id="01234567-89ab-cdef-0123-456789abcdef",
                title="Thread",
                cwd="/tmp/work",
                created_at=1,
                updated_at=2,
                first_user_message="first",
                last_user_message="last",
                last_codex_message="assistant",
            )

            prompt_results = [False]

            def fake_prompt_yes_no(*_args, **_kwargs):
                return prompt_results.pop(0)

            entries: dict[str, SessionEntry] = {}
            with patch("codex_tabs.wizard.prompt_yes_no", side_effect=fake_prompt_yes_no), patch(
                "codex_tabs.wizard.ignore_other_untracked_previous_sessions"
            ) as ignore_mock:
                process_selected_thread(
                    thread,
                    entries,
                    config,
                    input_fn=lambda _prompt: "Obsidian",
                    output=output,
                )

            self.assertFalse(prompt_results)
            ignore_mock.assert_not_called()
            self.assertIn("obsidian", entries)
