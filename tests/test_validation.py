from __future__ import annotations

import unittest

from codex_tabs.cli import normalize_name, normalize_tags, validate_name, validate_session_id


class ValidationTests(unittest.TestCase):
    def test_validate_name_accepts_expected_format(self) -> None:
        self.assertEqual(validate_name("work.main"), "work.main")

    def test_validate_name_normalizes_common_input(self) -> None:
        self.assertEqual(validate_name("Work Main"), "work-main")

    def test_validate_name_rejects_non_names(self) -> None:
        with self.assertRaises(ValueError):
            validate_name("!!!")

    def test_normalize_name_slugifies_friendly_input(self) -> None:
        self.assertEqual(normalize_name(" Obsidian Notes "), "obsidian-notes")

    def test_validate_session_id_accepts_uuid_like_value(self) -> None:
        value = "01234567-89ab-cdef-0123-456789abcdef"
        self.assertEqual(validate_session_id(value), value)

    def test_validate_session_id_rejects_invalid_value(self) -> None:
        with self.assertRaises(ValueError):
            validate_session_id("not-a-session-id")

    def test_normalize_tags_deduplicates_and_lowercases(self) -> None:
        self.assertEqual(
            normalize_tags(["Work", "work", " notes ", ""]),
            ["work", "notes"],
        )
