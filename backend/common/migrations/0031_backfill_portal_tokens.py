"""Backfill the unscoped portal token → org lookup from existing rows.

Every invoice/estimate already carries a ``public_token`` and every CSAT survey
a ``token_hash``; without a lookup row the anonymous portal endpoints would 404
those existing links once RLS is enforced. This populates the lookup once.

The backfill faces the same chicken-and-egg the table exists to solve: under a
non-superuser DB role the org-scoped source rows are hidden with an empty
context. Every row is mapped by its own ``org_id`` (never a loop variable), so
the strategy only decides *which rows are visible*:

* If an empty context still exposes rows (a superuser / RLS-disabled dev DB,
  where one deployment can have thousands of orgs), a single unscoped pass sees
  everything, O(rows), not O(orgs × rows).
* If an empty context hides rows (a correctly-configured non-superuser prod
  role), the pass sees nothing, so it falls back to iterating orgs and setting
  ``app.current_org`` for each: O(orgs) cheap lookups, each seeing only its own
  rows.
"""

import hashlib

from django.db import migrations


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def backfill(apps, schema_editor):
    connection = schema_editor.connection
    # RLS (and set_config) is Postgres-only; the SQLite test backend has no
    # scoped rows to hide, so a single unscoped pass over each model is correct.
    is_postgres = connection.vendor == "postgresql"

    Org = apps.get_model("common", "Org")
    Invoice = apps.get_model("invoices", "Invoice")
    Estimate = apps.get_model("invoices", "Estimate")
    CsatSurvey = apps.get_model("cases", "CsatSurvey")
    PortalAccessToken = apps.get_model("common", "PortalAccessToken")

    def upsert(token_hash, org_id, resource_type, resource_id):
        if not token_hash or not org_id:
            return
        PortalAccessToken.objects.update_or_create(
            token_hash=token_hash,
            defaults={
                "org_id": org_id,
                "resource_type": resource_type,
                "resource_id": resource_id,
            },
        )

    def backfill_visible_rows():
        """Map every currently-visible row by its own org_id."""
        for inv in (
            Invoice.objects.exclude(public_token="")
            .only("id", "org_id", "public_token")
            .iterator()
        ):
            upsert(_sha256(inv.public_token), inv.org_id, "invoice", inv.id)
        for est in (
            Estimate.objects.exclude(public_token="")
            .only("id", "org_id", "public_token")
            .iterator()
        ):
            upsert(_sha256(est.public_token), est.org_id, "estimate", est.id)
        for survey in CsatSurvey.objects.only("id", "org_id", "token_hash").iterator():
            upsert(survey.token_hash, survey.org_id, "csat", survey.id)

    def set_context(value):
        with connection.cursor() as cursor:
            cursor.execute("SELECT set_config('app.current_org', %s, false)", [value])

    if not is_postgres:
        backfill_visible_rows()
        return

    # Does an empty context still expose rows? If so, RLS is not enforcing here
    # (superuser dev DB) and one pass sees everything. If not, RLS is hiding the
    # rows and we must resolve them one org at a time.
    set_context("")
    rls_bypassed = (
        Invoice.objects.exists()
        or Estimate.objects.exists()
        or CsatSurvey.objects.exists()
    )

    if rls_bypassed:
        backfill_visible_rows()
        return

    for org_id in Org.objects.values_list("id", flat=True).iterator():
        set_context(str(org_id))
        backfill_visible_rows()
    set_context("")


class Migration(migrations.Migration):
    dependencies = [
        ("common", "0030_portalaccesstoken"),
        (
            "invoices",
            "0010_estimate_accepted_by_email_estimate_accepted_by_name_and_more",
        ),
        ("cases", "0024_emailmessage_mailbox"),
    ]

    operations = [
        migrations.RunPython(backfill, migrations.RunPython.noop),
    ]
