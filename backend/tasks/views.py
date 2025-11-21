import json

from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Account
from accounts.serializer import AccountSerializer
from common.models import Attachments, Comment, Profile

#from common.external_auth import CustomDualAuthentication
from common.serializer import (
    AttachmentsSerializer,
    CommentSerializer,
    ProfileSerializer,
)
from contacts.models import Contact
from contacts.serializer import ContactSerializer
from tasks import swagger_params
from tasks.models import Task, Board, BoardColumn, BoardTask, BoardMember
from tasks.serializer import (
    TaskSerializer, TaskCreateSerializer, TaskDetailEditSwaggerSerializer,
    TaskCommentEditSwaggerSerializer, TaskCreateSwaggerSerializer,
    BoardSerializer, BoardListSerializer, BoardColumnSerializer,
    BoardTaskSerializer, BoardMemberSerializer
)
from tasks.utils import PRIORITY_CHOICES, STATUS_CHOICES
from common.models import Teams
from common.serializer import TeamsSerializer
from django.shortcuts import get_object_or_404


class TaskListView(APIView, LimitOffsetPagination):
    model = Task
    #authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_context_data(self, **kwargs):
        params = self.request.query_params
        queryset = self.model.objects.filter(org=self.request.profile.org).order_by("-id")
        accounts = Account.objects.filter(org=self.request.profile.org)
        contacts = Contact.objects.filter(org=self.request.profile.org)
        if self.request.profile.role != "ADMIN" and not self.request.profile.is_admin:
            queryset = queryset.filter(
                Q(assigned_to__in=[self.request.profile])
                | Q(created_by=self.request.profile.user)
            )
            accounts = accounts.filter(
                Q(created_by=self.request.profile.user) | Q(assigned_to=self.request.profile)
            ).distinct()
            contacts = contacts.filter(
                Q(created_by=self.request.profile.user) | Q(assigned_to=self.request.profile)
            ).distinct()

        if params:
            if params.get("title"):
                queryset = queryset.filter(title__icontains=params.get("title"))
            if params.get("status"):
                queryset = queryset.filter(status=params.get("status"))
            if params.get("priority"):
                queryset = queryset.filter(priority=params.get("priority"))
        context = {}
        results_tasks = self.paginate_queryset(
            queryset.distinct(), self.request, view=self
        )
        tasks = TaskSerializer(results_tasks, many=True).data
        if results_tasks:
            offset = queryset.filter(id__gte=results_tasks[-1].id).count()
            if offset == queryset.count():
                offset = None
        else:
            offset = 0
        context.update(
            {
                "tasks_count": self.count,
                "offset": offset,
            }
        )
        context["tasks"] = tasks
        context["status"] = STATUS_CHOICES
        context["priority"] = PRIORITY_CHOICES
        context["accounts_list"] = AccountSerializer(accounts, many=True).data
        context["contacts_list"] = ContactSerializer(contacts, many=True).data
        return context

    @extend_schema(
        tags=["Tasks"], parameters=swagger_params.task_list_get_params
    )
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return Response(context)

    @extend_schema(
        tags=["Tasks"], parameters=swagger_params.organization_params,request=TaskCreateSwaggerSerializer
    )
    def post(self, request, *args, **kwargs):
        params = request.data
        serializer = TaskCreateSerializer(data=params, request_obj=request)
        if serializer.is_valid():
            task_obj = serializer.save(
                created_by=request.profile.user,
                due_date=params.get("due_date"),
                org=request.profile.org,
            )
            if params.get("contacts"):
                contacts_list = params.get("contacts")
                contacts = Contact.objects.filter(id__in=contacts_list, org=request.profile.org)
                task_obj.contacts.add(*contacts)

            if params.get("teams"):
                teams_list = params.get("teams")
                teams = Teams.objects.filter(id__in=teams_list, org=request.profile.org)
                task_obj.teams.add(*teams)

            if params.get("assigned_to"):
                assinged_to_list = params.get("assigned_to")
                profiles = Profile.objects.filter(
                    id__in=assinged_to_list, org=request.profile.org, is_active=True
                )
                task_obj.assigned_to.add(*profiles)

            return Response(
                {"error": False, "message": "Task Created Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class TaskDetailView(APIView):
    model = Task
    #authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        return Task.objects.get(pk=pk)

    def get_context_data(self, **kwargs):
        context = {}
        user_assgn_list = [
            assigned_to.id for assigned_to in self.task_obj.assigned_to.all()
        ]
        if self.request.profile == self.task_obj.created_by:
            user_assgn_list.append(self.request.profile.id)
        if self.request.profile.role != "ADMIN" and not self.request.profile.is_admin:
            if self.request.profile.id not in user_assgn_list:
                return Response(
                    {
                        "error": True,
                        "errors": "You don't have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        task_content_type = ContentType.objects.get_for_model(Task)
        comments = Comment.objects.filter(
            content_type=task_content_type,
            object_id=self.task_obj.id
        ).order_by("-id")
        attachments = Attachments.objects.filter(
            content_type=task_content_type,
            object_id=self.task_obj.id
        ).order_by("-id")

        assigned_data = self.task_obj.assigned_to.values("id", "user__email")

        if self.request.profile.is_admin or self.request.profile.role == "ADMIN":
            users_mention = list(
                Profile.objects.filter(is_active=True, org=self.request.profile.org).values(
                    "user__email"
                )
            )
        elif self.request.profile != self.task_obj.created_by:
            users_mention = [{"username": self.task_obj.created_by.user.email}]
        else:
            users_mention = list(
                self.task_obj.assigned_to.all().values("user__email")
            )
        if self.request.profile.role == "ADMIN" or self.request.profile.is_admin:
            users = Profile.objects.filter(
                is_active=True, org=self.request.profile.org
            ).order_by("user__email")
        else:
            users = Profile.objects.filter(role="ADMIN", org=self.request.profile.org).order_by(
                "user__email"
            )

        if self.request.profile == self.task_obj.created_by:
            user_assgn_list.append(self.request.profile.id)
        if self.request.profile.role != "ADMIN" and not self.request.profile.is_admin:
            if self.request.profile.id not in user_assgn_list:
                return Response(
                    {
                        "error": True,
                        "errors": "You don't have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
        team_ids = [user.id for user in self.task_obj.get_team_users]
        all_user_ids = users.values_list("id", flat=True)
        users_excluding_team_id = set(all_user_ids) - set(team_ids)
        users_excluding_team = Profile.objects.filter(id__in=users_excluding_team_id)
        context.update(
            {
                "task_obj": TaskSerializer(self.task_obj).data,
                "attachments": AttachmentsSerializer(attachments, many=True).data,
                "comments": CommentSerializer(comments, many=True).data,
                "users_mention": users_mention,
                "assigned_data": assigned_data,
            }
        )
        context["users"] = ProfileSerializer(users, many=True).data
        context["users_excluding_team"] = ProfileSerializer(
            users_excluding_team, many=True
        ).data
        context["teams"] = TeamsSerializer(Teams.objects.all(), many=True).data
        return context

    @extend_schema(
        tags=["Tasks"], parameters=swagger_params.organization_params
    )
    def get(self, request, pk, **kwargs):
        self.task_obj = self.get_object(pk)
        context = self.get_context_data(**kwargs)
        return Response(context)

    @extend_schema(
        tags=["Tasks"], parameters=swagger_params.organization_params,request=TaskDetailEditSwaggerSerializer
    )
    def post(self, request, pk, **kwargs):
        params = request.data
        context = {}
        self.task_obj = Task.objects.get(pk=pk)
        if self.request.profile.role != "ADMIN" and not self.request.profile.is_admin:
            if not (
                (self.request.profile == self.task_obj.created_by)
                or (self.request.profile in self.task_obj.assigned_to.all())
            ):
                return Response(
                    {
                        "error": True,
                        "errors": "You don't have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
        comment_serializer = CommentSerializer(data=params)
        if comment_serializer.is_valid():
            if params.get("comment"):
                comment_serializer.save(
                    task_id=self.task_obj.id,
                    commented_by_id=self.request.profile.id,
                )

        if self.request.FILES.get("task_attachment"):
            attachment = Attachments()
            attachment.created_by = self.request.profile.user
            attachment.file_name = self.request.FILES.get("task_attachment").name
            attachment.task = self.task_obj
            attachment.attachment = self.request.FILES.get("task_attachment")
            attachment.save()

        task_content_type = ContentType.objects.get_for_model(Task)
        comments = Comment.objects.filter(
            content_type=task_content_type,
            object_id=self.task_obj.id
        ).order_by("-id")
        attachments = Attachments.objects.filter(
            content_type=task_content_type,
            object_id=self.task_obj.id
        ).order_by("-id")
        context.update(
            {
                "task_obj": TaskSerializer(self.task_obj).data,
                "attachments": AttachmentsSerializer(attachments, many=True).data,
                "comments": CommentSerializer(comments, many=True).data,
            }
        )
        return Response(context)

    @extend_schema(
        tags=["Tasks"], parameters=swagger_params.organization_params,request=TaskCreateSwaggerSerializer
    )
    def put(self, request, pk, **kwargs):
        params = request.data
        self.task_obj = self.get_object(pk)
        serializer = TaskCreateSerializer(
            data=params,
            instance=self.task_obj,
            request_obj=request,
        )
        if serializer.is_valid():
            task_obj = serializer.save()
            previous_assigned_to_users = list(
                task_obj.assigned_to.all().values_list("id", flat=True)
            )
            task_obj.contacts.clear()
            if params.get("contacts"):
                contacts_list = params.get("contacts")
                contacts = Contact.objects.filter(id__in=contacts_list, org=request.profile.org)
                task_obj.contacts.add(*contacts)

            task_obj.teams.clear()
            if params.get("teams"):
                teams_list = params.get("teams")
                teams = Teams.objects.filter(id__in=teams_list, org=request.profile.org)
                task_obj.teams.add(*teams)

            task_obj.assigned_to.clear()
            if params.get("assigned_to"):
                assinged_to_list = params.get("assigned_to")
                profiles = Profile.objects.filter(
                    id__in=assinged_to_list, org=request.profile.org, is_active=True
                )
                task_obj.assigned_to.add(*profiles)

            return Response(
                {"error": False, "message": "Task updated Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @extend_schema(
        tags=["Tasks"], parameters=swagger_params.organization_params
    )
    def delete(self, request, pk, **kwargs):
        self.object = self.get_object(pk)
        if (
            request.profile.role == "ADMIN"
            or request.profile.is_admin
            or request.profile == self.object.created_by
        ):
            self.object.delete()
            return Response(
                {"error": False, "message": "Task deleted Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": "you don't have permission to delete this task"},
            status=status.HTTP_403_FORBIDDEN,
        )


class TaskCommentView(APIView):
    model = Comment
    #authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        return self.model.objects.get(pk=pk)

    @extend_schema(
        tags=["Tasks"], parameters=swagger_params.organization_params,request=TaskCommentEditSwaggerSerializer
    )
    def put(self, request, pk, format=None):
        params = request.data
        obj = self.get_object(pk)
        if (
            request.profile.role == "ADMIN"
            or request.profile.is_admin
            or request.profile == obj.commented_by
        ):
            serializer = CommentSerializer(obj, data=params)
            if params.get("comment"):
                if serializer.is_valid():
                    serializer.save()
                    return Response(
                        {"error": False, "message": "Comment Submitted"},
                        status=status.HTTP_200_OK,
                    )
                return Response(
                    {"error": True, "errors": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(
            {
                "error": True,
                "errors": "You don't have Permission to perform this action",
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    @extend_schema(
        tags=["Tasks"], parameters=swagger_params.organization_params
    )
    def delete(self, request, pk, format=None):
        self.object = self.get_object(pk)
        if (
            request.profile.role == "ADMIN"
            or request.profile.is_admin
            or request.profile == self.object.commented_by
        ):
            self.object.delete()
            return Response(
                {"error": False, "message": "Comment Deleted Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "error": True,
                "errors": "You don't have Permission to perform this action",
            },
            status=status.HTTP_403_FORBIDDEN,
        )


class TaskAttachmentView(APIView):
    model = Attachments
    #authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["Tasks"], parameters=swagger_params.organization_params
    )
    def delete(self, request, pk, format=None):
        self.object = self.model.objects.get(pk=pk)
        if (
            request.profile.role == "ADMIN"
            or request.profile.is_admin
            or request.profile == self.object.created_by
        ):
            self.object.delete()
            return Response(
                {"error": False, "message": "Attachment Deleted Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "error": True,
                "errors": "You don't have Permission to perform this action",
            },
            status=status.HTTP_403_FORBIDDEN,
        )


# =============================================================================
# Kanban Board Views (merged from boards app)
# =============================================================================

class BoardListCreateView(APIView, LimitOffsetPagination):
    """List all boards or create a new board"""

    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["Boards"],
        parameters=[
            OpenApiParameter(name="org", description="Organization ID", required=True, type=str),
            OpenApiParameter(name="search", description="Search in board name", required=False, type=str),
            OpenApiParameter(name="archived", description="Filter archived boards", required=False, type=bool),
        ],
        responses={200: BoardListSerializer(many=True)}
    )
    def get(self, request):
        """List all boards for the user's organization"""
        org = request.profile.org
        user_profile = request.profile

        # Get boards where user is owner or member
        queryset = Board.objects.filter(
            Q(org=org) &
            (Q(owner=user_profile) | Q(members=user_profile))
        ).distinct().order_by('-created_at')

        # Filtering
        archived = request.query_params.get('archived')
        if archived is not None:
            is_archived = archived.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(is_archived=is_archived)

        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)

        # Pagination
        results = self.paginate_queryset(queryset, request, view=self)
        serializer = BoardListSerializer(results, many=True)

        return Response({
            'count': self.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': serializer.data
        })

    @extend_schema(
        tags=["Boards"],
        parameters=[OpenApiParameter(name="org", description="Organization ID", required=True, type=str)],
        request=BoardSerializer,
        responses={201: BoardSerializer}
    )
    def post(self, request):
        """Create a new board with default columns"""
        org = request.profile.org
        user_profile = request.profile
        data = request.data.copy()

        serializer = BoardSerializer(data=data)
        if not serializer.is_valid():
            return Response(
                {'error': True, 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create board
        board = serializer.save(
            org=org,
            owner=user_profile,
            created_by=request.user
        )

        # Add owner as member with owner role
        BoardMember.objects.create(
            board=board,
            profile=user_profile,
            role='owner'
        )

        # Create default columns if requested
        if request.data.get('create_default_columns', True):
            default_columns = [
                {'name': 'To Do', 'order': 1, 'color': '#EF4444'},
                {'name': 'In Progress', 'order': 2, 'color': '#F59E0B'},
                {'name': 'Done', 'order': 3, 'color': '#10B981'},
            ]
            for col_data in default_columns:
                BoardColumn.objects.create(board=board, **col_data)

        return Response(
            BoardSerializer(board).data,
            status=status.HTTP_201_CREATED
        )


class BoardDetailView(APIView):
    """Retrieve, update or delete a board"""

    permission_classes = (IsAuthenticated,)

    def get_object(self, pk, org, user_profile):
        """Get board if user has access"""
        board = get_object_or_404(Board, pk=pk, org=org)
        # Check if user is owner or member
        if board.owner != user_profile and not board.members.filter(id=user_profile.id).exists():
            return None
        return board

    @extend_schema(
        tags=["Boards"],
        parameters=[OpenApiParameter(name="org", description="Organization ID", required=True, type=str)],
        responses={200: BoardSerializer}
    )
    def get(self, request, pk):
        """Get board details with columns and tasks"""
        board = self.get_object(pk, request.profile.org, request.profile)
        if not board:
            return Response(
                {'error': 'Board not found or access denied'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = BoardSerializer(board)
        return Response(serializer.data)

    @extend_schema(
        tags=["Boards"],
        parameters=[OpenApiParameter(name="org", description="Organization ID", required=True, type=str)],
        request=BoardSerializer,
        responses={200: BoardSerializer}
    )
    def put(self, request, pk):
        """Update board"""
        board = self.get_object(pk, request.profile.org, request.profile)
        if not board:
            return Response(
                {'error': 'Board not found or access denied'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Only owner or admin can update board
        membership = BoardMember.objects.filter(board=board, profile=request.profile).first()
        if not membership or membership.role not in ['owner', 'admin']:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = BoardSerializer(board, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(
                {'error': True, 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        board = serializer.save(updated_by=request.user)
        return Response(BoardSerializer(board).data)

    @extend_schema(
        tags=["Boards"],
        parameters=[OpenApiParameter(name="org", description="Organization ID", required=True, type=str)],
        responses={204: None}
    )
    def delete(self, request, pk):
        """Delete board (owner only)"""
        board = self.get_object(pk, request.profile.org, request.profile)
        if not board:
            return Response(
                {'error': 'Board not found or access denied'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Only owner can delete
        if board.owner != request.profile:
            return Response(
                {'error': 'Only board owner can delete the board'},
                status=status.HTTP_403_FORBIDDEN
            )

        board.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BoardColumnListCreateView(APIView):
    """List or create columns for a board"""

    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["Boards"],
        parameters=[OpenApiParameter(name="org", description="Organization ID", required=True, type=str)],
        responses={200: BoardColumnSerializer(many=True)}
    )
    def get(self, request, board_pk):
        """List all columns for a board"""
        org = request.profile.org
        board = get_object_or_404(Board, pk=board_pk, org=org)

        # Check access
        if board.owner != request.profile and not board.members.filter(id=request.profile.id).exists():
            return Response(
                {'error': 'Board not found or access denied'},
                status=status.HTTP_404_NOT_FOUND
            )

        columns = board.columns.all()
        serializer = BoardColumnSerializer(columns, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["Boards"],
        parameters=[OpenApiParameter(name="org", description="Organization ID", required=True, type=str)],
        request=BoardColumnSerializer,
        responses={201: BoardColumnSerializer}
    )
    def post(self, request, board_pk):
        """Create a new column"""
        org = request.profile.org
        board = get_object_or_404(Board, pk=board_pk, org=org)

        # Check permission
        membership = BoardMember.objects.filter(board=board, profile=request.profile).first()
        if not membership or membership.role not in ['owner', 'admin']:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        data = request.data.copy()
        serializer = BoardColumnSerializer(data=data)
        if not serializer.is_valid():
            return Response(
                {'error': True, 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        column = serializer.save(board=board, created_by=request.user)
        return Response(
            BoardColumnSerializer(column).data,
            status=status.HTTP_201_CREATED
        )


class BoardTaskListCreateView(APIView):
    """List or create tasks for a column"""

    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["Boards"],
        parameters=[OpenApiParameter(name="org", description="Organization ID", required=True, type=str)],
        responses={200: BoardTaskSerializer(many=True)}
    )
    def get(self, request, column_pk):
        """List all tasks for a column"""
        org = request.profile.org
        column = get_object_or_404(BoardColumn, pk=column_pk, board__org=org)

        # Check access
        board = column.board
        if board.owner != request.profile and not board.members.filter(id=request.profile.id).exists():
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_404_NOT_FOUND
            )

        tasks = column.tasks.all()
        serializer = BoardTaskSerializer(tasks, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["Boards"],
        parameters=[OpenApiParameter(name="org", description="Organization ID", required=True, type=str)],
        request=BoardTaskSerializer,
        responses={201: BoardTaskSerializer}
    )
    def post(self, request, column_pk):
        """Create a new task"""
        org = request.profile.org
        column = get_object_or_404(BoardColumn, pk=column_pk, board__org=org)

        # Check access
        board = column.board
        membership = BoardMember.objects.filter(board=board, profile=request.profile).first()
        if not membership:
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        data = request.data.copy()
        serializer = BoardTaskSerializer(data=data)
        if not serializer.is_valid():
            return Response(
                {'error': True, 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        task = serializer.save(column=column, created_by=request.user)

        # Handle assigned_to
        if 'assigned_to_ids' in data:
            profiles = Profile.objects.filter(id__in=data['assigned_to_ids'], org=org)
            task.assigned_to.set(profiles)

        return Response(
            BoardTaskSerializer(task).data,
            status=status.HTTP_201_CREATED
        )


class BoardTaskDetailView(APIView):
    """Retrieve, update or delete a task"""

    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["Boards"],
        parameters=[OpenApiParameter(name="org", description="Organization ID", required=True, type=str)],
        request=BoardTaskSerializer,
        responses={200: BoardTaskSerializer}
    )
    def put(self, request, pk):
        """Update task (including moving to different column)"""
        org = request.profile.org
        task = get_object_or_404(BoardTask, pk=pk, column__board__org=org)

        # Check access
        board = task.column.board
        membership = BoardMember.objects.filter(board=board, profile=request.profile).first()
        if not membership:
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        data = request.data.copy()
        serializer = BoardTaskSerializer(task, data=data, partial=True)
        if not serializer.is_valid():
            return Response(
                {'error': True, 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        task = serializer.save(updated_by=request.user)

        # Handle assigned_to
        if 'assigned_to_ids' in data:
            profiles = Profile.objects.filter(id__in=data['assigned_to_ids'], org=org)
            task.assigned_to.set(profiles)

        return Response(BoardTaskSerializer(task).data)

    @extend_schema(
        tags=["Boards"],
        parameters=[OpenApiParameter(name="org", description="Organization ID", required=True, type=str)],
        responses={204: None}
    )
    def delete(self, request, pk):
        """Delete task"""
        org = request.profile.org
        task = get_object_or_404(BoardTask, pk=pk, column__board__org=org)

        # Check permission
        board = task.column.board
        membership = BoardMember.objects.filter(board=board, profile=request.profile).first()
        if not membership or membership.role not in ['owner', 'admin', 'member']:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
