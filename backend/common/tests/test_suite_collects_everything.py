"""A test file pytest never collects is not a test, and it reads like one.

`pytest.ini` sets ``python_files = tests.py test_*.py *_tests.py``. Nine files
matched none of those patterns, because they were named ``tests_*.py``: the
plural ``tests_`` prefix is one character away from the ``test_`` that gets
collected and a full word away from the ``*_tests.py`` suffix that also does.

They were not merely idle. Every one of them raised ``ImportError`` on import,
naming base classes and helpers that had been deleted (``AccountCreateTest``,
``CaseCreation``, ``ObjectsCreation``) or, in one case, the ``Company`` model
that became ``Org``. So the tree contained 29 test functions that could not run
and had not run for a long time, and `grep` still found "a celery task test"
for anyone who went looking for coverage of the mail tasks. That is worse than
an empty directory, which is why they were deleted rather than renamed.

This test guards the naming, not the deletion: it fails on a new file that
looks like a test and would be skipped by the collector.
"""

from __future__ import annotations

import fnmatch
from pathlib import Path

# Kept in sync with `python_files` in pytest.ini by hand. There is no public
# API to read it back from a running session, and duplicating three globs is
# cheaper than the failure this prevents.
COLLECTED_PATTERNS = ("tests.py", "test_*.py", "*_tests.py")

SKIP_DIRS = {".venv", "venv", "node_modules", "migrations", "htmlcov", "staticfiles"}


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _looks_like_tests(name: str) -> bool:
    """Files a reader would take for a test suite."""
    return name.startswith("test") or "_test" in name


def test_no_test_file_is_invisible_to_the_collector():
    stranded = []
    for path in _backend_root().rglob("*.py"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        name = path.name
        if not _looks_like_tests(name):
            continue
        if any(fnmatch.fnmatch(name, pattern) for pattern in COLLECTED_PATTERNS):
            continue
        stranded.append(str(path.relative_to(_backend_root())))

    assert stranded == [], (
        "These files look like tests but pytest will not collect them "
        f"(python_files = {' '.join(COLLECTED_PATTERNS)}). Rename to test_*.py "
        "or delete them: " + ", ".join(stranded)
    )


def test_the_sweep_actually_looks_at_something():
    """A guard that silently walks zero files passes forever.

    The same trap as `common/tests/test_org_index_coverage.py`: without this,
    a wrong root or an over-broad skip list turns the check above into a
    green light that means nothing.
    """
    seen = [
        p
        for p in _backend_root().rglob("test_*.py")
        if not any(part in SKIP_DIRS for part in p.parts)
    ]
    assert len(seen) > 50, f"only found {len(seen)} test files, the walk is wrong"
