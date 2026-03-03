# Contributing

## Development setup

```bash
git clone https://github.com/d0d1/codex-tabs.git
cd codex-tabs
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
```

## Run tests

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## Notes

- Windows/WSL is the primary tested launcher path.
- Linux/macOS support is implemented through `tmux`, but should be treated as lightly tested unless explicitly verified. Linux/macOS tests and contributions are welcome.

## Commits

Please use Conventional Commits where practical:

- https://www.conventionalcommits.org/

Examples:

- `feat: add tmux launcher backend`
- `fix: handle empty recent-session search`
- `docs: refresh installation guidance`
