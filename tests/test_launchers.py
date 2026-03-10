from __future__ import annotations

import unittest
from unittest.mock import patch

from codex_tabs.cli import SessionEntry, build_tmux_commands, build_wt_command, detect_launcher_backend


class LauncherTests(unittest.TestCase):
    def test_build_wt_command_for_two_sessions(self) -> None:
        entries = [
            SessionEntry(
                name="personal",
                session_id="01234567-89ab-cdef-0123-456789abcdef",
                cwd="/home/example/notes",
            ),
            SessionEntry(
                name="work",
                session_id="89abcdef-0123-4567-89ab-cdef01234567",
                cwd="/home/example/project",
            ),
        ]

        cmd = build_wt_command(
            entries,
            codex_bin="/usr/bin/codex",
            distro="Ubuntu",
            profile=None,
            window="last",
            fallback_cwd="/tmp",
        )
        rendered = " ".join(cmd)

        self.assertEqual(cmd[:3], ["wt.exe", "-w", "last"])
        self.assertIn("new-tab", cmd)
        self.assertIn("personal", cmd)
        self.assertIn("work", cmd)
        self.assertIn("wsl.exe", cmd)
        self.assertIn("resume '01234567-89ab-cdef-0123-456789abcdef'", rendered)
        self.assertIn("resume '89abcdef-0123-4567-89ab-cdef01234567'", rendered)

    def test_build_wt_command_for_new_window_omits_window_flag(self) -> None:
        entries = [
            SessionEntry(
                name="personal",
                session_id="01234567-89ab-cdef-0123-456789abcdef",
            )
        ]

        cmd = build_wt_command(
            entries,
            codex_bin="/usr/bin/codex",
            distro="Ubuntu",
            profile=None,
            window="new",
            fallback_cwd="/tmp",
        )

        self.assertEqual(cmd[0], "wt.exe")
        self.assertNotIn("-w", cmd)

    def test_build_wt_command_with_profile(self) -> None:
        entries = [
            SessionEntry(
                name="personal",
                session_id="01234567-89ab-cdef-0123-456789abcdef",
            )
        ]

        cmd = build_wt_command(
            entries,
            codex_bin="/usr/bin/codex",
            distro="Ubuntu",
            profile="Ubuntu (Admin)",
            window="last",
            fallback_cwd="/tmp",
        )

        self.assertIn("-p", cmd)
        self.assertIn("Ubuntu (Admin)", cmd)

    def test_build_tmux_commands_for_new_session(self) -> None:
        entries = [
            SessionEntry(
                name="personal",
                session_id="01234567-89ab-cdef-0123-456789abcdef",
                cwd="/home/example/notes",
            ),
            SessionEntry(
                name="work",
                session_id="89abcdef-0123-4567-89ab-cdef01234567",
                cwd="/home/example/project",
            ),
        ]

        commands = build_tmux_commands(
            entries,
            codex_bin="/usr/bin/codex",
            fallback_cwd="/tmp",
            current_session=None,
            session_name="codex-tabs-test",
        )

        self.assertEqual(commands[0][:6], ["tmux", "new-session", "-d", "-s", "codex-tabs-test", "-n"])
        self.assertEqual(commands[1][:5], ["tmux", "new-window", "-t", "codex-tabs-test", "-n"])
        self.assertEqual(commands[-1], ["tmux", "attach-session", "-t", "codex-tabs-test"])
        self.assertIn("resume '01234567-89ab-cdef-0123-456789abcdef'", commands[0][-1])
        self.assertIn("resume '89abcdef-0123-4567-89ab-cdef01234567'", commands[1][-1])

    def test_build_tmux_commands_for_existing_session(self) -> None:
        entries = [
            SessionEntry(
                name="personal",
                session_id="01234567-89ab-cdef-0123-456789abcdef",
            )
        ]

        commands = build_tmux_commands(
            entries,
            codex_bin="/usr/bin/codex",
            fallback_cwd="/tmp",
            current_session="current",
        )

        self.assertEqual(commands, [[
            "tmux",
            "new-window",
            "-t",
            "current",
            "-n",
            "personal",
            "cd '/tmp' && '/usr/bin/codex' --dangerously-bypass-approvals-and-sandbox resume '01234567-89ab-cdef-0123-456789abcdef'",
        ]])

    def test_detect_launcher_backend_prefers_wt_in_wsl(self) -> None:
        with patch.dict("os.environ", {"WSL_DISTRO_NAME": "Ubuntu"}, clear=False), patch(
            "codex_tabs.launchers.shutil.which",
            side_effect=lambda name: "/mnt/c/Windows/System32/wt.exe" if name == "wt.exe" else None,
        ):
            self.assertEqual(detect_launcher_backend(), "wt")

    def test_detect_launcher_backend_uses_tmux_elsewhere(self) -> None:
        with patch.dict("os.environ", {}, clear=True), patch(
            "codex_tabs.launchers.shutil.which",
            side_effect=lambda name: "/usr/bin/tmux" if name == "tmux" else None,
        ):
            self.assertEqual(detect_launcher_backend(), "tmux")
