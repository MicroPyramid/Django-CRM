# Code style

## Python

`backend/ruff.toml` exists and is a real, checked-in configuration:

```toml
indent-width = 4

[format]
indent-style = "space"
line-ending = "lf"
quote-style = "double"

[lint]
select = ["E", "F", "I"]
ignore = ["E501"]
```

That selects pycodestyle errors (`E`), pyflakes (`F`), and import sorting (`I`), and explicitly
ignores line-length (`E501`), so this project has decided not to enforce a line-length limit, not
that it forgot to.

`ruff` is the only Python style tool here, and it is a real dev dependency, so `uv sync` installs
it and these commands work on a fresh clone:

```bash
cd backend
uv run ruff check .          # lint: E, F, I as ruff.toml selects them
uv run ruff check --fix .    # and fix what is safely fixable
uv run ruff format .         # format the tree
uv run ruff format --check . # or just report, which is what CI runs
```

**There is no `black` and no `isort`.** `ruff format` is a reimplementation of black and produces
the same output, and ruff's `I` rules do isort's job, so all three would be doing one job with two
of them redundant, and black and `ruff format` can disagree at the edges. Older docs and habits
name `uv run black . && uv run isort .`; neither is installed and neither should be added.

**CI runs both, and both must pass.** `.github/workflows/tests.yml` runs `uv run ruff check .` and
`uv run ruff format --check .` as hard steps, not warnings. `uv run` rather than `uvx` on purpose:
ruff is pinned in `uv.lock`, so your machine and CI check against one version and a ruff release
cannot turn the build red overnight.

**The tree conforms.** It was formatted in full on 2026-08-07 (205 files) with imports sorted in
112 more, so `ruff format .` on a clean checkout changes nothing and your diff stays your diff.
That is the point of formatting everything at once: before it, running the formatter across the
tree turned any focused PR into an unreviewable one, which is why the old advice here was to scope
`uvx` to the files you touched. That advice no longer applies. Run the commands above on the whole
tree and commit only what you meant to change.

One thing worth knowing before you run `--fix` over code you did not write: a `# noqa` binds to the
line ruff reports the diagnostic on, so a suppression that has drifted onto the next line, or that
names the wrong rule code, silently suppresses nothing, and the autofix will then delete what it
was protecting. `common/models.py`'s `SecurityAuditLog` import is the live example: it exists only
so Django discovers the model for migrations, and its `# noqa: F401,E402` has to sit on the same
line as the imported name.

## Frontend

`frontend/package.json` defines the real commands:

```bash
pnpm run lint     # prettier --check . && eslint .
pnpm run format   # prettier --write .
pnpm run check    # svelte-kit sync && svelte-check --tsconfig ./jsconfig.json
```

These tools are installed (`prettier`, `eslint`, `svelte-check`, and their plugins are all in
`frontend/package.json`'s `devDependencies`) and CI runs all three, but not symmetrically: `.github/workflows/tests.yml`'s `frontend-checks` job runs the Prettier check with a
`|| echo "::warning::..."` fallback, so a formatting difference shows up as a CI **warning**, not a
failed build. The ESLint step (`pnpm eslint .`) has no such fallback. A lint error fails the job.
`pnpm check` (svelte-check) and `pnpm build` run unconditionally after that and also fail the job on
error. So in practice: fix ESLint errors and type errors before opening a PR, but don't be surprised
if Prettier differences are flagged as a warning rather than a hard failure. Run `pnpm run format`
yourself rather than relying on CI to catch it.

## Flutter

```bash
cd mobile
dart format .
flutter analyze --no-fatal-infos
```

`mobile/analysis_options.yaml` includes `package:flutter_lints/flutter.yaml` with no
project-specific rules added or removed. Neither of this repository's two GitHub Actions workflows
(`tests.yml`, `codeql-analysis.yml`) mentions Flutter, Dart, or `mobile/` at all, so nothing in CI
enforces Dart formatting or lint cleanliness. Unlike the backend, which now gates on ruff, running
these commands yourself before opening a PR is the only check that happens. See
[Build and configure](../mobile/build-and-configure.md#tests-and-analysis) for the full command set
including `flutter test`.
