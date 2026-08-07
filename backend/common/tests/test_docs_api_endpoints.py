"""Every endpoint named in docs/api/ must exist in the generated OpenAPI schema.

The API reference is hand-written by choice, so nothing else stops it drifting
from the code. The current bottlecrm.io docs document `POST /api/auth/refresh/`;
the real route is `POST /api/auth/refresh-token/`. This test is what catches
that class of error.

The check runs one way only: documented endpoints must exist. It does not
require every schema path to be documented, because the reference is curated.
"""

import re
from pathlib import Path

from django.conf import settings
from drf_spectacular.generators import SchemaGenerator

DOCS_API_DIR = Path(settings.BASE_DIR).parent / "docs" / "api"
ALLOWLIST_PATH = DOCS_API_DIR / ".endpoint-check-allowlist"

HTTP_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE")

# Matches "GET /api/leads/{id}/" in prose, tables, and fenced code blocks.
# Stops at whitespace and at the characters that delimit markdown table cells,
# inline code, and quoted strings.
ENDPOINT_RE = re.compile(
    r"\b("
    + "|".join(HTTP_METHODS)
    + r")\s+(/api/[^\s`'\"|)\]<>]*(?:<[^>]*>[^\s`'\"|)\]<>]*)*)"
)

# Path parameters appear as {id} in the schema and as {id} or <str:pk> in docs.
PARAM_RE = re.compile(r"\{[^}]*\}|<[^>]*>")


def _normalise_path(path: str) -> str:
    """Collapse parameter names and trailing punctuation so docs and schema compare."""
    path = path.split("?", 1)[0].split("#", 1)[0]
    path = path.rstrip(".,;:")
    if not path.endswith("/"):
        path += "/"
    return PARAM_RE.sub("{}", path)


def _extract_endpoints(text: str) -> list[tuple[str, str]]:
    return [(method, _normalise_path(raw)) for method, raw in ENDPOINT_RE.findall(text)]


def _schema_operations() -> dict[str, set[str]]:
    schema = SchemaGenerator().get_schema(request=None, public=True)
    operations: dict[str, set[str]] = {}
    for path, methods in schema["paths"].items():
        key = _normalise_path(path)
        operations.setdefault(key, set()).update(
            method.upper() for method in methods if method.upper() in HTTP_METHODS
        )
    return operations


def _load_allowlist() -> set[str]:
    if not ALLOWLIST_PATH.exists():
        return set()
    entries = set()
    for line in ALLOWLIST_PATH.read_text().splitlines():
        entry = line.split("#", 1)[0].strip()
        if entry:
            entries.add(entry)
    return entries


def _find_missing(
    documented: list[tuple[str, str, str]],
    operations: dict[str, set[str]],
    allowlist: set[str],
) -> list[str]:
    """documented is a list of (source_filename, method, normalised_path)."""
    missing = []
    for filename, method, path in documented:
        if f"{method} {path}" in allowlist:
            continue
        if path not in operations:
            missing.append(f"{filename}: {method} {path}, no such path in the API")
        elif method not in operations[path]:
            missing.append(
                f"{filename}: {method} {path}. Path exists but does not accept "
                f"{method} (accepts {', '.join(sorted(operations[path]))})"
            )
    return missing


def test_docs_api_directory_exists():
    # Without this, every check below passes vacuously if the directory is
    # renamed or moved: Path.glob() on a missing directory yields nothing
    # rather than raising, so the whole guard would silently stop guarding.
    assert DOCS_API_DIR.is_dir(), f"{DOCS_API_DIR} is missing"


def test_normalise_path_collapses_parameters_and_trailing_slash():
    assert _normalise_path("/api/leads/{id}/") == "/api/leads/{}/"
    assert _normalise_path("/api/leads/<str:pk>/") == "/api/leads/{}/"
    assert _normalise_path("/api/leads") == "/api/leads/"


def test_normalise_path_strips_query_strings():
    # Documented filter examples carry a query string; the schema path does not.
    # Without stripping, a correct page fails the check.
    assert _normalise_path("/api/leads/?status=open") == "/api/leads/"
    assert _normalise_path("/api/leads/?status=open&page=2") == "/api/leads/"
    assert _normalise_path("/api/leads/{id}/?expand=account") == "/api/leads/{}/"


def test_extract_endpoints_reads_prose_tables_and_code_blocks():
    text = (
        "Call `GET /api/leads/` to list them.\n"
        "| POST /api/leads/ | create |\n"
        "```http\nDELETE /api/leads/{id}/\n```\n"
    )
    assert _extract_endpoints(text) == [
        ("GET", "/api/leads/"),
        ("POST", "/api/leads/"),
        ("DELETE", "/api/leads/{}/"),
    ]


def test_find_missing_reports_a_path_that_does_not_exist():
    # The real-world case: /api/auth/refresh/ does not exist; the route is
    # /api/auth/refresh-token/.
    operations = {"/api/auth/refresh-token/": {"POST"}}
    missing = _find_missing(
        [("authentication.md", "POST", "/api/auth/refresh/")], operations, set()
    )
    assert len(missing) == 1
    assert "no such path" in missing[0]


def test_find_missing_reports_a_method_the_path_does_not_accept():
    operations = {"/api/leads/": {"GET", "POST"}}
    missing = _find_missing([("leads.md", "DELETE", "/api/leads/")], operations, set())
    assert len(missing) == 1
    assert "does not accept DELETE" in missing[0]


def test_find_missing_is_empty_when_everything_resolves():
    operations = {"/api/leads/": {"GET", "POST"}}
    documented = [
        ("leads.md", "GET", "/api/leads/"),
        ("leads.md", "POST", "/api/leads/"),
    ]
    assert _find_missing(documented, operations, set()) == []


def test_find_missing_honours_the_allowlist():
    operations = {"/api/leads/": {"GET"}}
    documented = [("leads.md", "POST", "/api/planned/")]
    assert _find_missing(documented, operations, {"POST /api/planned/"}) == []


def test_every_documented_api_endpoint_exists():
    operations = _schema_operations()
    allowlist = _load_allowlist()
    documented = [
        (path.name, method, endpoint)
        for path in sorted(DOCS_API_DIR.glob("*.md"))
        for method, endpoint in _extract_endpoints(path.read_text())
    ]
    missing = _find_missing(documented, operations, allowlist)
    assert not missing, (
        "docs/api/ documents endpoints that do not exist:\n  "
        + "\n  ".join(missing)
        + "\n\nFix the docs, or add an entry to docs/api/.endpoint-check-allowlist "
        "with a comment explaining why."
    )
