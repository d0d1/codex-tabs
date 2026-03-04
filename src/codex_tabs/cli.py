from __future__ import annotations

import argparse
import sys

from codex_tabs.codex_state import (
    enrich_threads_with_last_messages,
    load_codex_threads,
    load_codex_threads_by_session_ids,
    search_codex_threads,
)
from codex_tabs.commands import (
    cmd_add,
    cmd_ignore,
    cmd_ignored,
    cmd_import,
    cmd_init,
    cmd_list,
    cmd_open,
    cmd_remove,
    cmd_rename,
    cmd_show,
    cmd_unignore,
    ignore_other_untracked_previous_sessions,
)
from codex_tabs.display import (
    filter_ignored_threads,
    print_import_candidates,
    print_numbered_saved_tabs,
    print_thread_details,
)
from codex_tabs.formatting import format_relative_age, format_timestamp
from codex_tabs.launchers import (
    build_tmux_commands,
    build_wt_command,
    detect_launcher_backend,
    open_named_sessions,
)
from codex_tabs.models import CodexThread, RegistryData, SessionEntry
from codex_tabs.registry import (
    create_example_entries,
    get_config_path,
    load_ignored_session_ids,
    load_registry,
    load_registry_data,
    normalize_name,
    normalize_tags,
    validate_name,
    validate_session_id,
    write_registry,
)
from codex_tabs.wizard import (
    browse_recent_threads,
    handle_wizard_add,
    parse_saved_tab_selection,
    prompt_main_action,
    resolve_single_saved_tab_selection,
    run_wizard,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="codex-tabs")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("list", help="List configured named sessions")

    show_parser = subparsers.add_parser("show", help="Show one named session")
    show_parser.add_argument("name", help="Session name")

    open_parser = subparsers.add_parser("open", help="Open one or more named sessions")
    open_parser.add_argument("names", nargs="+", help="Session names to open")
    open_parser.add_argument(
        "--window",
        default="last",
        choices=["0", "last", "new"],
        help="Windows Terminal window target when using the wt launcher",
    )
    open_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the generated launcher command(s) without executing them",
    )

    add_parser = subparsers.add_parser("add", help="Add or update a named session")
    add_parser.add_argument("--name", required=True, help="Alias name")
    add_parser.add_argument("--session-id", required=True, help="Codex session ID")
    add_parser.add_argument("--cwd", help="Working directory for the session")
    add_parser.add_argument("--notes", help="Optional notes")
    add_parser.add_argument(
        "--tag",
        dest="tags",
        action="append",
        default=[],
        help="Tag to attach to the session; repeatable",
    )

    remove_parser = subparsers.add_parser("remove", help="Remove a named session")
    remove_parser.add_argument("name", help="Session name")

    rename_parser = subparsers.add_parser("rename", help="Rename a named session")
    rename_parser.add_argument("old_name", help="Existing session name")
    rename_parser.add_argument("new_name", help="New session name")

    ignored_parser = subparsers.add_parser(
        "ignored",
        help="List sessions ignored by codex-tabs discovery",
    )
    ignored_parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="How many ignored sessions to describe when metadata is available",
    )

    ignore_parser = subparsers.add_parser(
        "ignore",
        help="Hide sessions from codex-tabs discovery without changing Codex itself",
    )
    ignore_parser.add_argument("--session-id", help="Ignore a specific Codex session ID")
    ignore_parser.add_argument(
        "--index",
        type=int,
        help="1-based index from the recent-session list to ignore",
    )
    ignore_parser.add_argument(
        "--all-untracked",
        action="store_true",
        help="Ignore all recent sessions that are not already saved aliases",
    )
    ignore_parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="How many recent sessions to inspect",
    )
    ignore_parser.add_argument(
        "--contains",
        help="Filter recent sessions by text in id, title, cwd, or first message",
    )
    ignore_parser.add_argument(
        "--all",
        action="store_true",
        help="Include archived Codex sessions when selecting candidates",
    )

    unignore_parser = subparsers.add_parser(
        "unignore",
        help="Remove sessions from codex-tabs ignore tracking",
    )
    unignore_parser.add_argument(
        "--session-id",
        action="append",
        default=[],
        help="Ignored session ID to restore; repeatable",
    )
    unignore_parser.add_argument(
        "--all",
        action="store_true",
        help="Remove all ignored sessions from codex-tabs tracking",
    )

    import_parser = subparsers.add_parser(
        "import",
        help="Browse recent Codex sessions and import one into the registry",
    )
    import_parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="How many recent sessions to inspect",
    )
    import_parser.add_argument(
        "--contains",
        help="Filter recent sessions by text in id, title, cwd, or first message",
    )
    import_parser.add_argument(
        "--all",
        action="store_true",
        help="Include archived Codex sessions",
    )
    import_parser.add_argument(
        "--include-ignored",
        action="store_true",
        help="Include sessions previously ignored by codex-tabs",
    )
    import_parser.add_argument(
        "--index",
        type=int,
        help="1-based index from the printed recent-session list to import",
    )
    import_parser.add_argument(
        "--session-id",
        help="Import a specific Codex session ID directly",
    )
    import_parser.add_argument("--name", help="Alias name to store in codex-tabs")
    import_parser.add_argument("--cwd", help="Override the imported working directory")
    import_parser.add_argument("--notes", help="Optional notes for the imported alias")
    import_parser.add_argument(
        "--tag",
        dest="tags",
        action="append",
        default=[],
        help="Tag to attach to the imported session; repeatable",
    )

    init_parser = subparsers.add_parser("init", help="Create an initial config file")
    init_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing config file",
    )
    init_parser.add_argument(
        "--empty",
        action="store_true",
        help="Create an empty registry instead of example entries",
    )

    config_parser = subparsers.add_parser("config", help="Print the active config path")
    config_parser.add_argument(
        "--ensure-example",
        action="store_true",
        help="Create an example config if one does not exist",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        return run_wizard()

    parser = build_parser()
    args = parser.parse_args(argv)
    config_path = get_config_path()

    try:
        if args.command == "config":
            if args.ensure_example and not config_path.exists():
                write_registry(config_path, create_example_entries())
            print(config_path)
            return 0

        if args.command == "init":
            return cmd_init(config_path, args)

        registry = load_registry_data(config_path)
        entries = registry.sessions
        ignored_session_ids = registry.ignored_session_ids

        if args.command == "list":
            return cmd_list(entries, config_path)
        if args.command == "show":
            return cmd_show(entries, args.name)
        if args.command == "add":
            return cmd_add(entries, config_path, args)
        if args.command == "remove":
            return cmd_remove(entries, config_path, args.name)
        if args.command == "rename":
            return cmd_rename(entries, config_path, args.old_name, args.new_name)
        if args.command == "ignored":
            return cmd_ignored(entries, ignored_session_ids, args)
        if args.command == "ignore":
            return cmd_ignore(entries, ignored_session_ids, config_path, args)
        if args.command == "unignore":
            return cmd_unignore(entries, ignored_session_ids, config_path, args)
        if args.command == "import":
            return cmd_import(entries, ignored_session_ids, config_path, args)
        if args.command == "open":
            return cmd_open(entries, args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    parser.error(f"unknown command: {args.command}")
    return 2


__all__ = [
    "CodexThread",
    "RegistryData",
    "SessionEntry",
    "browse_recent_threads",
    "build_parser",
    "build_tmux_commands",
    "build_wt_command",
    "create_example_entries",
    "detect_launcher_backend",
    "enrich_threads_with_last_messages",
    "filter_ignored_threads",
    "format_relative_age",
    "format_timestamp",
    "get_config_path",
    "handle_wizard_add",
    "ignore_other_untracked_previous_sessions",
    "load_codex_threads",
    "load_codex_threads_by_session_ids",
    "load_ignored_session_ids",
    "load_registry",
    "load_registry_data",
    "main",
    "normalize_name",
    "normalize_tags",
    "open_named_sessions",
    "parse_saved_tab_selection",
    "print_import_candidates",
    "print_numbered_saved_tabs",
    "print_thread_details",
    "prompt_main_action",
    "resolve_single_saved_tab_selection",
    "run_wizard",
    "search_codex_threads",
    "validate_name",
    "validate_session_id",
    "write_registry",
]
