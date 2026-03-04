from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable, TextIO

from codex_tabs.codex_state import (
    enrich_threads_with_last_messages,
    load_codex_threads,
    search_codex_threads,
)
from codex_tabs.commands import (
    cmd_list,
    cmd_remove,
    cmd_rename,
    ignore_other_untracked_previous_sessions,
)
from codex_tabs.display import (
    filter_ignored_threads,
    print_import_candidates,
    print_numbered_saved_tabs,
    print_thread_details,
)
from codex_tabs.launchers import open_named_sessions
from codex_tabs.models import CodexThread, SessionEntry
from codex_tabs.registry import (
    get_config_path,
    load_registry,
    load_registry_data,
    validate_name,
    write_registry,
)
from codex_tabs.style import (
    header_text,
    label_text,
    menu_line,
    prompt_input,
    success_text,
    warning_text,
    error_text,
)


def run_wizard(
    *,
    input_fn: Callable[[str], str] = input,
    output: TextIO = sys.stdout,
) -> int:
    config_path = get_config_path()

    print_wizard_header(config_path, output=output)

    while True:
        registry = load_registry_data(config_path)
        entries = registry.sessions
        ignored_session_ids = registry.ignored_session_ids
        action = prompt_main_action(entries, input_fn=input_fn, output=output)
        if action == "quit":
            print(success_text("Graceful shutdown complete", stream=output), file=output)
            return 0
        if action == "clear":
            clear_screen(output=output)
            print_wizard_header(config_path, output=output)
            continue
        if action == "list":
            if not entries:
                print(warning_text("No saved tabs yet.", stream=output), file=output)
            else:
                print("", file=output)
                cmd_list(entries, config_path)
            continue
        if action == "add":
            handle_wizard_add(
                entries,
                ignored_session_ids,
                config_path,
                input_fn=input_fn,
                output=output,
            )
            continue
        if action == "open":
            handle_wizard_open(entries, input_fn=input_fn, output=output)
            continue
        if action == "open-all":
            handle_wizard_open_all(entries, input_fn=input_fn, output=output)
            continue
        if action == "rename":
            handle_wizard_rename(entries, config_path, input_fn=input_fn, output=output)
            continue
        if action == "remove":
            handle_wizard_remove(entries, config_path, input_fn=input_fn, output=output)
            continue


def prompt_main_action(
    entries: dict[str, SessionEntry],
    *,
    input_fn: Callable[[str], str],
    output: TextIO,
) -> str:
    if not entries:
        print("", file=output)
        print(warning_text("No saved tabs yet.", stream=output), file=output)
        menu_line("A", "Add a tab", output=output)
        menu_line("C", "Clear the screen", output=output)
        menu_line("Q", "Quit", output=output)
        while True:
            choice = prompt_input(input_fn, "> ", output=output).strip().lower()
            if choice in {"a", "add"}:
                return "add"
            if choice in {"c", "clear"}:
                return "clear"
            if choice in {"q", "quit"}:
                return "quit"
    else:
        print("", file=output)
        print(header_text("What would you like to do?", stream=output), file=output)
        menu_line("W", "Open all saved tabs", output=output)
        menu_line("O", "Open a tab", output=output)
        menu_line("A", "Add a tab", output=output)
        menu_line("L", "List tabs", output=output)
        menu_line("C", "Clear the screen", output=output)
        menu_line("R", "Rename a saved tab alias", output=output)
        menu_line("D", "Delete a saved tab alias", output=output)
        menu_line("Q", "Quit", output=output)
        while True:
            choice = prompt_input(input_fn, "> ", output=output).strip().lower()
            if choice in {"w", "open-all"}:
                return "open-all"
            if choice in {"o", "open"}:
                return "open"
            if choice in {"a", "add"}:
                return "add"
            if choice in {"l", "list"}:
                return "list"
            if choice in {"c", "clear"}:
                return "clear"
            if choice in {"r", "rename"}:
                return "rename"
            if choice in {"d", "delete", "remove"}:
                return "remove"
            if choice in {"q", "quit"}:
                return "quit"


