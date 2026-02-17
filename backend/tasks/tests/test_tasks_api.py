import pytest
from rest_framework.exceptions import PermissionDenied

from tasks.models import Task


@pytest.mark.django_db
class TestTaskListView:
    """Tests for GET /api/tasks/ and POST /api/tasks/."""

    def test_list_tasks(self, admin_client, admin_user, org_a):
        Task.objects.create(
            title="Sample Task",
            status="New",
            priority="Medium",
            org=org_a,
            created_by=admin_user,
        )
        response = admin_client.get("/api/tasks/")
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert data["tasks_count"] >= 1

    def test_create_task(self, admin_client, org_a):
        response = admin_client.post(
            "/api/tasks/",
            {"title": "New Task", "status": "New", "priority": "High"},
            format="json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is False
        assert Task.objects.filter(title="New Task", org=org_a).exists()

    def test_create_task_unauthenticated(self, unauthenticated_client):
        with pytest.raises(PermissionDenied):
            unauthenticated_client.post(
                "/api/tasks/",
                {"title": "Unauthorized Task", "status": "New", "priority": "Low"},
                format="json",
            )

    def test_org_isolation(self, admin_client, admin_user, org_a, org_b):
        """Tasks from another org should not appear in the task list."""
        Task.objects.create(
            title="Org A Task",
            status="New",
            priority="Low",
            org=org_a,
            created_by=admin_user,
        )
        # Create a task in org_b that should not be visible
        from common.models import User

        other_user = User.objects.create_user(
            email="other@example.com", password="testpass123"
        )
        Task.objects.create(
            title="Org B Task",
            status="New",
            priority="Low",
            org=org_b,
            created_by=other_user,
        )
        response = admin_client.get("/api/tasks/")
        assert response.status_code == 200
        data = response.json()
        titles = [t["title"] for t in data["tasks"]]
        assert "Org A Task" in titles
        assert "Org B Task" not in titles


@pytest.mark.django_db
class TestTaskDetailView:
    """Tests for GET/PUT/DELETE /api/tasks/<pk>/."""

    def test_get_detail(self, admin_client, admin_user, org_a):
        task = Task.objects.create(
            title="Detail Task",
            status="New",
            priority="Medium",
            org=org_a,
            created_by=admin_user,
        )
        response = admin_client.get(f"/api/tasks/{task.id}/")
        assert response.status_code == 200
        data = response.json()
        assert "task_obj" in data
        assert data["task_obj"]["title"] == "Detail Task"

    def test_update_task(self, admin_client, admin_user, org_a):
        task = Task.objects.create(
            title="Old Title",
            status="New",
            priority="Low",
            org=org_a,
            created_by=admin_user,
        )
        response = admin_client.put(
            f"/api/tasks/{task.id}/",
            {"title": "Updated Title", "status": "In Progress", "priority": "High"},
            format="json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is False
        task.refresh_from_db()
        assert task.title == "Updated Title"
        assert task.status == "In Progress"

    def test_delete_task(self, admin_client, admin_user, org_a):
        task = Task.objects.create(
            title="Delete Me",
            status="New",
            priority="Low",
            org=org_a,
            created_by=admin_user,
        )
        response = admin_client.delete(f"/api/tasks/{task.id}/")
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is False
        assert not Task.objects.filter(id=task.id).exists()

    def test_cross_org(self, org_b_client, admin_user, org_a):
        """A client from org_b must not access a task belonging to org_a."""
        task = Task.objects.create(
            title="Org A Only",
            status="New",
            priority="Low",
            org=org_a,
            created_by=admin_user,
        )
        response = org_b_client.get(f"/api/tasks/{task.id}/")
        assert response.status_code == 404

    def test_add_comment(self, admin_client, admin_user, org_a):
        task = Task.objects.create(
            title="Comment Task",
            status="New",
            priority="Medium",
            org=org_a,
            created_by=admin_user,
        )
        response = admin_client.post(
            f"/api/tasks/{task.id}/",
            {"comment": "This is a test comment"},
            format="json",
        )
        assert response.status_code == 200
        data = response.json()
        assert "comments" in data

    def test_create_task_invalid(self, admin_client):
        """POST without a title should return 400."""
        response = admin_client.post(
            "/api/tasks/",
            {"status": "New", "priority": "Low"},
            format="json",
        )
        assert response.status_code == 400
        data = response.json()
        assert data["error"] is True
