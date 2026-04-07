# FAQ

## How do I reopen a Codex session by name?

Save the session as a tab alias in `codex-tabs`, then reopen it with:

```bash
codex-tabs open your-tab-name
```

## How do I manage multiple Codex sessions?

Use the wizard to save recurring sessions as named tabs, then open one or many of them from the same registry.

Examples:

- open one saved tab
- open all saved tabs
- keep separate named sessions for different projects

## How do I open Codex sessions in separate terminal tabs?

`codex-tabs` reopens saved sessions with the terminal backend for your platform:

- Windows/WSL: Windows Terminal tabs
- Linux/macOS: `tmux` windows

If you want to reopen one session in the current terminal instead, use:

```bash
codex-tabs open your-tab-name --launcher direct
```

To make that the default, either use the interactive `Settings` menu in `codex-tabs` or run:

```bash
codex-tabs config set launcher direct
```

The registry will then contain:

```toml
launcher = "direct"
```

## How do I open Codex sessions elevated on Windows/WSL?

Run:

```bash
codex-tabs setup-wt-admin
```

Or, if you start `codex-tabs` from an elevated Windows Terminal WSL session, accept the automatic setup prompt.

After that, `codex-tabs` can target an elevated Windows Terminal profile for launched sessions.

## How do I find an existing Codex session without remembering its ID?

Use the wizard:

```bash
codex-tabs
```

Then choose one of the add-flow options to:

- use the most recent unsaved session
- browse recent unsaved sessions
- search unsaved sessions from local Codex history

## How do I keep old Codex sessions from cluttering discovery?

Use the main menu action:

- `Ignore other untracked previous sessions`

This hides older untracked sessions from future discovery without changing Codex itself.

## Does codex-tabs change Codex data?

No. `codex-tabs` manages its own registry and discovery filters. It does not modify Codex itself.

## Is codex-tabs a multi-agent orchestrator?

No. `codex-tabs` is a small session launcher and registry for named Codex sessions. It is not a worktree manager or multi-agent orchestration tool.
