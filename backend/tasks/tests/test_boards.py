import pytest

from tasks.models import Board, BoardColumn, BoardMember, BoardTask


@pytest.mark.django_db
class TestBoardListView:
    """Tests for GET /api/boards/ and POST /api/boards/."""

    def test_list_boards(self, admin_client, admin_profile, org_a):
        board = Board.objects.create(
            name="Test Board", owner=admin_profile, org=org_a
        )
        BoardMember.objects.create(board=board, profile=admin_profile, role="owner")
        response = admin_client.get("/api/boards/")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert data["count"] >= 1

    def test_create_board(self, admin_client, org_a):
        response = admin_client.post(
            "/api/boards/",
            {"name": "New Board", "create_default_columns": False},
            format="json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Board"
        assert Board.objects.filter(name="New Board", org=org_a).exists()


@pytest.mark.django_db
class TestBoardDetailView:
    """Tests for GET/PUT/DELETE /api/boards/<pk>/."""

    def test_get_board(self, admin_client, admin_profile, admin_user, org_a):
        board = Board.objects.create(
            name="Detail Board",
            owner=admin_profile,
            org=org_a,
            created_by=admin_user,
        )
        BoardMember.objects.create(board=board, profile=admin_profile, role="owner")
        response = admin_client.get(f"/api/boards/{board.id}/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Detail Board"

    def test_update_board(self, admin_client, admin_profile, admin_user, org_a):
        board = Board.objects.create(
            name="Old Board Name",
            owner=admin_profile,
            org=org_a,
            created_by=admin_user,
        )
        BoardMember.objects.create(board=board, profile=admin_profile, role="owner")
        response = admin_client.put(
            f"/api/boards/{board.id}/",
            {"name": "Updated Board Name"},
            format="json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Board Name"

    def test_delete_board(self, admin_client, admin_profile, admin_user, org_a):
        board = Board.objects.create(
            name="Delete Board",
            owner=admin_profile,
            org=org_a,
            created_by=admin_user,
        )
        BoardMember.objects.create(board=board, profile=admin_profile, role="owner")
        response = admin_client.delete(f"/api/boards/{board.id}/")
        assert response.status_code == 204
        assert not Board.objects.filter(id=board.id).exists()


@pytest.mark.django_db
class TestBoardColumns:
    """Tests for GET/POST /api/boards/<board_pk>/columns/."""

    def test_create_column(self, admin_client, admin_profile, admin_user, org_a):
        board = Board.objects.create(
            name="Column Board",
            owner=admin_profile,
            org=org_a,
            created_by=admin_user,
        )
        BoardMember.objects.create(board=board, profile=admin_profile, role="owner")
        response = admin_client.post(
            f"/api/boards/{board.id}/columns/",
            {"name": "Backlog", "order": 0, "color": "#6B7280"},
            format="json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Backlog"
        assert BoardColumn.objects.filter(board=board, name="Backlog").exists()

    def test_list_columns(self, admin_client, admin_profile, admin_user, org_a):
        board = Board.objects.create(
            name="List Column Board",
            owner=admin_profile,
            org=org_a,
            created_by=admin_user,
        )
        BoardMember.objects.create(board=board, profile=admin_profile, role="owner")
        BoardColumn.objects.create(board=board, name="To Do", order=1, org=org_a)
        BoardColumn.objects.create(board=board, name="Done", order=2, org=org_a)
        response = admin_client.get(f"/api/boards/{board.id}/columns/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2


@pytest.mark.django_db
class TestBoardTasks:
    """Tests for board task endpoints."""

    def _create_board_with_column(self, admin_profile, admin_user, org_a):
        """Helper to create a board with one column and owner membership."""
        board = Board.objects.create(
            name="Task Board",
            owner=admin_profile,
            org=org_a,
            created_by=admin_user,
        )
        BoardMember.objects.create(board=board, profile=admin_profile, role="owner")
        column = BoardColumn.objects.create(
            board=board, name="To Do", order=1, org=org_a
        )
        return board, column

    def test_create_board_task(
        self, admin_client, admin_profile, admin_user, org_a
    ):
        _board, column = self._create_board_with_column(
            admin_profile, admin_user, org_a
        )
        response = admin_client.post(
            f"/api/boards/columns/{column.id}/tasks/",
            {"title": "New Card", "priority": "medium"},
            format="json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Card"
        assert BoardTask.objects.filter(column=column, title="New Card").exists()

    def test_get_board_task(
        self, admin_client, admin_profile, admin_user, org_a
    ):
        """Verify a board task appears in the column task list."""
        _board, column = self._create_board_with_column(
            admin_profile, admin_user, org_a
        )
        BoardTask.objects.create(
            column=column,
            title="Existing Card",
            priority="high",
            org=org_a,
            created_by=admin_user,
        )
        response = admin_client.get(f"/api/boards/columns/{column.id}/tasks/")
        assert response.status_code == 200
        data = response.json()
        titles = [t["title"] for t in data]
        assert "Existing Card" in titles

    def test_delete_board_task(
        self, admin_client, admin_profile, admin_user, org_a
    ):
        _board, column = self._create_board_with_column(
            admin_profile, admin_user, org_a
        )
        task = BoardTask.objects.create(
            column=column,
            title="Delete Card",
            priority="low",
            org=org_a,
            created_by=admin_user,
        )
        response = admin_client.delete(f"/api/boards/tasks/{task.id}/")
        assert response.status_code == 204
        assert not BoardTask.objects.filter(id=task.id).exists()
