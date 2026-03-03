# Installation

## Recommended

```bash
pipx install codex-tabs
```

Update an existing install:

```bash
pipx upgrade codex-tabs
```

## Install from GitHub

If you want the latest unreleased GitHub state instead of the published PyPI package:

```bash
pipx install --force git+https://github.com/d0d1/codex-tabs.git
```

## Local development

```bash
git clone https://github.com/d0d1/codex-tabs.git
cd codex-tabs
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
```

## Config path

Default registry path:

```text
~/.config/codex-tabs/sessions.toml
```

Override it with:

```bash
export CODEX_TABS_CONFIG=/path/to/sessions.toml
```