def print_wizard_header(config_path: Path, *, output: TextIO) -> None:
    print("", file=output)
    print(header_text("Welcome to codex-tabs.", stream=output), file=output)
    print(f"{label_text('Registry:', stream=output)} {config_path}", file=output)
    print(
        label_text(
            "Everything here affects codex-tabs only. Your Codex setup and data stay unchanged.",
            stream=output,
        ),
        file=output,
    )


def clear_screen(*, output: TextIO) -> None:
    output.write("\033[2J\033[H")
    output.flush()


def handle_wizard_add(
    entries: dict[str, SessionEntry],
    ignored_session_ids: set[str],
    config_path: Path,
    *,
    input_fn: Callable[[str], str],
    output: TextIO,
) -> None:
    print("", file=output)
    print(header_text("Add a tab from an existing Codex session.", stream=output), file=output)
    menu_line("1", "Use the most recent active session", output=output)
    menu_line("2", "Show the recent session list", output=output)
    menu_line("3", "Search recent sessions", output=output)
    menu_line("B", "Back", output=output)

    while True:
        choice = prompt_input(input_fn, "> ", output=output).strip().lower()
        if choice in {"b", "back"}:
            return
        if choice == "1":
            threads = load_codex_threads(limit=1)
            enrich_threads_with_last_messages(threads)
            threads = filter_ignored_threads(
                threads,
                ignored_session_ids=ignored_session_ids,
                include_ignored=False,
            )
            if not threads:
                print(warning_text("No Codex sessions found.", stream=output), file=output)
                return
            process_selected_thread(threads[0], entries, config_path, input_fn=input_fn, output=output)
            return
        if choice == "2":
            selected = browse_recent_threads(
                ignored_session_ids,
                input_fn=input_fn,
                output=output,
            )
            if selected:
                process_selected_thread(selected, entries, config_path, input_fn=input_fn, output=output)
            return
        if choice == "3":
            while True:
                query = prompt_input(input_fn, "Search text (blank to go back): ", output=output).strip()
                if not query:
                    return
                threads = search_codex_threads(query, limit=10)
                threads = filter_ignored_threads(
                    threads,
                    ignored_session_ids=ignored_session_ids,
                    include_ignored=False,
                )
                if not threads:
                    print(warning_text("No matching sessions found.", stream=output), file=output)
                    continue
                selected = choose_thread_from_list(threads, input_fn=input_fn, output=output)
                if selected:
                    process_selected_thread(
                        selected,
                        entries,
                        config_path,
                        input_fn=input_fn,
                        output=output,
                    )
                    return


def choose_thread_from_list(
    threads: list[CodexThread],
    *,
    input_fn: Callable[[str], str],
    output: TextIO,
) -> CodexThread | None:
    print("", file=output)
    result = print_import_candidates(threads)
    if result != 0:
        return None
    while True:
        raw = prompt_input(input_fn, "Select a session by number (blank to cancel): ", output=output).strip()
        if not raw:
            return None
        if raw.isdigit():
            index = int(raw)
            if 1 <= index <= len(threads):
                return threads[index - 1]


def browse_recent_threads(
    ignored_session_ids: set[str],
    *,
    input_fn: Callable[[str], str],
    output: TextIO,
    initial_limit: int = 3,
    step: int = 10,
) -> CodexThread | None:
    limit = initial_limit
    while True:
        threads = load_codex_threads(limit=limit)
        enrich_threads_with_last_messages(threads)
        threads = filter_ignored_threads(
            threads,
            ignored_session_ids=ignored_session_ids,
            include_ignored=False,
        )
        if not threads:
            print(warning_text("No Codex sessions found.", stream=output), file=output)
            return None

        print("", file=output)
        result = print_import_candidates(threads)
        if result != 0:
            return None

        if len(threads) < limit:
            prompt = "Select a session by number (blank to cancel): "
        else:
            prompt = "Select a session by number, or [M] to show more (blank to cancel): "

        while True:
            print("", file=output)
            raw = prompt_input(input_fn, prompt, output=output).strip().lower()
            if not raw:
                return None
            if raw.isdigit():
                index = int(raw)
                if 1 <= index <= len(threads):
                    return threads[index - 1]
            if raw in {"m", "more"} and len(threads) >= limit:
                limit += step
                break


