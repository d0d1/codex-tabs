# Publishing

`codex-tabs` is set up for Trusted Publisher releases through GitHub Actions.

## What is configured

- `.github/workflows/publish.yml` builds the sdist and wheel
- checks the built artifacts with `twine check`
- currently publishes to TestPyPI using GitHub OIDC instead of a long-lived API token

## What you still need to configure in TestPyPI

Create the `codex-tabs` project on TestPyPI, then add a Trusted Publisher with:

- owner: `d0d1`
- repository: `codex-tabs`
- workflow name: `publish`
- environment name: `testpypi`

If you prefer, you can also configure the publisher after the first manual project creation step on TestPyPI.

## Moving from TestPyPI to PyPI

After a successful TestPyPI release:

- change the workflow environment from `testpypi` to `pypi`
- remove the TestPyPI `repository-url`
- configure the matching Trusted Publisher entry on PyPI
- publish the real release

## Release flow

Once the Trusted Publisher is configured:

1. bump the version in `pyproject.toml`
2. commit and push
3. create a GitHub release
4. the `publish` workflow will build and publish the package to TestPyPI

You can also trigger the workflow manually with `workflow_dispatch`.
