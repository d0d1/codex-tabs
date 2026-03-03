# Privacy

`codex-tabs` collects no telemetry or user data.

It works only with local files and local commands on your machine.

## What it reads

- the local registry file under `~/.config/codex-tabs/`
- local Codex state under `~/.codex/`
- local Codex session transcript files under `~/.codex/sessions/`

## What it does not do

- no analytics
- no telemetry
- no remote API calls
- no background service
- no uploading of session content

## Platform launchers

To reopen sessions, `codex-tabs` can invoke:

- `wt.exe` on Windows/WSL
- `tmux` on Linux/macOS

Those launchers run locally on your machine.
