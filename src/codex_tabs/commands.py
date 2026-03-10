from __future__ import annotations

import argparse
import sys
from pathlib import Path

from codex_tabs.codex_state import (
    enrich_threads_with_last_messages,
    load_codex_threads,
)
from codex_tabs.display import (
    filter_ignored_threads,
    print_ignored_metadata,
    print_import_candidates,
)
from codex_tabs.launchers import open_named_sessions
from codex_tabs.models import SessionEntry
from codex_tabs.registry import (
    create_example_entries,
    load_registry_data,
    normalize_tags,
    require_entry,
    validate_name,
    validate_session_id,
    write_registry,
)
from codex_tabs.style import accent_text, error_text, label_text, success_text, warning_text


def cmd_init(config_path: Path, args: argparse.Namespace) -> int:
    if config_path.exists() and not args.force:
        print(
            f"Config already exists at {config_path}. Use --force to overwrite.",
            file=sys.stderr,
        )
        return 1

    entries = {} if args.empty else create_example_entries()
    write_registry(config_path, entries)
    print(config_path)
    return 0


def cmd_list(entries: dict[str, SessionEntry], config_path: Path) -> int:
    if not entries:
        print(
            error_text(f"No sessions configured in {config_path}", stream=sys.stderr),
            file=sys.stderr,
        )
        return 1

    max_name = max(len(entry.name) for entry in entries.values())
    for name in sorted(entries):
        entry = entries[name]
        line = f"{accent_text(entry.name.ljust(max_name), stream=sys.stdout)}  {entry.session_id}"
        if entry.tags:
            line += f"  tags={','.join(entry.tags)}"
        if entry.cwd:
            line += f"  cwd={entry.cwd}"
        print(line)
        if entry.notes:
            print(
                f"{' ' * (max_name + 2)}{label_text('notes=', stream=sys.stdout)}{entry.notes}"
            )
    return 0


def cmd_show(entries: dict[str, SessionEntry], name: str) -> int:
    entry = require_entry(entries, name)
    print(f"{label_text('name:', stream=sys.stdout)} {entry.name}")
    print(f"{label_text('session_id:', stream=sys.stdout)} {entry.session_id}")
    print(f"{label_text('cwd:', stream=sys.stdout)} {entry.cwd or ''}")
    print(f"{label_text('tags:', stream=sys.stdout)} {', '.join(entry.tags)}")
    print(f"{label_text('notes:', stream=sys.stdout)} {entry.notes or ''}")
    return 0


def cmd_add(entries: dict[str, SessionEntry], config_path: Path, args: argparse.Namespace) -> int:
    name = validate_name(args.name)
    session_id = validate_session_id(args.session_id.lower())
    normalized_tags = normalize_tags(args.tags)

    entries[name] = SessionEntry(
        name=name,
        session_id=session_id,
        cwd=args.cwd,
        notes=args.notes,
        tags=normalized_tags,
    )
    write_registry(config_path, entries)
    print(success_text(f"Updated {name} in {config_path}", stream=sys.stdout))
    return 0


def cmd_remove(entries: dict[str, SessionEntry], config_path: Path, name: str) -> int:
    require_entry(entries, name)
    del entries[name]
    write_registry(config_path, entries)
    print(success_text(f"Removed {name} from {config_path}", stream=sys.stdout))
    return 0


def cmd_rename(
    entries: dict[str, SessionEntry],
    config_path: Path,
    old_name: str,
    new_name: str,
) -> int:
    entry = require_entry(entries, old_name)
    new_name = validate_name(new_name)
    if new_name in entries and new_name != old_name:
        raise ValueError(f"session name already exists: {new_name}")

    del entries[old_name]
    entry.name = new_name
    entries[new_name] = entry
    write_registry(config_path, entries)
    print(success_text(f"Renamed {old_name} to {new_name} in {config_path}", stream=sys.stdout))
    return 0


def cmd_open(entries: dict[str, SessionEntry], args: argparse.Namespace) -> int:
    wt_profile = getattr(args, "wt_profile", None)
    return open_named_sessions(
        entries,
        args.names,
        wt_profile=wt_profile,
        window=args.window,
        dry_run=args.dry_run,
    )


def cmd_ignored(
    entries: dict[str, SessionEntry],
    ignored_session_ids: set[str],
    args: argparse.Namespace,
) -> int:
    if not ignored_session_ids:
        print(warning_text("No ignored sessions.", stream=sys.stderr), file=sys.stderr)
        return 1

    threads = load_codex_threads(limit=args.limit, include_archived=True)
    enrich_threads_with_last_messages(threads)
    by_id = {thread.session_id: thread for thread in threads}

    for i, session_id in enumerate(sorted(ignored_session_ids), start=1):
        if i > 1:
            print()
        print(f"{accent_text(f'[{i}]', stream=sys.stdout)} {session_id}")
        thread = by_id.get(session_id)
        if thread:
            print_ignored_metadata(thread)
        else:
            print(
                f"    {label_text('metadata:', stream=sys.stdout)} not available in recent local Codex state"
            )
    return 0


