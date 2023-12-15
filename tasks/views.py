import json

from django.db.models import Q
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
from tasks import swagger_params1
from tasks.models import Task
from tasks.serializer import *
from tasks.utils import PRIORITY_CHOICES, STATUS_CHOICES
from teams.models import Teams
from teams.serializer import TeamsSerializer


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
        tags=["Tasks"], parameters=swagger_params1.task_list_get_params
    )
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return Response(context)

    @extend_schema(
        tags=["Tasks"], parameters=swagger_params1.organization_params,request=TaskCreateSwaggerSerializer
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

        comments = Comment.objects.filter(task=self.task_obj).order_by("-id")
        attachments = Attachments.objects.filter(task=self.task_obj).order_by("-id")

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
        tags=["Tasks"], parameters=swagger_params1.organization_params
    )
    def get(self, request, pk, **kwargs):
        self.task_obj = self.get_object(pk)
        context = self.get_context_data(**kwargs)
        return Response(context)

    @extend_schema(
        tags=["Tasks"], parameters=swagger_params1.organization_params,request=TaskDetailEditSwaggerSerializer
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

        comments = Comment.objects.filter(task__id=self.task_obj.id).order_by("-id")
        attachments = Attachments.objects.filter(task__id=self.task_obj.id).order_by(
            "-id"
        )
        context.update(
            {
                "task_obj": TaskSerializer(self.task_obj).data,
                "attachments": AttachmentsSerializer(attachments, many=True).data,
                "comments": CommentSerializer(comments, many=True).data,
            }
        )
        return Response(context)

    @extend_schema(
        tags=["Tasks"], parameters=swagger_params1.organization_params,request=TaskCreateSwaggerSerializer
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
        tags=["Tasks"], parameters=swagger_params1.organization_params
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
        tags=["Tasks"], parameters=swagger_params1.organization_params,request=TaskCommentEditSwaggerSerializer
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
        tags=["Tasks"], parameters=swagger_params1.organization_params
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
        tags=["Tasks"], parameters=swagger_params1.organization_params
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
