from __future__ import annotations

import json
import os
import shutil
import subprocess
import uuid
from pathlib import Path

from codex_tabs.registry import load_registry_data, write_registry


WT_SETTINGS_SUFFIX = Path(
    "Packages/Microsoft.WindowsTerminal_8wekyb3d8bbwe/LocalState/settings.json"
)
DEFAULT_WT_ADMIN_PROFILE = "Codex Tabs (Admin)"


def detect_windows_admin_context() -> bool:
    if not os.environ.get("WSL_DISTRO_NAME"):
        return False

    shell = shutil.which("powershell.exe") or shutil.which("pwsh.exe")
    if shell is None:
        return False

    command = (
        "[bool](([Security.Principal.WindowsPrincipal]"
        "[Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole("
        "[Security.Principal.WindowsBuiltInRole]::Administrator))"
    )
    completed = subprocess.run(
        [shell, "-NoProfile", "-Command", command],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return False
    return completed.stdout.strip().lower() == "true"


def get_wt_settings_path() -> Path | None:
    override = os.environ.get("CODEX_TABS_WT_SETTINGS_PATH")
    if override:
        return Path(override).expanduser()

    shell = shutil.which("powershell.exe") or shutil.which("pwsh.exe")
    wslpath = shutil.which("wslpath")
    if shell is None or wslpath is None:
        return None

    completed = subprocess.run(
        [shell, "-NoProfile", "-Command", "$env:LOCALAPPDATA"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return None

    windows_path = completed.stdout.strip()
    if not windows_path:
        return None

    translated = subprocess.run(
        [wslpath, "-u", windows_path],
        check=False,
        capture_output=True,
        text=True,
    )
    if translated.returncode != 0:
        return None

    return Path(translated.stdout.strip()) / WT_SETTINGS_SUFFIX


def load_wt_settings(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_wt_settings(path: Path, settings: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4)
        f.write("\n")


def find_wt_profile(settings: dict, profile_name: str) -> dict | None:
    profiles = settings.get("profiles", {})
    if not isinstance(profiles, dict):
        return None
    profile_list = profiles.get("list", [])
    if not isinstance(profile_list, list):
        return None
    for profile in profile_list:
        if isinstance(profile, dict) and profile.get("name") == profile_name:
            return profile
    return None


def configured_wt_profile_name(registry_wt_profile: str | None) -> str | None:
    return os.environ.get("CODEX_TABS_WT_PROFILE") or registry_wt_profile


def has_valid_wt_profile_setup(registry_wt_profile: str | None) -> bool:
    profile_name = configured_wt_profile_name(registry_wt_profile)
    if not profile_name:
        return False
    settings_path = get_wt_settings_path()
    if settings_path is None or not settings_path.exists():
        return False
    settings = load_wt_settings(settings_path)
    profile = find_wt_profile(settings, profile_name)
    return isinstance(profile, dict) and bool(profile.get("elevate"))


def ensure_admin_profile(settings: dict, *, profile_name: str, distro: str) -> bool:
    profiles = settings.setdefault("profiles", {})
    profile_list = profiles.setdefault("list", [])
    if not isinstance(profile_list, list):
        raise ValueError("Windows Terminal settings.json has an unexpected profiles.list format")

    guid = "{" + str(uuid.uuid5(uuid.NAMESPACE_URL, f"codex-tabs:{distro}:admin")) + "}"
    desired = {
        "commandline": f"wsl.exe -d {distro}",
        "elevate": True,
        "guid": guid,
        "hidden": False,
        "name": profile_name,
    }

    profile = find_wt_profile(settings, profile_name)
    if profile is None:
        profile_list.append(desired)
        return True

    changed = False
    for key, value in desired.items():
        if profile.get(key) != value:
            profile[key] = value
            changed = True
    return changed


def setup_wt_admin(config_path: Path) -> tuple[str, bool, Path]:
    if not os.environ.get("WSL_DISTRO_NAME"):
        raise ValueError("setup-wt-admin only works from WSL.")

    settings_path = get_wt_settings_path()
    if settings_path is None:
        raise ValueError("Windows Terminal settings.json could not be located from this shell.")

    settings = load_wt_settings(settings_path) if settings_path.exists() else {}
    distro = os.environ.get("WSL_DISTRO_NAME", "Ubuntu")
    profile_name = DEFAULT_WT_ADMIN_PROFILE
    changed = ensure_admin_profile(settings, profile_name=profile_name, distro=distro)
    if changed or not settings_path.exists():
        write_wt_settings(settings_path, settings)

    registry = load_registry_data(config_path)
    write_registry(
        config_path,
        registry.sessions,
        registry.ignored_session_ids,
        wt_profile=profile_name,
    )
    return profile_name, changed, settings_path