def process_selected_thread(
    thread: CodexThread,
    entries: dict[str, SessionEntry],
    config_path: Path,
    *,
    input_fn: Callable[[str], str],
    output: TextIO,
) -> None:
    print("", file=output)
    print(header_text("Selected session:", stream=output), file=output)
    print_thread_details(thread, output=output)
    print("", file=output)
    while True:
        name = prompt_input(input_fn, "Name this tab (leave blank to cancel): ", output=output).strip()
        if not name:
            return

        try:
            validated_name = validate_name(name)
        except ValueError as exc:
            print(error_text(str(exc), stream=output), file=output)
            continue
        break

    entries[validated_name] = SessionEntry(
        name=validated_name,
        session_id=thread.session_id,
        cwd=thread.cwd or None,
    )
    registry = load_registry_data(config_path)
    ignored_session_ids = registry.ignored_session_ids
    write_registry(config_path, entries, ignored_session_ids)
    print(success_text(f"Saved tab: {validated_name}", stream=output), file=output)

    ignore_rest = prompt_yes_no(
        "Ignore all other untracked previous sessions? [y/N]: ",
        input_fn=input_fn,
        default=False,
    )
    if ignore_rest:
        print(
            label_text(
                "Ignoring other untracked previous sessions. This can take a moment...",
                stream=output,
            ),
            file=output,
        )
        ignored_count = ignore_other_untracked_previous_sessions(
            entries,
            ignored_session_ids,
            current_session_id=thread.session_id,
            config_path=config_path,
        )
        if ignored_count == 0:
            print(warning_text("No other untracked previous sessions to ignore.", stream=output), file=output)
        elif ignored_count == 1:
            print(success_text("Ignored 1 previous untracked session.", stream=output), file=output)
        else:
            print(success_text(f"Ignored {ignored_count} previous untracked sessions.", stream=output), file=output)

    open_now = prompt_yes_no("Open it now? [Y/n]: ", input_fn=input_fn, default=True)
    if open_now:
        code = open_named_sessions(
            load_registry(config_path),
            [validated_name],
            window="last",
            dry_run=False,
        )
        if code == 0:
            print(
                success_text(
                    f"Opened. You can reopen it later with: codex-tabs open {validated_name}",
                    stream=output,
                ),
                file=output,
            )
        else:
            print(error_text(f"Open failed with exit code {code}.", stream=output), file=output)
    else:
        print(
            label_text(f"You can open it later with: codex-tabs open {validated_name}", stream=output),
            file=output,
        )


def handle_wizard_open(
    entries: dict[str, SessionEntry],
    *,
    input_fn: Callable[[str], str],
    output: TextIO,
) -> None:
    if not entries:
        print(warning_text("No saved tabs yet.", stream=output), file=output)
        return
    print("", file=output)
    print(header_text("Saved tabs:", stream=output), file=output)
    print_numbered_saved_tabs(entries, output=output)
    raw = prompt_input(
        input_fn,
        "Enter one or more numbers or names separated by spaces (blank to cancel): ",
        output=output,
    ).strip()
    if not raw:
        print(warning_text("Canceled.", stream=output), file=output)
        return
    try:
        names = parse_saved_tab_selection(raw, entries)
    except ValueError as exc:
        print(error_text(str(exc), stream=output), file=output)
        return
    try:
        code = open_named_sessions(entries, names, window="last", dry_run=False)
    except ValueError as exc:
        print(error_text(str(exc), stream=output), file=output)
        return
    if code == 0:
        print(success_text(f"Opened. You can also run: codex-tabs open {' '.join(names)}", stream=output), file=output)
    else:
        print(error_text(f"Open failed with exit code {code}.", stream=output), file=output)


def handle_wizard_open_all(
    entries: dict[str, SessionEntry],
    *,
    input_fn: Callable[[str], str],
    output: TextIO,
) -> None:
    if not entries:
        print(warning_text("No saved tabs yet.", stream=output), file=output)
        return

    names = sorted(entries)
    if len(names) >= 6:
        confirmed = prompt_yes_no(
            f"Open {len(names)} saved tabs in separate Windows Terminal tabs? [y/N]: ",
            input_fn=input_fn,
            default=False,
        )
        if not confirmed:
            print(warning_text("Canceled.", stream=output), file=output)
            return

    code = open_named_sessions(entries, names, window="last", dry_run=False)
    if code == 0:
        print("", file=output)
        print(success_text("Opened all saved tabs.", stream=output), file=output)
    else:
        print(error_text(f"Open failed with exit code {code}.", stream=output), file=output)


