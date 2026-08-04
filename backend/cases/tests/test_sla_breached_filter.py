"""Regression tests for the ``?sla_breached=true`` case filter.

The filter is raw SQL in ``.extra(where=[...])``. Written with unqualified
column names it resolved fine against a bare ``Case`` queryset and raised
``ProgrammingError: column reference "first_response_at" is ambiguous`` the
moment the queryset joined a table sharing any of those names. Combining the
filter with a status list did exactly that, so ``/api/cases/?sla_breached=true``
answered 500 for any authenticated caller.

These assert the shape of the generated SQL rather than executing it, so they
run on the SQLite test database. The clause itself is Postgres-specific
(``INTERVAL``), so an execution test could only run under the
``postgres_only`` marker and would not guard the default suite.
"""

from django.http import QueryDict

from cases.models import Case
from cases.views import apply_case_list_filters

SLA_COLUMNS = (
    "first_response_at",
    "sla_first_response_hours",
    "resolved_at",
    "sla_resolution_hours",
    "created_at",
)


def _where_sql(queryset):
    """The WHERE text of a queryset, without needing a live connection.

    Only the WHERE clause. ``str(query)`` also renders the SELECT list, which
    already names every column table-qualified, so asserting against the whole
    string passes whether or not the raw clause was ever fixed. The first
    version of this test did exactly that and was worthless.
    """
    sql = str(queryset.query)
    _, separator, where = sql.partition(" WHERE ")
    assert separator, "queryset has no WHERE clause to inspect"
    return where


def test_sla_breached_qualifies_every_column():
    """Each column the raw clause names must carry its table.

    An unqualified name here is the exact bug this test exists for: it works
    until the queryset joins, then answers 500.
    """
    params = QueryDict("sla_breached=true")
    sql = _where_sql(apply_case_list_filters(Case.objects.all(), params))

    for column in SLA_COLUMNS:
        assert f'"case"."{column}"' in sql, (
            f"{column} is not table-qualified in the sla_breached clause. "
            "Unqualified, it raises ProgrammingError as soon as the queryset "
            "joins a table with a column of the same name."
        )


def test_sla_breached_survives_a_join():
    """The filter must still build when combined with one that joins.

    ``assigned_to`` is a many-to-many, so filtering on it joins the through
    table and the profile table. This is the combination the frontend's ticket
    queue actually sends, and the one that used to 500.
    """
    params = QueryDict("sla_breached=true&status=New&status=Assigned")
    queryset = apply_case_list_filters(Case.objects.all(), params)
    queryset = queryset.filter(assigned_to__isnull=False)

    sql = _where_sql(queryset)

    assert '"case"."first_response_at"' in sql
    # A bare reference would be the regression. Look for the column name with
    # no table prefix in front of it.
    assert " first_response_at" not in sql.replace('"case"."first_response_at"', "")


def test_sla_breached_is_opt_in():
    """Anything other than the literal "true" leaves the queryset alone."""
    untouched = str(Case.objects.all().query)

    for value in ("false", "1", "yes", ""):
        params = QueryDict(f"sla_breached={value}")
        sql = str(apply_case_list_filters(Case.objects.all(), params).query)
        assert sql == untouched, f"sla_breached={value!r} should not filter"
