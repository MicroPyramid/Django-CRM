from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from accounts.models import Account
from accounts.serializer import AccountSerializer
from contacts.models import Contact
from contacts.serializer import ContactSerializer

from common.models import Profile, Attachments, Comment
from common.custom_auth import JSONWebTokenAuthentication
from common.serializer import (
    ProfileSerializer,
    CommentSerializer,
    AttachmentsSerializer,
    CommentSerializer,
)
from tasks import swagger_params
from tasks.models import Task
from tasks.serializer import TaskSerializer, TaskCreateSerializer
from tasks.utils import STATUS_CHOICES, PRIORITY_CHOICES
from teams.serializer import TeamsSerializer
from teams.models import Teams
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import LimitOffsetPagination
from drf_yasg.utils import swagger_auto_schema
import json


class TaskListView(APIView, LimitOffsetPagination):
    model = Task
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_context_data(self, **kwargs):
        params = (
            self.request.query_params
            if len(self.request.data) == 0
            else self.request.data
        )
        queryset = self.model.objects.filter(org=self.request.org)
        accounts = Account.objects.filter(org=self.request.org)
        contacts = Contact.objects.filter(org=self.request.org)
        if self.request.profile.role != "ADMIN" and not self.request.profile.is_admin:
            queryset = queryset.filter(
                Q(assigned_to__in=[self.request.profile]) | Q(created_by=self.request.profile)
            )
            accounts = accounts.filter(
                Q(created_by=self.request.profile) | Q(assigned_to=self.request.profile)
            ).distinct()
            contacts = contacts.filter(
                Q(created_by=self.request.profile) | Q(assigned_to=self.request.profile)
            ).distinct()

        request_post = params
        if request_post:
            if request_post.get("title"):
                queryset = queryset.filter(title__icontains=request_post.get("title"))
            if request_post.get("status"):
                queryset = queryset.filter(status=request_post.get("status"))
            if request_post.get("priority"):
                queryset = queryset.filter(priority=request_post.get("priority"))
        context = {}
        search = False
        if params.get("title") or params.get("status") or params.get("priority"):
            search = True
        context["search"] = search
        results_tasks = self.paginate_queryset(
            queryset.distinct(), self.request, view=self
        )
        tasks = TaskSerializer(results_tasks, many=True).data
        context["per_page"] = 10
        context.update(
            {
                "tasks_count": self.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "page_number": int(self.offset / 10) + 1,
            }
        )
        context["tasks"] = tasks
        context["status"] = STATUS_CHOICES
        context["priority"] = PRIORITY_CHOICES
        users = []
        if self.request.profile.role == "ADMIN" or self.request.profile.is_admin:
            users = Profile.objects.filter(
                is_active=True, org=self.request.org
            ).order_by("user__email")
        elif self.request.profile.google.all():
            users = []
        else:
            users = Profile.objects.filter(
                role="ADMIN", org=self.request.org
            ).order_by("user__email")
        context["users"] = ProfileSerializer(users, many=True).data
        if self.request.profile == "ADMIN":
            context["teams_list"] = TeamsSerializer(Teams.objects.filter(
                org=self.request.org), many=True).data
        context["accounts_list"] = AccountSerializer(accounts, many=True).data
        context["contacts_list"] = ContactSerializer(contacts, many=True).data
        return context

    @swagger_auto_schema(
        tags=["Tasks"], manual_parameters=swagger_params.task_list_get_params
    )
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return Response(context)

    @swagger_auto_schema(
        tags=["Tasks"], manual_parameters=swagger_params.task_create_post_params
    )
    def post(self, request, *args, **kwargs):
        params = (
            self.request.query_params
            if len(self.request.data) == 0
            else self.request.data
        )
        data = {}
        serializer = TaskCreateSerializer(data=params, request_obj=request)
        if serializer.is_valid():
            task_obj = serializer.save(
                created_by=request.profile,
                due_date=params.get("due_date"),
                org=request.org
            )
            if params.get("contacts"):
                contacts = json.loads(params.get("contacts"))
                for contact in contacts:
                    obj_contact = Contact.objects.filter(
                        id=contact, org=request.org
                    )
                    if obj_contact.exists():
                        task_obj.contacts.add(contact)
                    else:
                        task_obj.delete()
                        data["contacts"] = "Please enter valid contact"
                        return Response(
                            {"error": True, "errors": data},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
            if self.request.profile.role == "ADMIN":
                if params.get("teams"):
                    teams = json.loads(params.get("teams"))
                    for team in teams:
                        teams_ids = Teams.objects.filter(id=team, org=request.org)
                        if teams_ids.exists():
                            task_obj.teams.add(team)
                        else:
                            task_obj.delete()
                            data["team"] = "Please enter valid Team"
                            return Response(
                                {"error": True, "errors": data},
                                status=status.HTTP_400_BAD_REQUEST,
                            )
                if params.get("assigned_to"):
                    assinged_to_users_ids = json.loads(params.get("assigned_to"))
                    for user_id in assinged_to_users_ids:
                        profile = Profile.objects.filter(id=user_id, org=request.org)
                        if profile.exists():
                            task_obj.assigned_to.add(user_id)
                        else:
                            task_obj.delete()
                            data["assigned_to"] = "Please enter valid User"
                            return Response(
                                {"error": True, "errors": data},
                                status=status.HTTP_400_BAD_REQUEST,
                            )

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
    authentication_classes = (JSONWebTokenAuthentication,)
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
                Profile.objects.filter(
                    is_active=True, org=self.request.org
                ).values("user__username")
            )
        elif self.request.profile != self.task_obj.created_by:
            users_mention = [{"username": self.task_obj.created_by.user.username}]
        else:
            users_mention = list(self.task_obj.assigned_to.all().values("user__username"))
        if self.request.profile.role == "ADMIN" or self.request.profile.is_admin:
            users = Profile.objects.filter(
                is_active=True, org=self.request.org
            ).order_by("user__email")
        else:
            users = Profile.objects.filter(
                role="ADMIN", org=self.request.org
            ).order_by("user__email")

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

    @swagger_auto_schema(
        tags=["Tasks"], manual_parameters=swagger_params.organization_params
    )
    def get(self, request, pk, **kwargs):
        self.task_obj = self.get_object(pk)
        context = self.get_context_data(**kwargs)
        return Response(context)

    @swagger_auto_schema(
        tags=["Tasks"], manual_parameters=swagger_params.task_detail_post_params
    )
    def post(self, request, pk, **kwargs):
        params = (
            self.request.query_params
            if len(self.request.data) == 0
            else self.request.data
        )
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
            attachment.created_by = self.request.profile
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

    @swagger_auto_schema(
        tags=["Tasks"], manual_parameters=swagger_params.task_create_post_params
    )
    def put(self, request, pk, **kwargs):
        params = (
            self.request.query_params
            if len(self.request.data) == 0
            else self.request.data
        )
        data = {}
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
                contacts = json.loads(params.get("contacts"))
                for contact in contacts:
                    obj_contact = Contact.objects.filter(id=contact)
                    if obj_contact.exists():
                        task_obj.contacts.add(contact)
                    else:
                        data["contacts"] = "Please enter valid Contact"
                        return Response(
                            {"error": True, "errors": data},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
            if self.request.profile.role == "ADMIN":
                task_obj.teams.clear()
                if params.get("teams"):
                    teams = json.loads(params.get("teams"))
                    for team in teams:
                        teams_ids = Teams.objects.filter(id=team)
                        if teams_ids.exists():
                            task_obj.teams.add(team)
                        else:
                            task_obj.delete()
                            data["team"] = "Please enter valid Team"
                            return Response(
                                {"error": True, "errors": data},
                                status=status.HTTP_400_BAD_REQUEST,
                            )
                else:
                    task_obj.teams.clear()

                task_obj.assigned_to.clear()
                if params.get("assigned_to"):
                    assinged_to_users_ids = json.loads(params.get("assigned_to"))
                    for user_id in assinged_to_users_ids:
                        profile = Profile.objects.filter(id=user_id, org=request.org)
                        if profile.exists():
                            task_obj.assigned_to.add(user_id)
                        else:
                            task_obj.delete()
                            data["assigned_to"] = "Please enter valid User"
                            return Response(
                                {"error": True, "errors": data},
                                status=status.HTTP_400_BAD_REQUEST,
                            )
                else:
                    task_obj.assigned_to.clear()
            return Response(
                {"error": False, "message": "Task updated Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @swagger_auto_schema(
        tags=["Tasks"], manual_parameters=swagger_params.organization_params
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
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        return self.model.objects.get(pk=pk)

    @swagger_auto_schema(
        tags=["Tasks"], manual_parameters=swagger_params.task_comment_edit_params
    )
    def put(self, request, pk, format=None):
        params = request.query_params if len(request.data) == 0 else request.data
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
        else:
            return Response(
                {
                    "error": True,
                    "errors": "You don't have Permission to perform this action",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

    @swagger_auto_schema(
        tags=["Tasks"], manual_parameters=swagger_params.organization_params
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
        else:
            return Response(
                {
                    "error": True,
                    "errors": "You don't have Permission to perform this action",
                },
                status=status.HTTP_403_FORBIDDEN,
            )


class TaskAttachmentView(APIView):
    model = Attachments
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        tags=["Tasks"], manual_parameters=swagger_params.organization_params
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
        else:
            return Response(
                {
                    "error": True,
                    "errors": "You don't have Permission to perform this action",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