def cmd_ignore(
    entries: dict[str, SessionEntry],
    ignored_session_ids: set[str],
    config_path: Path,
    args: argparse.Namespace,
) -> int:
    mode_count = sum(
        1
        for value in (
            args.session_id is not None,
            args.index is not None,
            args.all_untracked,
        )
        if value
    )
    if mode_count != 1:
        raise ValueError("choose exactly one of --session-id, --index, or --all-untracked")

    tracked_ids = {entry.session_id for entry in entries.values()}
    if args.session_id is not None:
        session_id = validate_session_id(args.session_id.lower())
        if session_id in tracked_ids:
            raise ValueError("cannot ignore a session that is already saved in the registry")
        ignored_session_ids.add(session_id)
        write_registry(config_path, entries, ignored_session_ids)
        print(success_text(f"Ignored {session_id}", stream=sys.stdout))
        return 0

    threads = load_codex_threads(
        limit=args.limit,
        contains=args.contains,
        include_archived=args.all,
    )
    enrich_threads_with_last_messages(threads)
    visible_threads = filter_ignored_threads(
        threads,
        ignored_session_ids=ignored_session_ids,
        include_ignored=False,
    )

    if args.index is not None:
        if args.index < 1 or args.index > len(visible_threads):
            raise ValueError(f"--index must be between 1 and {len(visible_threads)}")
        thread = visible_threads[args.index - 1]
        if thread.session_id in tracked_ids:
            raise ValueError("cannot ignore a session that is already saved in the registry")
        ignored_session_ids.add(thread.session_id)
        write_registry(config_path, entries, ignored_session_ids)
        print(success_text(f"Ignored {thread.session_id}", stream=sys.stdout))
        return 0

    candidates = [
        thread.session_id for thread in visible_threads if thread.session_id not in tracked_ids
    ]
    if not candidates:
        print(warning_text("No untracked sessions to ignore.", stream=sys.stderr), file=sys.stderr)
        return 1
    ignored_session_ids.update(candidates)
    write_registry(config_path, entries, ignored_session_ids)
    print(success_text(f"Ignored {len(candidates)} sessions.", stream=sys.stdout))
    return 0


def cmd_unignore(
    entries: dict[str, SessionEntry],
    ignored_session_ids: set[str],
    config_path: Path,
    args: argparse.Namespace,
) -> int:
    if args.all:
        ignored_session_ids.clear()
        write_registry(config_path, entries, ignored_session_ids)
        print(success_text("Removed all ignored sessions.", stream=sys.stdout))
        return 0

    if not args.session_id:
        raise ValueError("provide --session-id or --all")

    removed = 0
    for raw_session_id in args.session_id:
        session_id = validate_session_id(raw_session_id.lower())
        if session_id in ignored_session_ids:
            ignored_session_ids.remove(session_id)
            removed += 1

    write_registry(config_path, entries, ignored_session_ids)
    print(success_text(f"Removed {removed} ignored sessions.", stream=sys.stdout))
    return 0


def cmd_import(
    entries: dict[str, SessionEntry],
    ignored_session_ids: set[str],
    config_path: Path,
    args: argparse.Namespace,
) -> int:
    selected_thread = None

    if args.index is not None and args.session_id is not None:
        raise ValueError("use either --index or --session-id, not both")

    threads = load_codex_threads(
        limit=args.limit,
        contains=args.contains,
        include_archived=args.all,
    )
    enrich_threads_with_last_messages(threads)
    threads = filter_ignored_threads(
        threads,
        ignored_session_ids=ignored_session_ids,
        include_ignored=args.include_ignored,
    )

    if args.session_id:
        session_id = validate_session_id(args.session_id.lower())
        selected_thread = next(
            (thread for thread in threads if thread.session_id == session_id),
            None,
        )
        if selected_thread is None:
            threads = load_codex_threads(
                limit=max(args.limit, 200),
                contains=session_id,
                include_archived=True,
            )
            selected_thread = next(
                (thread for thread in threads if thread.session_id == session_id),
                None,
            )
        if selected_thread is None:
            raise ValueError(f"could not find Codex session: {session_id}")
    elif args.index is not None:
        if args.index < 1 or args.index > len(threads):
            raise ValueError(f"--index must be between 1 and {len(threads)}")
        selected_thread = threads[args.index - 1]

    if selected_thread is None:
        return print_import_candidates(threads)

    if not args.name:
        raise ValueError("--name is required when importing a session")

    name = validate_name(args.name)
    normalized_tags = normalize_tags(args.tags)
    entries[name] = SessionEntry(
        name=name,
        session_id=selected_thread.session_id,
        cwd=args.cwd or selected_thread.cwd or None,
        notes=args.notes,
        tags=normalized_tags,
    )
    write_registry(config_path, entries)
    print(
        success_text(
            f"Imported {selected_thread.session_id} as {name} into {config_path}",
            stream=sys.stdout,
        )
    )
    return 0


def ignore_other_untracked_previous_sessions(
    entries: dict[str, SessionEntry],
    ignored_session_ids: set[str],
    *,
    current_session_id: str,
    config_path: Path,
    limit: int = 200,
) -> int:
    tracked_ids = {entry.session_id for entry in entries.values()}
    threads = load_codex_threads(limit=limit, include_archived=False)
    enrich_threads_with_last_messages(threads)

    new_ignored = {
        thread.session_id
        for thread in threads
        if thread.session_id != current_session_id
        and thread.session_id not in tracked_ids
        and thread.session_id not in ignored_session_ids
    }
    if not new_ignored:
        return 0

    ignored_session_ids.update(new_ignored)
    write_registry(config_path, entries, ignored_session_ids)
    return len(new_ignored)
