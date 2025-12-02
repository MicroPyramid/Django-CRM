from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.models import Profile
from common.permissions import HasOrgContext
from tasks.models import Board, BoardColumn, BoardMember, BoardTask
from tasks.serializer import (
    BoardColumnSerializer,
    BoardListSerializer,
    BoardSerializer,
    BoardTaskSerializer,
)


class BoardListCreateView(APIView, LimitOffsetPagination):
    """List all boards or create a new board"""

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(
        tags=["Boards"],
        parameters=[
            OpenApiParameter(
                name="org", description="Organization ID", required=True, type=str
            ),
            OpenApiParameter(
                name="search",
                description="Search in board name",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="archived",
                description="Filter archived boards",
                required=False,
                type=bool,
            ),
        ],
        responses={200: BoardListSerializer(many=True)},
    )
    def get(self, request):
        """List all boards for the user's organization"""
        org = request.profile.org
        user_profile = request.profile

        # Get boards where user is owner or member
        queryset = (
            Board.objects.filter(
                Q(org=org) & (Q(owner=user_profile) | Q(members=user_profile))
            )
            .distinct()
            .order_by("-created_at")
        )

        # Filtering
        archived = request.query_params.get("archived")
        if archived is not None:
            is_archived = archived.lower() in ["true", "1", "yes"]
            queryset = queryset.filter(is_archived=is_archived)

        search = request.query_params.get("search")
        if search:
            queryset = queryset.filter(name__icontains=search)

        # Pagination
        results = self.paginate_queryset(queryset, request, view=self)
        serializer = BoardListSerializer(results, many=True)

        return Response(
            {
                "count": self.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": serializer.data,
            }
        )

    @extend_schema(
        tags=["Boards"],
        parameters=[
            OpenApiParameter(
                name="org", description="Organization ID", required=True, type=str
            )
        ],
        request=BoardSerializer,
        responses={201: BoardSerializer},
    )
    def post(self, request):
        """Create a new board with default columns"""
        org = request.profile.org
        user_profile = request.profile
        data = request.data.copy()

        serializer = BoardSerializer(data=data)
        if not serializer.is_valid():
            return Response(
                {"error": True, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create board
        board = serializer.save(org=org, owner=user_profile, created_by=request.user)

        # Add owner as member with owner role
        BoardMember.objects.create(board=board, profile=user_profile, role="owner")

        # Create default columns if requested
        if request.data.get("create_default_columns", True):
            default_columns = [
                {"name": "To Do", "order": 1, "color": "#EF4444"},
                {"name": "In Progress", "order": 2, "color": "#F59E0B"},
                {"name": "Done", "order": 3, "color": "#10B981"},
            ]
            for col_data in default_columns:
                BoardColumn.objects.create(board=board, **col_data)

        return Response(BoardSerializer(board).data, status=status.HTTP_201_CREATED)


class BoardDetailView(APIView):
    """Retrieve, update or delete a board"""

    permission_classes = (IsAuthenticated, HasOrgContext)

    def get_object(self, pk, org, user_profile):
        """Get board if user has access"""
        board = get_object_or_404(Board, pk=pk, org=org)
        # Check if user is owner or member
        if (
            board.owner != user_profile
            and not board.members.filter(id=user_profile.id).exists()
        ):
            return None
        return board

    @extend_schema(
        tags=["Boards"],
        parameters=[
            OpenApiParameter(
                name="org", description="Organization ID", required=True, type=str
            )
        ],
        responses={200: BoardSerializer},
    )
    def get(self, request, pk):
        """Get board details with columns and tasks"""
        board = self.get_object(pk, request.profile.org, request.profile)
        if not board:
            return Response(
                {"error": "Board not found or access denied"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = BoardSerializer(board)
        return Response(serializer.data)

    @extend_schema(
        tags=["Boards"],
        parameters=[
            OpenApiParameter(
                name="org", description="Organization ID", required=True, type=str
            )
        ],
        request=BoardSerializer,
        responses={200: BoardSerializer},
    )
    def put(self, request, pk):
        """Update board"""
        board = self.get_object(pk, request.profile.org, request.profile)
        if not board:
            return Response(
                {"error": "Board not found or access denied"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Only owner or admin can update board
        membership = BoardMember.objects.filter(
            board=board, profile=request.profile
        ).first()
        if not membership or membership.role not in ["owner", "admin"]:
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        serializer = BoardSerializer(board, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(
                {"error": True, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        board = serializer.save(updated_by=request.user)
        return Response(BoardSerializer(board).data)

    @extend_schema(
        tags=["Boards"],
        parameters=[
            OpenApiParameter(
                name="org", description="Organization ID", required=True, type=str
            )
        ],
        request=BoardSerializer,
        responses={200: BoardSerializer},
        description="Partial Board Update",
    )
    def patch(self, request, pk):
        """Handle partial updates to a board."""
        board = self.get_object(pk, request.profile.org, request.profile)
        if not board:
            return Response(
                {"error": "Board not found or access denied"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Only owner or admin can update board
        membership = BoardMember.objects.filter(
            board=board, profile=request.profile
        ).first()
        if not membership or membership.role not in ["owner", "admin"]:
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        serializer = BoardSerializer(board, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(
                {"error": True, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        board = serializer.save(updated_by=request.user)
        return Response(BoardSerializer(board).data)

    @extend_schema(
        tags=["Boards"],
        parameters=[
            OpenApiParameter(
                name="org", description="Organization ID", required=True, type=str
            )
        ],
        responses={204: None},
    )
    def delete(self, request, pk):
        """Delete board (owner only)"""
        board = self.get_object(pk, request.profile.org, request.profile)
        if not board:
            return Response(
                {"error": "Board not found or access denied"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Only owner can delete
        if board.owner != request.profile:
            return Response(
                {"error": "Only board owner can delete the board"},
                status=status.HTTP_403_FORBIDDEN,
            )

        board.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BoardColumnListCreateView(APIView):
    """List or create columns for a board"""

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(
        tags=["Boards"],
        parameters=[
            OpenApiParameter(
                name="org", description="Organization ID", required=True, type=str
            )
        ],
        responses={200: BoardColumnSerializer(many=True)},
    )
    def get(self, request, board_pk):
        """List all columns for a board"""
        org = request.profile.org
        board = get_object_or_404(Board, pk=board_pk, org=org)

        # Check access
        if (
            board.owner != request.profile
            and not board.members.filter(id=request.profile.id).exists()
        ):
            return Response(
                {"error": "Board not found or access denied"},
                status=status.HTTP_404_NOT_FOUND,
            )

        columns = board.columns.all()
        serializer = BoardColumnSerializer(columns, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["Boards"],
        parameters=[
            OpenApiParameter(
                name="org", description="Organization ID", required=True, type=str
            )
        ],
        request=BoardColumnSerializer,
        responses={201: BoardColumnSerializer},
    )
    def post(self, request, board_pk):
        """Create a new column"""
        org = request.profile.org
        board = get_object_or_404(Board, pk=board_pk, org=org)

        # Check permission
        membership = BoardMember.objects.filter(
            board=board, profile=request.profile
        ).first()
        if not membership or membership.role not in ["owner", "admin"]:
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        data = request.data.copy()
        serializer = BoardColumnSerializer(data=data)
        if not serializer.is_valid():
            return Response(
                {"error": True, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        column = serializer.save(board=board, created_by=request.user)
        return Response(
            BoardColumnSerializer(column).data, status=status.HTTP_201_CREATED
        )


class BoardTaskListCreateView(APIView):
    """List or create tasks for a column"""

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(
        tags=["Boards"],
        parameters=[
            OpenApiParameter(
                name="org", description="Organization ID", required=True, type=str
            )
        ],
        responses={200: BoardTaskSerializer(many=True)},
    )
    def get(self, request, column_pk):
        """List all tasks for a column"""
        org = request.profile.org
        column = get_object_or_404(BoardColumn, pk=column_pk, board__org=org)

        # Check access
        board = column.board
        if (
            board.owner != request.profile
            and not board.members.filter(id=request.profile.id).exists()
        ):
            return Response(
                {"error": "Access denied"}, status=status.HTTP_404_NOT_FOUND
            )

        tasks = column.tasks.all()
        serializer = BoardTaskSerializer(tasks, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["Boards"],
        parameters=[
            OpenApiParameter(
                name="org", description="Organization ID", required=True, type=str
            )
        ],
        request=BoardTaskSerializer,
        responses={201: BoardTaskSerializer},
    )
    def post(self, request, column_pk):
        """Create a new task"""
        org = request.profile.org
        column = get_object_or_404(BoardColumn, pk=column_pk, board__org=org)

        # Check access
        board = column.board
        membership = BoardMember.objects.filter(
            board=board, profile=request.profile
        ).first()
        if not membership:
            return Response(
                {"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN
            )

        data = request.data.copy()
        serializer = BoardTaskSerializer(data=data)
        if not serializer.is_valid():
            return Response(
                {"error": True, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        task = serializer.save(column=column, created_by=request.user)

        # Handle assigned_to
        if "assigned_to_ids" in data:
            profiles = Profile.objects.filter(id__in=data["assigned_to_ids"], org=org)
            task.assigned_to.set(profiles)

        return Response(BoardTaskSerializer(task).data, status=status.HTTP_201_CREATED)


class BoardTaskDetailView(APIView):
    """Retrieve, update or delete a task"""

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(
        tags=["Boards"],
        parameters=[
            OpenApiParameter(
                name="org", description="Organization ID", required=True, type=str
            )
        ],
        request=BoardTaskSerializer,
        responses={200: BoardTaskSerializer},
    )
    def put(self, request, pk):
        """Update task (including moving to different column)"""
        org = request.profile.org
        task = get_object_or_404(BoardTask, pk=pk, column__board__org=org)

        # Check access
        board = task.column.board
        membership = BoardMember.objects.filter(
            board=board, profile=request.profile
        ).first()
        if not membership:
            return Response(
                {"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN
            )

        data = request.data.copy()
        serializer = BoardTaskSerializer(task, data=data, partial=True)
        if not serializer.is_valid():
            return Response(
                {"error": True, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        task = serializer.save(updated_by=request.user)

        # Handle assigned_to
        if "assigned_to_ids" in data:
            profiles = Profile.objects.filter(id__in=data["assigned_to_ids"], org=org)
            task.assigned_to.set(profiles)

        return Response(BoardTaskSerializer(task).data)

    @extend_schema(
        tags=["Boards"],
        parameters=[
            OpenApiParameter(
                name="org", description="Organization ID", required=True, type=str
            )
        ],
        responses={204: None},
    )
    def delete(self, request, pk):
        """Delete task"""
        org = request.profile.org
        task = get_object_or_404(BoardTask, pk=pk, column__board__org=org)

        # Check permission
        board = task.column.board
        membership = BoardMember.objects.filter(
            board=board, profile=request.profile
        ).first()
        if not membership or membership.role not in ["owner", "admin", "member"]:
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
