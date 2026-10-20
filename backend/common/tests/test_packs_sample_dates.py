"""Starter sample dates move to the day the starter is applied.

Each manifest was written with one day as "today": tasks due that day and the
few after it, deals closed some weeks before it, events and start dates
months ahead. Stored as fixed dates, every one of them aged, so a workspace
created in October opened with every open sample task overdue. The manifest
now records the day its dates were written for (`sample_dates_written_on`), and
the applier moves every sample date by however long has passed since then.
"""

import datetime
from unittest.mock import patch

import pytest

from common.packs.applier import apply_pack
from common.packs.loader import get_pack, get_registry
from common.packs.schema import PackValidationError, validate_manifest
from leads.models import Lead
from opportunity.models import Opportunity
from tasks.models import Task

APPLY_DAY = datetime.date(2026, 10, 20)


def _apply_on(day, org, pack, actor):
    with patch("common.packs.applier.timezone.localdate", return_value=day):
        return apply_pack(org, pack, actor)


@pytest.mark.django_db
def test_task_due_dates_keep_their_distance_from_today(org_a, admin_profile):
    pack = get_pack("real-estate")
    written = datetime.date.fromisoformat(pack["sample_dates_written_on"])
    shift = APPLY_DAY - written
    _apply_on(APPLY_DAY, org_a, pack, admin_profile)

    for spec in pack["sample_data"]["tasks"]:
        task = Task.objects.get(org=org_a, title=spec["title"], is_sample=True)
        expected = datetime.date.fromisoformat(spec["due_date"]) + shift
        assert task.due_date == expected


@pytest.mark.django_db
def test_deal_close_dates_and_date_custom_fields_move_too(org_a, admin_profile):
    pack = get_pack("real-estate")
    written = datetime.date.fromisoformat(pack["sample_dates_written_on"])
    shift = APPLY_DAY - written
    _apply_on(APPLY_DAY, org_a, pack, admin_profile)

    for spec in pack["sample_data"]["deals"]:
        deal = Opportunity.objects.get(org=org_a, name=spec["name"], is_sample=True)
        expected = datetime.date.fromisoformat(spec["closed_on"]) + shift
        assert deal.closed_on == expected

    moved = 0
    for spec in pack["sample_data"]["leads"]:
        raw = (spec.get("custom_fields") or {}).get("possession_by")
        if raw is None:
            continue
        lead = Lead.objects.get(
            org=org_a,
            first_name=spec.get("first_name"),
            last_name=spec.get("last_name"),
            is_sample=True,
        )
        expected = (datetime.date.fromisoformat(raw) + shift).isoformat()
        assert lead.custom_fields["possession_by"] == expected
        moved += 1
    assert moved > 0


@pytest.mark.django_db
def test_applying_does_not_change_the_cached_manifest(org_a, admin_profile):
    pack = get_pack("real-estate")
    before = pack["sample_data"]["tasks"][0]["due_date"]
    _apply_on(APPLY_DAY, org_a, pack, admin_profile)
    assert get_pack("real-estate")["sample_data"]["tasks"][0]["due_date"] == before


@pytest.mark.django_db
@pytest.mark.parametrize("pack_id", sorted(get_registry()))
def test_no_open_sample_task_is_overdue_on_the_day_it_is_applied(
    pack_id, org_a, admin_profile
):
    _apply_on(APPLY_DAY, org_a, get_pack(pack_id), admin_profile)
    overdue = Task.objects.filter(
        org=org_a, is_sample=True, due_date__lt=APPLY_DAY
    ).exclude(status="Completed")
    assert list(overdue.values_list("title", flat=True)) == []


def _minimal_manifest(**extra):
    manifest = {
        "id": "dates-test",
        "version": 1,
        "name": "Dates test",
        "description": "",
        "sample_data": {
            "tasks": [
                {
                    "title": "Call back",
                    "status": "New",
                    "priority": "Medium",
                    "due_date": "2026-08-04",
                }
            ]
        },
    }
    manifest.update(extra)
    return manifest


def test_sample_dates_without_a_written_on_day_are_refused():
    with pytest.raises(PackValidationError, match="sample_dates_written_on"):
        validate_manifest(_minimal_manifest())


def test_written_on_must_be_an_iso_date():
    with pytest.raises(PackValidationError, match="sample_dates_written_on"):
        validate_manifest(_minimal_manifest(sample_dates_written_on="3 Aug 2026"))


def test_written_on_is_accepted():
    validate_manifest(_minimal_manifest(sample_dates_written_on="2026-08-03"))
