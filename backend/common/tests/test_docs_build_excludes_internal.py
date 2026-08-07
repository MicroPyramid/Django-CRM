"""The docs/ directory holds internal specs and plans alongside published pages.

MkDocs copies every file under docs_dir into the built site, including files no
nav entry references. Without an explicit exclusion, implementation plans would
be published to a public documentation site. This test is the guard.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest
from django.conf import settings

REPO_ROOT = Path(settings.BASE_DIR).parent
MKDOCS_CONFIG = REPO_ROOT / "mkdocs.yml"
INTERNAL_PREFIXES = ("superpowers", "design")


def _build_site(destination: Path) -> None:
    subprocess.run(
        [
            "mkdocs",
            "build",
            "--strict",
            "-f",
            str(MKDOCS_CONFIG),
            "-d",
            str(destination),
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.mark.skipif(shutil.which("mkdocs") is None, reason="mkdocs not installed")
def test_built_site_contains_no_internal_artifacts():
    with tempfile.TemporaryDirectory() as tmp:
        destination = Path(tmp) / "site"
        _build_site(destination)
        leaked = sorted(
            str(p.relative_to(destination))
            for p in destination.rglob("*")
            if p.is_file() and p.relative_to(destination).parts[0] in INTERNAL_PREFIXES
        )
    assert not leaked, (
        "Internal artifacts were published to the docs site:\n"
        + "\n".join(leaked)
        + "\n\nAdd the directory to `exclude_docs` in mkdocs.yml."
    )


@pytest.mark.skipif(shutil.which("mkdocs") is None, reason="mkdocs not installed")
def test_strict_build_succeeds():
    # --strict turns broken internal links and missing nav targets into errors,
    # so this doubles as the link check for every page in the nav.
    with tempfile.TemporaryDirectory() as tmp:
        _build_site(Path(tmp) / "site")
