# Platforms

## Windows / WSL

Primary supported path.

`codex-tabs` uses Windows Terminal tab spawning through `wt.exe`.

Expected environment:

- Codex running inside WSL
- Windows Terminal available as `wt.exe`

Default behavior:

- `codex-tabs` opens Windows Terminal tabs
- if you are in an elevated Windows Terminal WSL session, `codex-tabs` can offer elevated-launch setup automatically
- if you prefer not to open tabs, set `launcher = "direct"` in the registry or pass `--launcher direct`

Elevated/admin setup:

```bash
codex-tabs setup-wt-admin
```

This creates an elevated Windows Terminal profile and saves it in the `codex-tabs` registry as `wt_profile`.

For elevated/admin workflows on Windows Terminal:

- `codex-tabs` can target an elevated profile once it is configured
- Windows Terminal may still open a separate elevated window instead of adding a tab to the current window
- the important outcome is that the launched Codex session can run elevated

Advanced override:

If `CODEX_TABS_WT_PROFILE` is set, `codex-tabs` opens Windows Terminal tabs with that profile:

```bash
export CODEX_TABS_WT_PROFILE="Ubuntu (Admin)"
```

This overrides the profile saved in the `codex-tabs` registry and is mainly useful for advanced setups.

## Linux / macOS

Implemented, but not fully tested yet.

`codex-tabs` defaults to `tmux` as the launcher backend.

Behavior:

- inside `tmux`: opens new windows in the current session
- outside `tmux`: creates a new `tmux` session, opens the requested windows, and attaches to it
- if you prefer to reopen a single session in the current terminal, use `launcher = "direct"` or `codex-tabs open <name> --launcher direct`

## Notes

- The session registry, import flow, search flow, ignore flow, and wizard are OS-agnostic.
- The launcher backend is the platform-specific part.
- `codex-tabs open --window ...` only affects the Windows Terminal backend.
- `launcher = "direct"` is useful over SSH or in terminals where tmux/window management is not desirable.
