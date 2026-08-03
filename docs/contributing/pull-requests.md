# Pull requests

## Before you open one

`CONTRIBUTING.md` (repo root) lays out the process this page assumes: branch from `master` with a
descriptive name, keep the change focused rather than mixing in unrelated edits, include tests where
practical, and update documentation when behavior, setup, or a public API changes. Its own checklist
is worth re-reading right before you open a PR:

- The change is focused and does not include unrelated edits.
- Relevant backend and frontend checks pass. See [Development setup](development-setup.md) and
  [Testing](testing.md) for what to run locally before pushing.
- Tests cover new or changed behavior where practical. See
  [Security rules](security-rules.md#prove-permission-checks-can-fail) specifically if the change
  touches a permission check.
- Required migrations are included. See [What CI runs](#what-ci-runs) below for what happens if
  one is missing.
- Documentation is updated.
- No credentials, tokens, or private data are committed.

In the PR description itself: explain what changed and why, how you tested it, and include
screenshots for any visible UI change.

## What CI runs

`.github/workflows/tests.yml` defines three jobs, `backend-tests`, `frontend-checks`, and
`docs-build`: triggered by two events, both scoped to the same path list (`backend/`, `frontend/`,
`docs/`, `mkdocs.yml`, `.readthedocs.yaml`, `.coveragerc`, or the workflow file itself): a pull
request against `master`, or a **push to `master` specifically** (`branches: [master]` on the `push`
trigger). Pushing a feature branch on its own doesn't run any of this. You'll only see these jobs
once you open the PR against `master`, so don't expect CI feedback from `git push` alone.

**`backend-tests`** installs WeasyPrint's system libraries, runs `uv sync --frozen` (installing
exactly what's locked in `uv.lock`, no re-resolution), then two steps in order:

```bash
uv run python manage.py makemigrations --check --dry-run
uv run pytest -m "not postgres_only" --tb=short -v
```

**A model change without a matching migration fails the first step**, before the test suite even
runs; `makemigrations --check --dry-run` exits non-zero if Django's autodetector finds any model
change that isn't already captured in a migration file. Generate and commit the migration
(`uv run python manage.py makemigrations`) before you push. See [Testing](testing.md#what-ci-runs)
for what the test step does and doesn't cover. Notably, this job runs on SQLite, so it exercises no
RLS policy regardless of what you changed. On a push to `master` (not on pull requests) this job
additionally regenerates and commits a coverage badge.

**`frontend-checks`** installs with `pnpm install --frozen-lockfile`, then runs a Prettier check (a
formatting difference is reported as a warning, not a failure: see
[Code style](code-style.md#frontend)), `pnpm eslint .` (this one does fail the job), `pnpm check`
(svelte-check), and finally `pnpm build`.

**`docs-build`** installs the `docs` dependency group (`uv sync --frozen --group docs`) and runs

```bash
uv run mkdocs build --strict -f ../mkdocs.yml -d site
```

`--strict` fails the build on a broken nav entry or a broken internal link target that doesn't
exist. A second step then runs `common/tests/test_docs_build_excludes_internal.py`, which rebuilds
the site again and asserts that nothing under `docs/superpowers/` or `docs/design/`, internal specs
and plans, excluded via `exclude_docs` in `mkdocs.yml`. Ends up published in the output. If you add
a documentation page, `mkdocs build --strict` is the same command you can run locally first; see
[Development setup](development-setup.md#backend) for the `uv run --group docs` invocation.

## Review expectations

Backend Python style is not enforced by CI (see [Code style](code-style.md#python) for why). A
reviewer may still ask you to match the surrounding file's formatting even though no bot will flag
it automatically. Frontend style mostly is enforced (ESLint failures and type errors block the
build; Prettier differences only warn). Flutter has no CI at all, so `dart format .` and `flutter
analyze` before opening a PR are the only check that happens for mobile changes.

Beyond style, expect review to focus on the two things this codebase treats as non-negotiable: every
new or changed queryset filtering by `org=request.profile.org` (or being covered by RLS with a test
proving it. See [Adding an org-scoped model](adding-an-org-scoped-model.md)), and every new or
changed permission check being provable in both directions. See
[Security rules](security-rules.md#prove-permission-checks-can-fail). A PR that adds an endpoint
without a test for the rejected/forbidden path, not just the happy path, is the single most common
thing to get asked to add here.
