import pytest

from tasks.models import Task, TaskPipeline, TaskStage


@pytest.mark.django_db
class TestTaskPipeline:
    """Tests for /api/tasks/pipelines/ endpoints."""

    def test_create_pipeline(self, admin_client, org_a):
        response = admin_client.post(
            "/api/tasks/pipelines/",
            {"name": "Development Pipeline", "create_default_stages": False},
            format="json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Development Pipeline"
        assert TaskPipeline.objects.filter(name="Development Pipeline", org=org_a).exists()

    def test_list_pipelines(self, admin_client, admin_user, org_a):
        TaskPipeline.objects.create(
            name="Pipeline 1", org=org_a, created_by=admin_user
        )
        response = admin_client.get("/api/tasks/pipelines/")
        assert response.status_code == 200
        data = response.json()
        assert "pipelines" in data
        assert len(data["pipelines"]) >= 1

    def test_get_pipeline_detail(self, admin_client, admin_user, org_a):
        pipeline = TaskPipeline.objects.create(
            name="Detail Pipeline", org=org_a, created_by=admin_user
        )
        response = admin_client.get(f"/api/tasks/pipelines/{pipeline.id}/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Detail Pipeline"

    def test_delete_empty_pipeline(self, admin_client, admin_user, org_a):
        pipeline = TaskPipeline.objects.create(
            name="Empty Pipeline", org=org_a, created_by=admin_user
        )
        response = admin_client.delete(f"/api/tasks/pipelines/{pipeline.id}/")
        assert response.status_code == 204


@pytest.mark.django_db
class TestTaskStage:
    """Tests for /api/tasks/pipelines/<pk>/stages/ and /api/tasks/stages/<pk>/."""

    def test_create_stage(self, admin_client, admin_user, org_a):
        pipeline = TaskPipeline.objects.create(
            name="Stage Pipeline", org=org_a, created_by=admin_user
        )
        response = admin_client.post(
            f"/api/tasks/pipelines/{pipeline.id}/stages/",
            {
                "name": "To Do",
                "order": 1,
                "color": "#3B82F6",
                "stage_type": "open",
            },
            format="json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "To Do"
        assert TaskStage.objects.filter(
            pipeline=pipeline, name="To Do"
        ).exists()

    def test_update_stage(self, admin_client, admin_user, org_a):
        pipeline = TaskPipeline.objects.create(
            name="Update Pipeline", org=org_a, created_by=admin_user
        )
        stage = TaskStage.objects.create(
            pipeline=pipeline,
            name="Old Stage",
            order=1,
            org=org_a,
            created_by=admin_user,
        )
        response = admin_client.put(
            f"/api/tasks/stages/{stage.id}/",
            {"name": "Renamed Stage", "order": 2},
            format="json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Renamed Stage"

    def test_delete_empty_stage(self, admin_client, admin_user, org_a):
        pipeline = TaskPipeline.objects.create(
            name="Delete Pipeline", org=org_a, created_by=admin_user
        )
        stage = TaskStage.objects.create(
            pipeline=pipeline,
            name="Delete Me",
            order=1,
            org=org_a,
            created_by=admin_user,
        )
        response = admin_client.delete(f"/api/tasks/stages/{stage.id}/")
        assert response.status_code == 204
        assert not TaskStage.objects.filter(id=stage.id).exists()

    def test_reorder_stages(self, admin_client, admin_user, org_a):
        pipeline = TaskPipeline.objects.create(
            name="Reorder Pipeline", org=org_a, created_by=admin_user
        )
        stage_a = TaskStage.objects.create(
            pipeline=pipeline, name="A", order=0, org=org_a, created_by=admin_user
        )
        stage_b = TaskStage.objects.create(
            pipeline=pipeline, name="B", order=1, org=org_a, created_by=admin_user
        )
        # Reverse the order: B first, then A
        response = admin_client.post(
            f"/api/tasks/pipelines/{pipeline.id}/stages/reorder/",
            {"stage_ids": [str(stage_b.id), str(stage_a.id)]},
            format="json",
        )
        assert response.status_code == 200
        stage_a.refresh_from_db()
        stage_b.refresh_from_db()
        assert stage_b.order < stage_a.order


@pytest.mark.django_db
class TestTaskKanban:
    """Tests for GET /api/tasks/kanban/."""

    def test_kanban_view(self, admin_client, admin_user, org_a):
        Task.objects.create(
            title="Kanban Task",
            status="New",
            priority="Medium",
            org=org_a,
            created_by=admin_user,
        )
        response = admin_client.get("/api/tasks/kanban/")
        assert response.status_code == 200
        data = response.json()
        assert "columns" in data
        assert data["mode"] == "status"
        assert data["total_tasks"] >= 1
