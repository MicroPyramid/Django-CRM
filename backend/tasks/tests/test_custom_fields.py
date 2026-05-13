"""Tasks-side tests for custom fields: Task create/update payloads,
list filter, and detail-page response shape.

Mirrors opportunity/tests/test_custom_fields.py.
"""

from __future__ import annotations

import pytest
from django.db import connection

from common.models import CustomFieldDefinition
from tasks.models import Task

pg_only = pytest.mark.skipif(
    connection.vendor != "postgresql",
    reason="JSONField __contains lookup requires PostgreSQL",
)


TASKS_LIST_URL = "/api/tasks/"


def _set_rls(org):
    if connection.vendor != "postgresql":
        return
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT set_config('app.current_org', %s, false)", [str(org.id)]
        )


def _make_complexity_def(org, **overrides):
    defaults = {
        "target_model": "Task",
        "key": "complexity",
        "label": "Complexity",
        "field_type": "dropdown",
        "options": [
            {"value": "trivial", "label": "Trivial"},
            {"value": "epic", "label": "Epic"},
        ],
        "is_required": False,
        "is_active": True,
    }
    defaults.update(overrides)
    return CustomFieldDefinition.objects.create(org=org, **defaults)


@pytest.fixture
def task_a(org_a, admin_user):
    _set_rls(org_a)
    return Task.objects.create(
        title="Primary Task",
        status="New",
        priority="Medium",
        org=org_a,
        created_by=admin_user,
    )


@pytest.fixture
def task_a2(org_a, admin_user):
    _set_rls(org_a)
    return Task.objects.create(
        title="Secondary Task",
        status="New",
        priority="Low",
        org=org_a,
        created_by=admin_user,
    )


@pytest.mark.django_db
class TestTaskCreateWithCustomFields:
    def test_create_with_valid_dropdown_value(self, admin_client, org_a):
        _make_complexity_def(org_a)
        response = admin_client.post(
            TASKS_LIST_URL,
            {
                "title": "Tiered Task",
                "status": "New",
                "priority": "Low",
                "custom_fields": {"complexity": "epic"},
            },
            format="json",
        )
        assert response.status_code == 200, response.content
        task = Task.objects.get(title="Tiered Task", org=org_a)
        assert task.custom_fields == {"complexity": "epic"}

    def test_create_rejects_invalid_dropdown_value(self, admin_client, org_a):
        _make_complexity_def(org_a)
        response = admin_client.post(
            TASKS_LIST_URL,
            {
                "title": "Bad Tier Task",
                "status": "New",
                "priority": "Low",
                "custom_fields": {"complexity": "platinum"},
            },
            format="json",
        )
        assert response.status_code == 400
        assert "custom_fields" in response.json()["errors"]
        assert "complexity" in response.json()["errors"]["custom_fields"]

    def test_create_drops_unknown_keys(self, admin_client, org_a):
        _make_complexity_def(org_a)
        response = admin_client.post(
            TASKS_LIST_URL,
            {
                "title": "Unknown Key Task",
                "status": "New",
                "priority": "Low",
                "custom_fields": {"complexity": "trivial", "made_up": "ignored"},
            },
            format="json",
        )
        assert response.status_code == 200
        task = Task.objects.get(title="Unknown Key Task", org=org_a)
        assert task.custom_fields == {"complexity": "trivial"}

    def test_create_required_missing_returns_400(self, admin_client, org_a):
        _make_complexity_def(org_a, is_required=True)
        response = admin_client.post(
            TASKS_LIST_URL,
            {"title": "No CF Task", "status": "New", "priority": "Low"},
            format="json",
        )
        assert response.status_code == 400
        assert "complexity" in response.json()["errors"]["custom_fields"]


@pytest.mark.django_db
class TestTaskUpdateWithCustomFields:
    def test_patch_merges_with_existing(self, admin_client, task_a, org_a):
        _make_complexity_def(org_a)
        _make_complexity_def(
            org_a,
            key="story_points",
            field_type="number",
            options=None,
        )
        task_a.custom_fields = {"complexity": "epic"}
        task_a.save()

        response = admin_client.patch(
            f"{TASKS_LIST_URL}{task_a.id}/",
            {"custom_fields": {"story_points": 13}},
            format="json",
        )
        assert response.status_code == 200, response.content
        task_a.refresh_from_db()
        assert task_a.custom_fields == {
            "complexity": "epic",
            "story_points": 13.0,
        }

    def test_patch_invalid_returns_400(self, admin_client, task_a, org_a):
        _make_complexity_def(org_a)
        response = admin_client.patch(
            f"{TASKS_LIST_URL}{task_a.id}/",
            {"custom_fields": {"complexity": "platinum"}},
            format="json",
        )
        assert response.status_code == 400

    def test_put_replaces_custom_fields(self, admin_client, task_a, org_a):
        _make_complexity_def(org_a)
        task_a.custom_fields = {"complexity": "trivial"}
        task_a.save()

        response = admin_client.put(
            f"{TASKS_LIST_URL}{task_a.id}/",
            {
                "title": task_a.title,
                "status": task_a.status,
                "priority": task_a.priority,
                "custom_fields": {"complexity": "epic"},
            },
            format="json",
        )
        assert response.status_code == 200, response.content
        task_a.refresh_from_db()
        assert task_a.custom_fields == {"complexity": "epic"}


@pg_only
@pytest.mark.django_db
class TestTaskListFilter:
    def test_cf_filter_returns_matching(
        self, admin_client, task_a, task_a2, org_a
    ):
        _make_complexity_def(org_a)
        task_a.custom_fields = {"complexity": "epic"}
        task_a.save()
        task_a2.custom_fields = {"complexity": "trivial"}
        task_a2.save()

        response = admin_client.get(f"{TASKS_LIST_URL}?cf_complexity=epic")
        body = response.json()
        ids = [t["id"] for t in body["tasks"]]
        assert str(task_a.id) in ids
        assert str(task_a2.id) not in ids


@pytest.mark.django_db
class TestTaskDetailResponse:
    def test_detail_includes_definitions_and_values(
        self, admin_client, task_a, org_a
    ):
        _make_complexity_def(org_a)
        task_a.custom_fields = {"complexity": "trivial"}
        task_a.save()

        response = admin_client.get(f"{TASKS_LIST_URL}{task_a.id}/")
        assert response.status_code == 200, response.content
        body = response.json()
        assert body["task_obj"]["custom_fields"] == {"complexity": "trivial"}
        keys = [d["key"] for d in body["custom_field_definitions"]]
        assert "complexity" in keys

    def test_detail_excludes_inactive_definitions(
        self, admin_client, task_a, org_a
    ):
        _make_complexity_def(org_a)
        _make_complexity_def(
            org_a, key="legacy", field_type="text", options=None, is_active=False
        )
        response = admin_client.get(f"{TASKS_LIST_URL}{task_a.id}/")
        keys = [d["key"] for d in response.json()["custom_field_definitions"]]
        assert "complexity" in keys
        assert "legacy" not in keys

    def test_cross_org_does_not_leak_definitions(
        self, admin_client, task_a, org_a, org_b
    ):
        CustomFieldDefinition.objects.create(
            org=org_b,
            target_model="Task",
            key="other_org_field",
            label="Other org",
            field_type="text",
        )
        response = admin_client.get(f"{TASKS_LIST_URL}{task_a.id}/")
        keys = [d["key"] for d in response.json()["custom_field_definitions"]]
        assert "other_org_field" not in keys