def handle_wizard_rename(
    entries: dict[str, SessionEntry],
    config_path: Path,
    *,
    input_fn: Callable[[str], str],
    output: TextIO,
) -> None:
    if not entries:
        print(warning_text("No saved tabs yet.", stream=output), file=output)
        return
    print("", file=output)
    print(header_text("Saved tab aliases:", stream=output), file=output)
    print(label_text("This only changes codex-tabs. Codex itself is not modified.", stream=output), file=output)
    print_numbered_saved_tabs(entries, output=output)
    raw = prompt_input(input_fn, "Select a tab to rename (blank to cancel): ", output=output).strip()
    if not raw:
        print(warning_text("Canceled.", stream=output), file=output)
        return
    try:
        old_name = resolve_single_saved_tab_selection(raw, entries)
    except ValueError as exc:
        print(error_text(str(exc), stream=output), file=output)
        return
    new_name = prompt_input(input_fn, "New name (blank to cancel): ", output=output).strip()
    if not new_name:
        print(warning_text("Canceled.", stream=output), file=output)
        return
    try:
        cmd_rename(entries, config_path, old_name, new_name)
        print(success_text(f"Renamed {old_name} to {new_name}.", stream=output), file=output)
    except ValueError as exc:
        print(error_text(str(exc), stream=output), file=output)


def handle_wizard_remove(
    entries: dict[str, SessionEntry],
    config_path: Path,
    *,
    input_fn: Callable[[str], str],
    output: TextIO,
) -> None:
    if not entries:
        print(warning_text("No saved tabs yet.", stream=output), file=output)
        return
    print("", file=output)
    print(header_text("Saved tab aliases:", stream=output), file=output)
    print(label_text("This only changes codex-tabs. Codex itself is not modified.", stream=output), file=output)
    print_numbered_saved_tabs(entries, output=output)
    raw = prompt_input(input_fn, "Select a tab to delete (blank to cancel): ", output=output).strip()
    if not raw:
        print(warning_text("Canceled.", stream=output), file=output)
        return
    try:
        name = resolve_single_saved_tab_selection(raw, entries)
    except ValueError as exc:
        print(error_text(str(exc), stream=output), file=output)
        return
    if not prompt_yes_no(
        f"Delete saved tab alias {name}? This does not delete the underlying Codex session. [y/N]: ",
        input_fn=input_fn,
        default=False,
    ):
        print(warning_text("Canceled.", stream=output), file=output)
        return
    try:
        cmd_remove(entries, config_path, name)
        print(success_text(f"Deleted {name}.", stream=output), file=output)
    except ValueError as exc:
        print(error_text(str(exc), stream=output), file=output)


def parse_saved_tab_selection(
    raw: str,
    entries: dict[str, SessionEntry],
) -> list[str]:
    ordered_names = sorted(entries)
    selected: list[str] = []
    seen: set[str] = set()

    for token in raw.split():
        if token.isdigit():
            index = int(token)
            if index < 1 or index > len(ordered_names):
                raise ValueError(f"selection must be between 1 and {len(ordered_names)}")
            name = ordered_names[index - 1]
        else:
            if token not in entries:
                raise ValueError(f"unknown session name: {token}")
            name = token
        if name not in seen:
            seen.add(name)
            selected.append(name)

    if not selected:
        raise ValueError("select at least one saved tab")
    return selected


def resolve_single_saved_tab_selection(
    raw: str,
    entries: dict[str, SessionEntry],
) -> str:
    names = parse_saved_tab_selection(raw, entries)
    if len(names) != 1:
        raise ValueError("select exactly one saved tab")
    return names[0]


def prompt_yes_no(
    prompt: str,
    *,
    input_fn: Callable[[str], str],
    default: bool,
) -> bool:
    while True:
        raw = input_fn(prompt).strip().lower()
        if not raw:
            return default
        if raw in {"y", "yes"}:
            return True
        if raw in {"n", "no"}:
            return False
