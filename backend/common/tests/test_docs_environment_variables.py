"""The environment-variable reference must match what the code actually reads.

The current bottlecrm.io quick-start tells self-hosters to set JWT_SIGNING_KEY.
No such variable is read anywhere in this codebase. A reader following that page
sets a variable that does nothing and believes their install is configured.
"""

import re
from pathlib import Path

import pytest
from django.conf import settings

REPO_ROOT = Path(settings.BASE_DIR).parent
SETTINGS_PATH = Path(settings.BASE_DIR) / "crm" / "settings.py"
ENV_DOCKER_PATH = REPO_ROOT / ".env.docker"
COMPOSE_PATH = REPO_ROOT / "docker-compose.yml"
REFERENCE_PATH = REPO_ROOT / "docs" / "reference" / "environment-variables.md"

# Matches os.environ.get("NAME") and os.getenv("NAME"), including calls whose
# argument sits on the following line.
SETTINGS_ENV_RE = re.compile(
    r"os\.(?:environ\.get|getenv)\(\s*[\"']([A-Z][A-Z0-9_]*)[\"']"
)
# Matches the leading `NAME` cell of a markdown table row.
DOC_TABLE_ROW_RE = re.compile(r"^\|\s*`([A-Z][A-Z0-9_]*)`", re.MULTILINE)
# Matches NAME= in .env files and NAME: in compose environment blocks.
ENV_FILE_RE = re.compile(r"^\s*-?\s*([A-Z][A-Z0-9_]*)\s*[=:]", re.MULTILINE)

# Read by settings.py but intentionally left out of the reference table.
UNDOCUMENTED_BY_DESIGN = {
    "ENV_TYPE",  # internal dev/prod switch; not something a self-hoster sets
}


def _documented_variables(text: str) -> set[str]:
    return set(DOC_TABLE_ROW_RE.findall(text))


def _variables_read_by_settings(text: str) -> set[str]:
    return set(SETTINGS_ENV_RE.findall(text))


def _variables_in_env_files() -> set[str]:
    found: set[str] = set()
    for path in (ENV_DOCKER_PATH, COMPOSE_PATH):
        if path.exists():
            found |= set(ENV_FILE_RE.findall(path.read_text()))
    return found


def test_documented_variables_parses_a_reference_table():
    text = "| Variable | Default |\n| --- | --- |\n| `SECRET_KEY` | none |\n"
    assert _documented_variables(text) == {"SECRET_KEY"}


def test_variables_read_by_settings_handles_both_call_styles():
    text = 'a = os.environ.get("DBNAME", "x")\nb = os.getenv("DEBUG")\n'
    assert _variables_read_by_settings(text) == {"DBNAME", "DEBUG"}


def test_variables_read_by_settings_handles_a_wrapped_call():
    text = 'EMAIL_BACKEND = os.environ.get(\n    "EMAIL_BACKEND", "smtp"\n)\n'
    assert _variables_read_by_settings(text) == {"EMAIL_BACKEND"}


@pytest.mark.skipif(
    not REFERENCE_PATH.exists(), reason="reference page not written yet"
)
def test_no_documented_variable_is_read_nowhere():
    documented = _documented_variables(REFERENCE_PATH.read_text())
    known = (
        _variables_read_by_settings(SETTINGS_PATH.read_text())
        | _variables_in_env_files()
    )
    invented = sorted(documented - known)
    assert not invented, (
        "These variables are documented but read nowhere in the codebase:\n  "
        + "\n  ".join(invented)
        + "\n\nThis is the JWT_SIGNING_KEY failure. Remove them, or point the "
        "reference at the code that reads them."
    )


@pytest.mark.skipif(
    not REFERENCE_PATH.exists(), reason="reference page not written yet"
)
def test_every_variable_settings_reads_is_documented():
    documented = _documented_variables(REFERENCE_PATH.read_text())
    read = _variables_read_by_settings(SETTINGS_PATH.read_text())
    missing = sorted(read - documented - UNDOCUMENTED_BY_DESIGN)
    assert not missing, (
        "crm/settings.py reads these variables but the reference does not list them:\n  "
        + "\n  ".join(missing)
        + "\n\nAdd a row to docs/reference/environment-variables.md, or add the "
        "name to UNDOCUMENTED_BY_DESIGN with a comment saying why."
    )
