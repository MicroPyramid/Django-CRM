# Adding an org-scoped model

This page walks through adding a new tenant-owned model end to end, using a worked example. A
`CallLog` model recording calls made against a `Lead`, so every code block is something you could
actually drop into the tree, not pseudocode. It assumes you've read
[Multi-tenancy and RLS](../architecture/multi-tenancy-and-rls.md), which explains *why* each of
these steps exists; this page is the checklist for *doing* it.

## The checklist

1. **Inherit `BaseOrgModel`** (`common.base`) so the model gets an `org` foreign key, the UUID
   primary key, audit fields, and the `OrgScopedManager` helpers for free.
2. **Add the table's `db_table` name to `ORG_SCOPED_TABLES`** in `backend/common/rls/__init__.py`.
3. **Write a migration** that calls `get_enable_policy_sql('your_table')` inside a `RunPython`
   operation, with a `dependencies` entry that guarantees the table already exists when it runs.
4. **Filter every queryset** that touches the model by `org=request.profile.org`.
5. **Pass `org=...` explicitly** on every `create()` / `serializer.save()`, never trust a
   client-supplied org.
6. **Write a test for both the allowed and the denied path**: an in-org request that succeeds, and
   a cross-org request that doesn't see or can't write the row.

Steps 2 and 3 are both required and neither substitutes for the other: registering the table
without a migration that actually calls `get_enable_policy_sql` leaves the table with no policies at
all, and a migration that calls `get_enable_policy_sql` without registering the table in
`ORG_SCOPED_TABLES` means `manage_rls --status` can never report on it, so a gap there is invisible
to the one tool meant to catch it. See
[Common mistakes](../self-hosting/postgresql-and-rls.md#common-mistakes) for both failure modes
described in more detail.

## The model

```python
# backend/leads/models.py
from django.db import models

from common.base import BaseOrgModel

class CallLog(BaseOrgModel):
    """A record of an outbound or inbound call made against a lead."""

    DIRECTION_CHOICES = (
        ("OUTBOUND", "Outbound"),
        ("INBOUND", "Inbound"),
    )

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="call_logs")
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    notes = models.TextField(blank=True, default="")
    duration_seconds = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Call Log"
        verbose_name_plural = "Call Logs"
        db_table = "call_log"
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["org", "-created_at"])]
```

`BaseOrgModel` is abstract, and. This is easy to get wrong, and this codebase has a live example of
getting it wrong. A subclass's own `Meta` class does **not** automatically inherit the abstract
parent's `indexes` just because the model inherits `BaseOrgModel`. `Order` (`backend/orders/models.py`,
one of the few models here that actually inherits `BaseOrgModel` rather than hand-declaring its own
`org` foreign key) declares its own `Meta` with `db_table`, `verbose_name`, and `ordering`, but no
`indexes`, so `Order._meta.indexes` is `[]` at runtime, not the `["org", "-created_at"]` index
`BaseOrgModel.Meta` defines. `backend/orders/migrations/0003_remove_order_orders_org_id_9026a7_idx_and_more.py`
is the receipt: it drops that exact index from both `order` and `order_line_item`, tables that
otherwise get every other query filtered by `org`. `PersonalAccessToken` (`backend/common/models.py`)
is the codebase's real example of doing this correctly: its own `Meta` explicitly redeclares
`indexes = [models.Index(fields=["org", "-created_at"])]` rather than assuming it's inherited, which
is exactly what the `CallLog` example above copies. `BaseOrgModel` reliably gives you `id` (UUID
primary key), `org`, `created_at`, `updated_at`, `created_by`, and `updated_by` regardless of whether
your model declares its own `Meta`. Those are fields and a `save()` override on the class itself, not
something `Meta` mediates. The `["org", "-created_at"]` index is the one thing on `BaseOrgModel` that
your own `Meta` can silently drop, so redeclare it (as above) any time your model needs its own
`Meta` for a `db_table`, `ordering`, or anything else.

## Registering the table

Add the table's `db_table` name (`call_log`, matching `Meta.db_table` above) to
`ORG_SCOPED_TABLES` in `backend/common/rls/__init__.py`. This list currently has 61 entries (see the
file itself for the current count. It changes as the project grows, so don't rely on a number
copied from documentation); a new entry looks like any other:

```python
# backend/common/rls/__init__.py
ORG_SCOPED_TABLES = [
    ...
    "task",
    "invoice",
    "call_log",  # CallLog. Call records against a lead
    # Supporting entities
    "comment",
    ...
]
```

## The RLS migration

Write a dedicated migration for the new table's policies, modeled on a real one already in the tree,
`backend/opportunity/migrations/0012_enable_rls_sales_goal.py`:

```python
# backend/leads/migrations/0017_enable_rls_call_log.py
from django.db import connection, migrations

from common.rls import get_disable_policy_sql, get_enable_policy_sql

TABLE = "call_log"


def enable_rls(apps, schema_editor):
    if connection.vendor != "postgresql":
        return
    with connection.cursor() as cursor:
        cursor.execute(get_enable_policy_sql(TABLE))


def disable_rls(apps, schema_editor):
    if connection.vendor != "postgresql":
        return
    with connection.cursor() as cursor:
        cursor.execute(get_disable_policy_sql(TABLE))


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("leads", "0016_call_log"),  # the migration that actually creates call_log
    ]

    operations = [
        migrations.RunPython(enable_rls, disable_rls),
    ]
```

