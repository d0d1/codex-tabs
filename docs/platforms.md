# Platforms

## Windows / WSL

Primary supported path.

`codex-tabs` uses Windows Terminal tab spawning through `wt.exe`.

Expected environment:

- Codex running inside WSL
- Windows Terminal available as `wt.exe`

Optional configuration:

- `CODEX_TABS_WT_PROFILE`

If `CODEX_TABS_WT_PROFILE` is set, `codex-tabs` opens Windows Terminal tabs with that profile:

```bash
export CODEX_TABS_WT_PROFILE="Ubuntu (Admin)"
```

This is useful when you want `codex-tabs` to target a specific Windows Terminal profile, including a profile configured with `elevate: true`.

For elevated/admin workflows on Windows Terminal:

- `codex-tabs` can target an elevated profile if you configure one
- Windows Terminal may still open a separate elevated window instead of adding a tab to the current window
- the important outcome is that the launched Codex session can run elevated

## Linux / macOS

Implemented, but not fully tested yet.

`codex-tabs` uses `tmux` as the launcher backend.

Behavior:

- inside `tmux`: opens new windows in the current session
- outside `tmux`: creates a new `tmux` session, opens the requested windows, and attaches to it

## Notes

- The session registry, import flow, search flow, ignore flow, and wizard are OS-agnostic.
- The launcher backend is the platform-specific part.
- `codex-tabs open --window ...` only affects the Windows Terminal backend.
