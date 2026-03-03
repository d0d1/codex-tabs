from __future__ import annotations

import sys
from typing import TextIO

from codex_tabs.formatting import format_timestamp, summarize_thread, truncate_text
from codex_tabs.models import CodexThread, SessionEntry
from codex_tabs.style import accent_text, error_text, label_text


def print_numbered_saved_tabs(
    entries: dict[str, SessionEntry],
    *,
    output: TextIO,
) -> None:
    for i, name in enumerate(sorted(entries), start=1):
        entry = entries[name]
        details = [entry.session_id[:8]]
        if entry.cwd:
            details.append(entry.cwd)
        elif entry.notes:
            details.append(entry.notes)
        print(
            f"{accent_text(f'[{i}]', stream=output)} {entry.name}  {'  '.join(details)}",
            file=output,
        )


def print_thread_details(thread: CodexThread, *, output: TextIO) -> None:
    if thread.updated_at:
        print(
            f"{label_text('last updated:', stream=output)} {format_timestamp(thread.updated_at)}",
            file=output,
        )
    if thread.cwd:
        print(f"{label_text('cwd:', stream=output)} {thread.cwd}", file=output)
        print("", file=output)
    if thread.first_user_message:
        print(
            f"{label_text('first user message:', stream=output)} {truncate_text(thread.first_user_message, 160)}",
            file=output,
        )
    if thread.last_user_message:
        print(
            f"{label_text('last user message:', stream=output)} {truncate_text(thread.last_user_message, 160)}",
            file=output,
        )
    if thread.last_codex_message:
        print(
            f"{label_text('last Codex message:', stream=output)} {truncate_text(thread.last_codex_message, 160)}",
            file=output,
        )


def print_import_candidates(threads: list[CodexThread]) -> int:
    if not threads:
        print(
            error_text("No Codex sessions found for the current query.", stream=sys.stderr),
            file=sys.stderr,
        )
        return 1

    for i, thread in enumerate(threads, start=1):
        if i > 1:
            print()
        print(accent_text(f"[{i}]", stream=sys.stdout))
        print(f"    {label_text('last updated:', stream=sys.stdout)} {format_timestamp(thread.updated_at)}")
        if thread.cwd:
            print(f"    {label_text('cwd:', stream=sys.stdout)} {thread.cwd}")
            print()
        if thread.first_user_message:
            print(
                f"    {label_text('first user message:', stream=sys.stdout)} {truncate_text(thread.first_user_message, 120)}"
            )
        if thread.last_user_message:
            print(
                f"    {label_text('last user message:', stream=sys.stdout)} {truncate_text(thread.last_user_message, 120)}"
            )
        if thread.last_codex_message:
            print(
                f"    {label_text('last Codex message:', stream=sys.stdout)} {truncate_text(thread.last_codex_message, 120)}"
            )
    return 0


def filter_ignored_threads(
    threads: list[CodexThread],
    *,
    ignored_session_ids: set[str],
    include_ignored: bool,
) -> list[CodexThread]:
    if include_ignored or not ignored_session_ids:
        return threads
    return [
        thread for thread in threads if thread.session_id not in ignored_session_ids
    ]


def print_ignored_metadata(thread: CodexThread) -> None:
    if thread.cwd:
        print(f"    {label_text('cwd:', stream=sys.stdout)} {thread.cwd}")
    if thread.updated_at:
        print(f"    {label_text('updated:', stream=sys.stdout)} {format_timestamp(thread.updated_at)}")
    summary = summarize_thread(thread)
    if summary:
        print(f"    {label_text('summary:', stream=sys.stdout)} {summary}")
