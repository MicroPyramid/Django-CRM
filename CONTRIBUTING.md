# Contributing to BottleCRM

Thank you for helping improve BottleCRM. Contributions of all sizes are welcome, including bug fixes, features, tests, documentation, and accessibility improvements.

## Before You Start

- Search the [existing issues](https://github.com/django-crm/Django-CRM/issues) before opening a new one.
- For a substantial feature or architectural change, open an issue first so the approach can be discussed before implementation begins.
- Keep pull requests focused. Unrelated changes are easier to review when submitted separately.

## Development Setup

Full instructions (cloning, Docker, the backend (`uv`), the frontend (`pnpm`), running the mobile app, adding dependencies, and running tests) live in the documentation site under Contributing:

- [Development setup](docs/contributing/development-setup.md). Get all three projects running locally.
- [Testing](docs/contributing/testing.md), running the suite, markers, and what CI runs.
- [Code style](docs/contributing/code-style.md), Python, frontend, and Flutter conventions, and what CI does and doesn't enforce.
- [Repository layout](docs/contributing/repo-layout.md), where each part of the codebase lives.
- [Security rules](docs/contributing/security-rules.md). The rules this codebase treats as non-negotiable.
- [Adding an org-scoped model](docs/contributing/adding-an-org-scoped-model.md). What a new multi-tenant model needs, including its RLS policy.

## Submitting a Pull Request

1. Create a branch from `master` with a descriptive name.
2. Make focused changes and include tests where appropriate.
3. Run the relevant development checks. See [Testing](docs/contributing/testing.md) and [Code style](docs/contributing/code-style.md).
4. Update documentation when behavior, setup, or public APIs change.
5. Push your branch and open a pull request against `master`.

In the pull request description, explain what changed, why it changed, how it was tested, and include screenshots for visible UI changes. See [Pull requests](docs/contributing/pull-requests.md) for what CI runs and what review focuses on.

## Pull Request Checklist

- [ ] The change is focused and does not include unrelated edits.
- [ ] Relevant backend and frontend checks pass.
- [ ] Tests cover new or changed behavior where practical.
- [ ] Required migrations are included.
- [ ] Documentation is updated.
- [ ] No credentials, tokens, or private data are committed.
