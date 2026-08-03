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

**But read this before running anything:** as of this writing, none of `black`, `isort`, or `ruff`
is declared as a dependency anywhere in `backend/pyproject.toml`, not in `[project.dependencies]`,
not in the `dev` or `docs` groups under `[dependency-groups]`, and not
pulled in transitively (`backend/uv.lock` has no entry for any of the three). `uv sync` on a fresh
clone will not install any of them, and `uv run black .` fails on a fresh clone with `error: Failed
to spawn: 'black' / Caused by: No such file or directory`. The same is true of `isort` and `ruff`.
CI does not run any of them either:
`.github/workflows/tests.yml`'s `backend-tests` job runs a migration check and `pytest`, and nothing
else. There is no lint or format step for Python anywhere in this repository's CI. In practice,
Python style in this project is currently enforced by human review, not tooling.

Two things follow from that:

1. **Don't `uv add black isort ruff` to make the documented commands work.** Adding a dependency
   changes `pyproject.toml` and re-locks `uv.lock` for every future `uv sync`, including CI's, so
   it's a decision to make deliberately, in its own PR, not something to smuggle in while fixing an
   unrelated bug. See [Development setup](development-setup.md#backend) for what `uv add` actually
   does.
2. **The codebase does not currently conform to what these tools would enforce**, so even running
   them read-only produces a large, unrelated diff: `uvx ruff check .`; `uvx` runs a tool from
   PyPI in an ephemeral environment without touching this project's lockfile, reports on the order
   of 150+ findings across the tree today, and `uvx black --check --diff .` reports on the order of
   170 files that would be reformatted. Neither number is a defect to fix in passing; it reflects
   that these tools have not been run consistently against this codebase's history. If you want to
   check your own changes without installing anything project-wide, scope `uvx` to the files you
   touched (`uvx ruff check path/to/your_file.py`, `uvx black --check path/to/your_file.py`) rather
   than the whole tree, running `black .` or `ruff check --fix .` across everything will reformat
   files you didn't mean to touch and turn a focused PR into an unreviewable one.

Match the surrounding file's conventions by eye, 4-space indentation, double-quoted strings,
Django/DRF import grouping (standard library, then third-party, then local `common`/app imports),
the way `ruff.toml`'s settings describe, even without the tool enforcing it for you.

## Frontend

`frontend/package.json` defines the real commands:

```bash
pnpm run lint     # prettier --check . && eslint .
pnpm run format   # prettier --write .
pnpm run check    # svelte-kit sync && svelte-check --tsconfig ./jsconfig.json
```

Unlike the backend, these tools are installed (`prettier`, `eslint`, `svelte-check`, and their
plugins are all in `frontend/package.json`'s `devDependencies`) and CI runs all three, but not
symmetrically: `.github/workflows/tests.yml`'s `frontend-checks` job runs the Prettier check with a
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
(`tests.yml`, `codeql-analysis.yml`) mentions Flutter, Dart, or `mobile/` at all, so, like the
backend's formatters, nothing in CI enforces Dart formatting or lint cleanliness; running these
commands yourself before opening a PR is the only check that happens. See
[Build and configure](../mobile/build-and-configure.md#tests-and-analysis) for the full command set
including `flutter test`.
