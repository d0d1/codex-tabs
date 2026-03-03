# Platforms

## Windows / WSL

Primary supported path.

`codex-tabs` uses Windows Terminal tab spawning through `wt.exe`.

Expected environment:

- Codex running inside WSL
- Windows Terminal available as `wt.exe`

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
