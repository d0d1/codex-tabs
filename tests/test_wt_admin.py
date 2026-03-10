from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from codex_tabs.registry import load_registry_data
from codex_tabs.wt_admin import (
    DEFAULT_WT_ADMIN_PROFILE,
    has_valid_wt_profile_setup,
    setup_wt_admin,
)


class WindowsAdminSetupTests(unittest.TestCase):
    def test_setup_wt_admin_creates_profile_and_registry_setting(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config_path = tmp_path / "sessions.toml"
            settings_path = tmp_path / "settings.json"
            settings_path.write_text(
                json.dumps({"profiles": {"defaults": {}, "list": []}}, indent=4) + "\n",
                encoding="utf-8",
            )

            env = {
                "WSL_DISTRO_NAME": "Ubuntu",
                "CODEX_TABS_WT_SETTINGS_PATH": str(settings_path),
            }
            with patch.dict(os.environ, env, clear=False):
                profile_name, changed, returned_settings_path = setup_wt_admin(config_path)

            self.assertEqual(profile_name, DEFAULT_WT_ADMIN_PROFILE)
            self.assertTrue(changed)
            self.assertEqual(returned_settings_path, settings_path)

            settings = json.loads(settings_path.read_text(encoding="utf-8"))
            profile = next(
                profile
                for profile in settings["profiles"]["list"]
                if profile["name"] == DEFAULT_WT_ADMIN_PROFILE
            )
            self.assertEqual(profile["commandline"], "wsl.exe -d Ubuntu")
            self.assertTrue(profile["elevate"])

            registry = load_registry_data(config_path)
            self.assertEqual(registry.wt_profile, DEFAULT_WT_ADMIN_PROFILE)

    def test_has_valid_wt_profile_setup_checks_registry_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            settings_path = Path(tmp) / "settings.json"
            settings_path.write_text(
                json.dumps(
                    {
                        "profiles": {
                            "defaults": {},
                            "list": [
                                {
                                    "name": DEFAULT_WT_ADMIN_PROFILE,
                                    "commandline": "wsl.exe -d Ubuntu",
                                    "elevate": True,
                                }
                            ],
                        }
                    },
                    indent=4,
                )
                + "\n",
                encoding="utf-8",
            )

            env = {
                "CODEX_TABS_WT_SETTINGS_PATH": str(settings_path),
            }
            with patch.dict(os.environ, env, clear=False):
                self.assertTrue(has_valid_wt_profile_setup(DEFAULT_WT_ADMIN_PROFILE))
