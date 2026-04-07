# codex-tabs

`codex-tabs` is a small launcher for named Codex sessions.

It keeps a registry of aliases for `codex resume <SESSION_ID>` and opens them with:

- Windows Terminal tabs on Windows/WSL
- `tmux` windows on Linux/macOS

Platform support outside Windows/WSL is implemented but not fully tested yet.

Launcher behavior is configurable. By default `codex-tabs` auto-detects the best backend for the current machine, and advanced setups can pin a launcher such as `direct` for the current terminal.

You can change persistent preferences from the interactive `Settings` menu or with `codex-tabs config set ...`.

Feature suggestions, bug reports, and platform-specific improvements are welcome in GitHub Issues or Discussions.

## Install

```bash
pipx install codex-tabs
```

## Start

```bash
codex-tabs
```

Example:

```text
Welcome to codex-tabs.
Registry: ~/.config/codex-tabs/sessions.toml
Everything here affects codex-tabs only. Your Codex setup and data stay unchanged.

What would you like to do?
[W] Open all saved tabs
[O] Open a tab
[A] Add a tab
[L] List tabs
[C] Clear the screen
[R] Rename a saved tab alias
[D] Delete a saved tab alias
[I] Ignore other untracked previous sessions
[Q] Quit

Add a tab from an unsaved Codex session.
[1] Use the most recent unsaved session
[2] Show recent unsaved sessions
[3] Search unsaved sessions
[B] Back

[1]
    last updated: 2026-03-03 09:03:01 -03 (2h 14m ago)
    cwd: /home/example/code/project

    first user message: study the project so I can ask you for help afterwards
    last user message: walk me through how to test it, step by step
    last Codex message: 1. Open the app. 2. Go to Settings. 3. ...

Select a session by number, or [M] to show more (blank to cancel):
Name this tab (leave blank to cancel):
```

## Docs

- [Installation](https://github.com/d0d1/codex-tabs/blob/main/docs/installation.md)
- [FAQ](https://github.com/d0d1/codex-tabs/blob/main/docs/faq.md)
- [Use cases](https://github.com/d0d1/codex-tabs/blob/main/docs/use-cases.md)
- [Usage](https://github.com/d0d1/codex-tabs/blob/main/docs/usage.md)
- [Platforms](https://github.com/d0d1/codex-tabs/blob/main/docs/platforms.md)
- [Privacy](https://github.com/d0d1/codex-tabs/blob/main/docs/privacy.md)
- [Publishing](https://github.com/d0d1/codex-tabs/blob/main/docs/publishing.md)
