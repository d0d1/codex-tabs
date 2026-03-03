# Installation

## Recommended

```bash
pipx install git+https://github.com/d0d1/codex-tabs.git
```

Update an existing install:

```bash
pipx upgrade codex-tabs
```

If you want to force-refresh directly from the latest GitHub state:

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
