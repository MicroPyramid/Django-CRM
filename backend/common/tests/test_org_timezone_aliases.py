"""An org's timezone is stored and used under its canonical IANA name.

Python's ``zoneinfo`` knows the backward-compatible aliases (``Asia/Calcutta``,
``Asia/Saigon``, ``US/Eastern``) through the ``tzdata`` package, so they pass
``validate_iana_timezone``. PostgreSQL reads the system tz database instead, and
newer distributions ship those aliases in an optional ``tzdata-legacy`` package.
Without it, every query that truncates a date in the org's zone fails with
``time zone "Asia/Calcutta" not recognized``, which made the leads list and the
Today page answer 500 for any org created from a browser that reports the alias.

So the alias is turned into the zone it points at on every write, in the one
function that resolves an org's zone, and once for rows already stored.
"""

import importlib

import pytest
from django.apps import apps
from django.utils import timezone

from common.models import Org
from common.org_time import activate_org_timezone, canonical_timezone


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Asia/Calcutta", "Asia/Kolkata"),
        ("Asia/Saigon", "Asia/Ho_Chi_Minh"),
        ("US/Eastern", "America/New_York"),
        ("Asia/Kolkata", "Asia/Kolkata"),
        ("America/New_York", "America/New_York"),
        # UTC is itself a link to Etc/UTC in the tz database. It stays UTC: it
        # is the field default, every database knows it, and Etc/UTC would be a
        # needless change to every org that never picked a zone.
        ("UTC", "UTC"),
        ("", ""),
    ],
)
def test_canonical_timezone(name, expected):
    assert canonical_timezone(name) == expected


def test_org_save_stores_the_canonical_name(org_a):
    org_a.timezone = "Asia/Calcutta"
    org_a.save()
    org_a.refresh_from_db()
    assert org_a.timezone == "Asia/Kolkata"


def test_activation_uses_the_canonical_name_for_a_stored_alias(org_a):
    # A row written before this fix, or by a path that skips save().
    Org.objects.filter(pk=org_a.pk).update(timezone="Asia/Calcutta")
    org_a.refresh_from_db()
    try:
        activate_org_timezone(org_a)
        assert timezone.get_current_timezone().key == "Asia/Kolkata"
    finally:
        timezone.deactivate()


def test_settings_api_stores_the_canonical_name(admin_client, org_a):
    response = admin_client.patch(
        "/api/org/settings/", {"timezone": "Asia/Calcutta"}, format="json"
    )
    assert response.status_code == 200
    org_a.refresh_from_db()
    assert org_a.timezone == "Asia/Kolkata"


def test_create_api_stores_the_canonical_name(admin_client):
    response = admin_client.post(
        "/api/org/",
        {"name": "Alias Zone Co", "timezone": "Asia/Calcutta"},
        format="json",
    )
    assert response.status_code == 201
    assert Org.objects.get(name="Alias Zone Co").timezone == "Asia/Kolkata"


def test_migration_rewrites_stored_aliases(org_a, org_b):
    Org.objects.filter(pk=org_a.pk).update(timezone="Asia/Calcutta")
    Org.objects.filter(pk=org_b.pk).update(timezone="UTC")
    migration = importlib.import_module(
        "common.migrations.0052_canonical_org_timezones"
    )

    migration.canonicalise_org_timezones(apps, None)

    org_a.refresh_from_db()
    org_b.refresh_from_db()
    assert org_a.timezone == "Asia/Kolkata"
    assert org_b.timezone == "UTC"


@pytest.mark.postgres_only
def test_today_and_leads_answer_for_an_org_stored_with_an_alias(admin_client, org_a):
    """The reported 500. On a PostgreSQL without the legacy aliases this failed
    with 'time zone "Asia/Calcutta" not recognized'; a server that still ships
    them passes either way, so the unit tests above are the real guard."""
    Org.objects.filter(pk=org_a.pk).update(timezone="Asia/Calcutta")
    assert admin_client.get("/api/dashboard/today/").status_code == 200
    assert admin_client.get("/api/leads/").status_code == 200
