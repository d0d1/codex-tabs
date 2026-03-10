# Usage

## Wizard

Run:

```bash
codex-tabs
```

The wizard is the main entrypoint. It can:

- discover recent Codex sessions
- search local Codex history
- save named aliases
- open one or many saved aliases
- rename or delete saved aliases
- ignore other untracked previous sessions from future discovery
- offer elevated Windows Terminal setup automatically when launched from an elevated Windows/WSL session

## CLI

Useful commands:

```bash
codex-tabs list
codex-tabs show personal
codex-tabs open personal
codex-tabs open personal work
codex-tabs add --name ideas --session-id 01234567-89ab-cdef-0123-456789abcdef
codex-tabs rename ideas inbox
codex-tabs remove inbox
codex-tabs import
codex-tabs import --index 1 --name personal
codex-tabs ignore --all-untracked
codex-tabs ignored
codex-tabs unignore --all
codex-tabs setup-wt-admin
```

## Registry format

Example:

```toml
wt_profile = "Codex Tabs (Admin)"

ignored_session_ids = [
  "fedcba98-7654-3210-fedc-ba9876543210",
]

[sessions.personal]
session_id = "01234567-89ab-cdef-0123-456789abcdef"
cwd = "/home/example/notes"
notes = "Personal knowledge base"
tags = ["notes", "personal"]

[sessions.work]
session_id = "89abcdef-0123-4567-89ab-cdef01234567"
cwd = "/home/example/code/project"
notes = "Main work project"
tags = ["project", "work"]
```
