from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
from datetime import datetime

from codex_tabs.models import SessionEntry
from codex_tabs.registry import require_entry
from codex_tabs.style import error_text


def open_named_sessions(
    entries: dict[str, SessionEntry],
    names: list[str],
    *,
    wt_profile: str | None = None,
    window: str,
    dry_run: bool,
) -> int:
    selected = [require_entry(entries, name) for name in names]

    codex_bin = shutil.which("codex")
    if codex_bin is None:
        print(error_text("codex is not available in PATH", stream=sys.stderr), file=sys.stderr)
        return 1

    backend = detect_launcher_backend()
    if backend == "wt":
        wt_parts = build_wt_command(
            selected,
            codex_bin=codex_bin,
            distro=os.environ.get("WSL_DISTRO_NAME", "Ubuntu"),
            profile=wt_profile or os.environ.get("CODEX_TABS_WT_PROFILE"),
            window=window,
            fallback_cwd=os.getcwd(),
        )
        if dry_run:
            print(subprocess.list2cmdline(wt_parts))
            return 0
        completed = subprocess.run(wt_parts, check=False)
        return completed.returncode

    if backend == "tmux":
        tmux_commands = build_tmux_commands(
            selected,
            codex_bin=codex_bin,
            fallback_cwd=os.getcwd(),
            current_session=get_current_tmux_session(),
        )
        if dry_run:
            for command in tmux_commands:
                print(shlex.join(command))
            return 0

        for command in tmux_commands:
            completed = subprocess.run(command, check=False)
            if completed.returncode != 0:
                return completed.returncode
        return 0

    print(
        error_text(
            "No supported launcher found. Install Windows Terminal in WSL or tmux on Linux/macOS.",
            stream=sys.stderr,
        ),
        file=sys.stderr,
    )
    return 1


def detect_launcher_backend() -> str | None:
    if os.environ.get("WSL_DISTRO_NAME") and shutil.which("wt.exe") is not None:
        return "wt"
    if shutil.which("tmux") is not None:
        return "tmux"
    if shutil.which("wt.exe") is not None:
        return "wt"
    return None


def get_current_tmux_session() -> str | None:
    if not os.environ.get("TMUX"):
        return None
    completed = subprocess.run(
        ["tmux", "display-message", "-p", "#S"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return None
    session_name = completed.stdout.strip()
    return session_name or None


def build_tmux_commands(
    entries: list[SessionEntry],
    *,
    codex_bin: str,
    fallback_cwd: str,
    current_session: str | None,
    session_name: str | None = None,
) -> list[list[str]]:
    if not entries:
        return []

    commands: list[list[str]] = []
    if current_session:
        target_session = current_session
        for entry in entries:
            commands.append(
                [
                    "tmux",
                    "new-window",
                    "-t",
                    target_session,
                    "-n",
                    entry.name,
                    build_codex_resume_shell_command(
                        entry,
                        codex_bin=codex_bin,
                        fallback_cwd=fallback_cwd,
                    ),
                ]
            )
        return commands

    target_session = session_name or default_tmux_session_name()
    first, *rest = entries
    commands.append(
        [
            "tmux",
            "new-session",
            "-d",
            "-s",
            target_session,
            "-n",
            first.name,
            build_codex_resume_shell_command(
                first,
                codex_bin=codex_bin,
                fallback_cwd=fallback_cwd,
            ),
        ]
    )
    for entry in rest:
        commands.append(
            [
                "tmux",
                "new-window",
                "-t",
                target_session,
                "-n",
                entry.name,
                build_codex_resume_shell_command(
                    entry,
                    codex_bin=codex_bin,
                    fallback_cwd=fallback_cwd,
                ),
            ]
        )
    commands.append(["tmux", "attach-session", "-t", target_session])
    return commands


def default_tmux_session_name() -> str:
    return f"codex-tabs-{datetime.now().strftime('%Y%m%d-%H%M%S')}"


def build_wt_command(
    entries: list[SessionEntry],
    *,
    codex_bin: str,
    distro: str,
    profile: str | None,
    window: str,
    fallback_cwd: str,
) -> list[str]:
    wt_parts: list[str] = ["wt.exe"]
    if window != "new":
        wt_parts.extend(["-w", window])

    first = True
    for entry in entries:
        command = build_codex_resume_shell_command(
            entry,
            codex_bin=codex_bin,
            fallback_cwd=fallback_cwd,
        )
        if not first:
            wt_parts.append(";")
        wt_parts.extend(
            [
                "new-tab",
                "--title",
                entry.name,
            ]
        )
        if profile:
            wt_parts.extend(
                [
                    "-p",
                    profile,
                ]
            )
        wt_parts.extend(
            [
                "wsl.exe",
                "-d",
                distro,
                "bash",
                "-lic",
                command,
            ]
        )
        first = False
    return wt_parts


def build_codex_resume_shell_command(
    entry: SessionEntry,
    *,
    codex_bin: str,
    fallback_cwd: str,
) -> str:
    cwd = entry.cwd or fallback_cwd
    return (
        f"cd {shell_quote(cwd)} && "
        f"{shell_quote(codex_bin)} --dangerously-bypass-approvals-and-sandbox "
        f"resume {shell_quote(entry.session_id)}"
    )


def shell_quote(value: str) -> str:
    return "'" + value.replace("'", "'\\''") + "'"
