import pytest

from leads.models import LeadPipeline, LeadStage


@pytest.mark.django_db
class TestLeadPipelineListCreateView:
    """Tests for GET/POST /api/leads/pipelines/."""

    def test_create_pipeline(self, admin_client, org_a):
        response = admin_client.post(
            "/api/leads/pipelines/",
            {"name": "Sales Pipeline"},
            format="json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Sales Pipeline"
        assert LeadPipeline.objects.filter(
            name="Sales Pipeline", org=org_a
        ).exists()

    def test_list_pipelines(self, admin_client, admin_user, org_a):
        LeadPipeline.objects.create(
            name="Pipeline A", org=org_a, created_by=admin_user
        )
        response = admin_client.get("/api/leads/pipelines/")
        assert response.status_code == 200
        data = response.json()
        assert "pipelines" in data

    def test_create_pipeline_non_admin(self, user_client):
        response = user_client.post(
            "/api/leads/pipelines/",
            {"name": "Blocked Pipeline"},
            format="json",
        )
        assert response.status_code == 403


@pytest.mark.django_db
class TestLeadPipelineDetailView:
    """Tests for GET/PUT/DELETE /api/leads/pipelines/<pk>/."""

    def test_get_pipeline_detail(self, admin_client, admin_user, org_a):
        pipeline = LeadPipeline.objects.create(
            name="Detail Pipeline", org=org_a, created_by=admin_user
        )
        response = admin_client.get(f"/api/leads/pipelines/{pipeline.id}/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Detail Pipeline"

    def test_update_pipeline(self, admin_client, admin_user, org_a):
        pipeline = LeadPipeline.objects.create(
            name="Old Name", org=org_a, created_by=admin_user
        )
        response = admin_client.put(
            f"/api/leads/pipelines/{pipeline.id}/",
            {"name": "New Name"},
            format="json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"

    def test_delete_empty_pipeline(self, admin_client, admin_user, org_a):
        pipeline = LeadPipeline.objects.create(
            name="Empty Pipeline", org=org_a, created_by=admin_user
        )
        response = admin_client.delete(
            f"/api/leads/pipelines/{pipeline.id}/"
        )
        assert response.status_code == 204


@pytest.mark.django_db
class TestLeadStageViews:
    """Tests for stage creation, update, delete, and reorder."""

    def test_create_stage(self, admin_client, admin_user, org_a):
        pipeline = LeadPipeline.objects.create(
            name="Stage Pipeline",
            org=org_a,
            created_by=admin_user,
        )
        response = admin_client.post(
            f"/api/leads/pipelines/{pipeline.id}/stages/",
            {
                "name": "Qualification",
                "order": 1,
                "color": "#FF5733",
                "stage_type": "open",
            },
            format="json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Qualification"

    def test_update_stage(self, admin_client, admin_user, org_a):
        pipeline = LeadPipeline.objects.create(
            name="Update Stage Pipeline",
            org=org_a,
            created_by=admin_user,
        )
        stage = LeadStage.objects.create(
            pipeline=pipeline,
            name="Initial",
            order=0,
            color="#000000",
            stage_type="open",
            org=org_a,
        )
        response = admin_client.put(
            f"/api/leads/stages/{stage.id}/",
            {"name": "Renamed Stage", "color": "#FFFFFF"},
            format="json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Renamed Stage"

    def test_delete_empty_stage(self, admin_client, admin_user, org_a):
        pipeline = LeadPipeline.objects.create(
            name="Delete Stage Pipeline",
            org=org_a,
            created_by=admin_user,
        )
        stage = LeadStage.objects.create(
            pipeline=pipeline,
            name="Disposable",
            order=0,
            color="#000000",
            stage_type="open",
            org=org_a,
        )
        response = admin_client.delete(f"/api/leads/stages/{stage.id}/")
        assert response.status_code == 204

    def test_reorder_stages(self, admin_client, admin_user, org_a):
        pipeline = LeadPipeline.objects.create(
            name="Reorder Pipeline",
            org=org_a,
            created_by=admin_user,
        )
        stage_a = LeadStage.objects.create(
            pipeline=pipeline,
            name="Stage A",
            order=0,
            org=org_a,
        )
        stage_b = LeadStage.objects.create(
            pipeline=pipeline,
            name="Stage B",
            order=1,
            org=org_a,
        )
        # Reverse the order
        response = admin_client.post(
            f"/api/leads/pipelines/{pipeline.id}/stages/reorder/",
            {"stage_ids": [str(stage_b.id), str(stage_a.id)]},
            format="json",
        )
        assert response.status_code == 200
        stage_a.refresh_from_db()
        stage_b.refresh_from_db()
        assert stage_b.order < stage_a.order


@pytest.mark.django_db
class TestLeadKanbanView:
    """Tests for GET /api/leads/kanban/."""

    def test_kanban_view(self, admin_client, org_a):
        response = admin_client.get("/api/leads/kanban/")
        assert response.status_code == 200
        data = response.json()
        assert "columns" in data
