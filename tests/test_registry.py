from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from codex_tabs.cli import (
    RegistryData,
    SessionEntry,
    create_example_entries,
    load_ignored_session_ids,
    load_registry,
    load_registry_data,
    write_registry,
)


class RegistryTests(unittest.TestCase):
    def test_write_and_load_registry_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sessions.toml"
            entries = {
                "work": SessionEntry(
                    name="work",
                    session_id="89abcdef-0123-4567-89ab-cdef01234567",
                    cwd="/home/example/project",
                    notes="Main project",
                    tags=["project", "work"],
                ),
                "personal": SessionEntry(
                    name="personal",
                    session_id="01234567-89ab-cdef-0123-456789abcdef",
                    notes="Personal notes",
                ),
            }

            write_registry(path, entries)
            loaded = load_registry(path)

            self.assertEqual(set(loaded), {"personal", "work"})
            self.assertEqual(loaded["work"].cwd, "/home/example/project")
            self.assertEqual(loaded["work"].tags, ["project", "work"])
            self.assertEqual(loaded["personal"].notes, "Personal notes")

    def test_write_and_load_registry_preserves_ignored_session_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sessions.toml"
            entries = {
                "personal": SessionEntry(
                    name="personal",
                    session_id="01234567-89ab-cdef-0123-456789abcdef",
                )
            }
            ignored = {"89abcdef-0123-4567-89ab-cdef01234567"}

            write_registry(path, entries, ignored)
            registry = load_registry_data(path)

            self.assertEqual(set(registry.sessions), {"personal"})
            self.assertEqual(registry.ignored_session_ids, ignored)
            self.assertEqual(load_ignored_session_ids(path), ignored)

    def test_create_example_entries_is_generic(self) -> None:
        entries = create_example_entries()
        self.assertEqual(set(entries), {"personal", "work"})
        self.assertIn("Replace with a real session ID", entries["personal"].notes)


class RegistryMutationTests(unittest.TestCase):
    def test_rename_style_mutation_is_round_trippable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sessions.toml"
            entries = {
                "old-name": SessionEntry(
                    name="old-name",
                    session_id="01234567-89ab-cdef-0123-456789abcdef",
                    tags=["a"],
                )
            }

            write_registry(path, entries)
            loaded = load_registry(path)
            entry = loaded.pop("old-name")
            entry.name = "new-name"
            loaded["new-name"] = entry
            write_registry(path, loaded)

            reloaded = load_registry(path)
            self.assertNotIn("old-name", reloaded)
            self.assertEqual(reloaded["new-name"].name, "new-name")
            self.assertEqual(reloaded["new-name"].tags, ["a"])
