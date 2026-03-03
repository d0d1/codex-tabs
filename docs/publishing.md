# Publishing

`codex-tabs` is set up for PyPI Trusted Publisher releases through GitHub Actions.

## What is configured

- `.github/workflows/publish.yml` builds the sdist and wheel
- checks the built artifacts with `twine check`
- publishes to PyPI using GitHub OIDC instead of a long-lived API token

## What you still need to configure in PyPI

Create the `codex-tabs` project on PyPI, then add a Trusted Publisher with:

- owner: `d0d1`
- repository: `codex-tabs`
- workflow name: `publish`
- environment name: `pypi`

If you prefer, you can also configure the publisher after the first manual project creation step on PyPI.

## Release flow

Once the Trusted Publisher is configured:

1. bump the version in `pyproject.toml`
2. commit and push
3. create a GitHub release
4. the `publish` workflow will build and publish the package to PyPI

You can also trigger the workflow manually with `workflow_dispatch`.
