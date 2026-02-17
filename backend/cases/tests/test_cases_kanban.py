"""
Tests for Case Kanban, Pipeline, and Stage API views.

Run with: pytest cases/tests/test_cases_kanban.py -v
"""

import pytest
from django.db import connection
from rest_framework import status

from cases.models import Case, CasePipeline, CaseStage


PIPELINES_URL = "/api/cases/pipelines/"
KANBAN_URL = "/api/cases/kanban/"


def _pipeline_detail_url(pk):
    return f"/api/cases/pipelines/{pk}/"


def _stage_create_url(pipeline_pk):
    return f"/api/cases/pipelines/{pipeline_pk}/stages/"


def _stage_reorder_url(pipeline_pk):
    return f"/api/cases/pipelines/{pipeline_pk}/stages/reorder/"


def _stage_detail_url(pk):
    return f"/api/cases/stages/{pk}/"


def _set_rls(org):
    """Set PostgreSQL RLS context so direct ORM writes are allowed.
    No-op on SQLite (used in tests).
    """
    if connection.vendor != "postgresql":
        return
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT set_config('app.current_org', %s, false)", [str(org.id)]
        )


@pytest.fixture
def pipeline(admin_user, org_a):
    """A case pipeline belonging to org_a with no default stages."""
    _set_rls(org_a)
    return CasePipeline.objects.create(
        name="Support Pipeline",
        org=org_a,
        created_by=admin_user,
    )


@pytest.fixture
def stage_open(pipeline, admin_user, org_a):
    """An 'open' stage inside the test pipeline."""
    _set_rls(org_a)
    return CaseStage.objects.create(
        pipeline=pipeline,
        name="New",
        order=0,
        color="#3B82F6",
        stage_type="open",
        org=org_a,
        created_by=admin_user,
    )


@pytest.fixture
def stage_closed(pipeline, admin_user, org_a):
    """A 'closed' stage inside the test pipeline."""
    _set_rls(org_a)
    return CaseStage.objects.create(
        pipeline=pipeline,
        name="Resolved",
        order=1,
        color="#22C55E",
        stage_type="closed",
        org=org_a,
        created_by=admin_user,
    )


@pytest.mark.django_db
class TestCasePipeline:
    """Tests for pipeline CRUD: /api/cases/pipelines/"""

    def test_create_pipeline(self, admin_client):
        response = admin_client.post(
            PIPELINES_URL,
            {
                "name": "Engineering Pipeline",
                "create_default_stages": False,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Engineering Pipeline"

    def test_list_pipelines(self, admin_client, pipeline):
        response = admin_client.get(PIPELINES_URL)
        assert response.status_code == status.HTTP_200_OK
        assert "pipelines" in response.data
        names = [p["name"] for p in response.data["pipelines"]]
        assert "Support Pipeline" in names

    def test_get_pipeline_detail(self, admin_client, pipeline):
        response = admin_client.get(_pipeline_detail_url(pipeline.pk))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Support Pipeline"

    def test_delete_empty_pipeline(self, admin_client, pipeline):
        """Deleting a pipeline with no cases should succeed with 204."""
        response = admin_client.delete(_pipeline_detail_url(pipeline.pk))
        assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
class TestCaseStage:
    """Tests for stage CRUD and reorder."""

    def test_create_stage(self, admin_client, pipeline):
        response = admin_client.post(
            _stage_create_url(pipeline.pk),
            {
                "name": "In Progress",
                "order": 2,
                "color": "#F59E0B",
                "stage_type": "open",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "In Progress"

    def test_update_stage(self, admin_client, stage_open):
        response = admin_client.put(
            _stage_detail_url(stage_open.pk),
            {
                "name": "Triaged",
                "color": "#8B5CF6",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        stage_open.refresh_from_db()
        assert stage_open.name == "Triaged"

    def test_delete_empty_stage(self, admin_client, stage_open):
        """Deleting a stage with no cases should succeed with 204."""
        response = admin_client.delete(_stage_detail_url(stage_open.pk))
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not CaseStage.objects.filter(pk=stage_open.pk).exists()

    def test_reorder_stages(self, admin_client, pipeline, stage_open, stage_closed):
        """Reorder stages so that 'Resolved' comes before 'New'."""
        response = admin_client.post(
            _stage_reorder_url(pipeline.pk),
            {
                "stage_ids": [str(stage_closed.pk), str(stage_open.pk)],
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        stage_closed.refresh_from_db()
        stage_open.refresh_from_db()
        assert stage_closed.order < stage_open.order


@pytest.mark.django_db
class TestCaseKanban:
    """Tests for the kanban board view: GET /api/cases/kanban/"""

    def test_kanban_view(self, admin_client, org_a, admin_user):
        """The default status-based kanban view should return columns."""
        # Create a case so there is data (RLS context set by _set_rls)
        _set_rls(org_a)
        Case.objects.create(
            name="Kanban test case",
            status="New",
            priority="Normal",
            created_by=admin_user,
            org=org_a,
        )
        response = admin_client.get(KANBAN_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["mode"] == "status"
        assert "columns" in response.data
        assert response.data["total_cases"] >= 1