`atomic = False` matches every RLS migration in this codebase; `DROP`/`CREATE POLICY` each take an
`ACCESS EXCLUSIVE` lock, so committing per-statement instead of holding one long transaction keeps
each lock brief. `get_enable_policy_sql` itself opens with `DROP POLICY IF EXISTS` before creating
either policy, so the migration is idempotent if it's ever re-run.

!!! warning "The dependency is not decorative. Get it wrong and the migration silently does nothing"
    `dependencies = [("leads", "0016_call_log")]` above is what guarantees Django applies this
    migration *after* the one that runs `CreateModel` for `CallLog`. If that dependency were missing
    or pointed at an earlier migration, Django would be free to apply this one first, and
    `ALTER TABLE "call_log" ENABLE ROW LEVEL SECURITY` against a table that doesn't exist yet would
    raise a hard error, not fail silently, *unless* the migration is written defensively with an
    existence check first. `backend/common/migrations/0034_rls_pipeline_tables.py` is exactly that
    defensive style. It checks `get_check_table_exists_sql()` before stamping each table, because
    it registers six tables across three different apps in one migration and couldn't express a
    single clean dependency chain for all of them. Its own comment explains the cost: get the
    dependencies wrong there and the check silently prints `Skipping <table> (table does not exist)`
    and moves on. The migration "succeeds," CI is green, and the table simply never gets a policy.
    For a single new model in one app, prefer the plain `opportunity/0012` shape above (a hard
    dependency, no existence check, a real error if the ordering is ever wrong) over copying
    `0034`'s defensive pattern: a loud failure during development is much cheaper than a policy
    that quietly never gets created.

## The view

Every view touching the new model needs both the standard permission classes and an explicit org
filter. RLS is the safety net, not the contract (see
[The two-layer contract](../architecture/multi-tenancy-and-rls.md#the-two-layer-contract)):

```python
# backend/leads/views/call_log_views.py
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import HasOrgContext
from leads.models import Lead, CallLog
from leads.serializer import CallLogSerializer


class CallLogListView(APIView):
    permission_classes = (IsAuthenticated, HasOrgContext)

    def get(self, request, lead_id, format=None):
        lead = get_object_or_404(Lead, id=lead_id, org=request.profile.org)
        logs = CallLog.objects.filter(org=request.profile.org, lead=lead)
        return Response(CallLogSerializer(logs, many=True).data)

    def post(self, request, lead_id, format=None):
        lead = get_object_or_404(Lead, id=lead_id, org=request.profile.org)
        serializer = CallLogSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(org=request.profile.org, lead=lead, created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
```

Two things to notice: the `Lead` lookup itself is org-filtered (`get_object_or_404(Lead, id=lead_id,
org=request.profile.org)`), so a cross-org caller gets a 404 on the parent object before ever
reaching the `CallLog` query, and `org` is passed to `serializer.save()` explicitly rather than
accepted from `request.data`, the same [server-owned field](security-rules.md#server-owned-fields)
rule that applies everywhere else.

## The tests

Write both directions, using the shared fixtures in `backend/conftest.py` (`org_a`, `org_b`,
`admin_client`, `org_b_client`, and the rest), modeled on the real pair in
`opportunity/tests/test_sales_goals.py`. `org_a`, `org_b`, `admin_client`, and `org_b_client` are
real, shared fixtures already defined in `backend/conftest.py`; `lead_in_org_a` below is not. It's a
local, file-scoped fixture this example defines itself, the same way `leads/tests/
test_lead_access_and_totals.py` has its own local `_lead()` helper rather than a shared one (there is
no org-scoped `Lead` fixture shared across the suite, because what fields a test needs on its `Lead`
varies too much to make one worth sharing):

```python
import pytest

from leads.models import CallLog, Lead


@pytest.fixture
def lead_in_org_a(org_a):
    return Lead.objects.create(
        first_name="Ada",
        last_name="Lovelace",
        email="ada@example.com",
        status="in process",
        company_name="Analytical Engines",
        org=org_a,
    )


@pytest.mark.django_db
def test_admin_can_create_call_log(admin_client, org_a, lead_in_org_a):
    response = admin_client.post(
        f"/api/leads/{lead_in_org_a.id}/call-logs/",
        {"direction": "OUTBOUND", "notes": "Left voicemail"},
        format="json",
    )
    assert response.status_code == 201
    assert CallLog.objects.filter(lead=lead_in_org_a, org=org_a).exists()


@pytest.mark.django_db
def test_org_b_cannot_read_org_a_call_logs(org_b_client, org_a, lead_in_org_a):
    """The denied path: mirrors test_org_isolation in test_sales_goals.py."""
    CallLog.objects.create(lead=lead_in_org_a, org=org_a, direction="OUTBOUND")

    response = org_b_client.get(f"/api/leads/{lead_in_org_a.id}/call-logs/")

    # The parent Lead lookup is org-scoped, so a foreign org gets a 404 on the
    # lead itself, before the CallLog query ever runs.
    assert response.status_code == 404
```

The second test is the one that actually earns its keep: a test suite that only ever checks the
allowed path can pass at 100% coverage while the org filter above is missing entirely. See
[Testing](testing.md#the-sqlite-caveat) for why this particular pair of tests is also the only thing
proving the ORM filter is correct, independent of whether RLS is even enforced in the environment the
test runs in.
