import json

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Account
from accounts.serializer import AccountSerializer
from common.models import Attachments, Comment, Profile, Tags, Teams
from common.permissions import HasOrgContext
from common.serializer import (
    AttachmentsSerializer,
    CommentSerializer,
    ProfileSerializer,
    TeamsSerializer,
)
from contacts.models import Contact
from contacts.serializer import ContactSerializer
from tasks import swagger_params
from tasks.models import Task
from tasks.serializer import (
    TaskCommentEditSwaggerSerializer,
    TaskCreateSerializer,
    TaskCreateSwaggerSerializer,
    TaskDetailEditSwaggerSerializer,
    TaskSerializer,
)
from tasks.utils import PRIORITY_CHOICES, STATUS_CHOICES


class TaskListView(APIView, LimitOffsetPagination):
    model = Task
    permission_classes = (IsAuthenticated, HasOrgContext)

    def get_context_data(self, **kwargs):
        params = self.request.query_params
        queryset = self.model.objects.filter(org=self.request.profile.org).order_by(
            "-id"
        )
        accounts = Account.objects.filter(org=self.request.profile.org)
        contacts = Contact.objects.filter(org=self.request.profile.org)
        if self.request.profile.role != "ADMIN" and not self.request.profile.is_admin:
            queryset = queryset.filter(
                Q(assigned_to__in=[self.request.profile])
                | Q(created_by=self.request.profile.user)
            )
            accounts = accounts.filter(
                Q(created_by=self.request.profile.user)
                | Q(assigned_to=self.request.profile)
            ).distinct()
            contacts = contacts.filter(
                Q(created_by=self.request.profile.user)
                | Q(assigned_to=self.request.profile)
            ).distinct()

        if params:
            if params.get("title"):
                queryset = queryset.filter(title__icontains=params.get("title"))
            if params.get("status"):
                queryset = queryset.filter(status=params.get("status"))
            if params.get("priority"):
                queryset = queryset.filter(priority=params.get("priority"))
            if params.getlist("assigned_to"):
                queryset = queryset.filter(
                    assigned_to__id__in=params.getlist("assigned_to")
                ).distinct()
            if params.get("tags"):
                queryset = queryset.filter(
                    tags__id__in=params.getlist("tags")
                ).distinct()
            if params.get("search"):
                queryset = queryset.filter(title__icontains=params.get("search"))
            if params.get("due_date__gte"):
                queryset = queryset.filter(due_date__gte=params.get("due_date__gte"))
            if params.get("due_date__lte"):
                queryset = queryset.filter(due_date__lte=params.get("due_date__lte"))
            if params.get("created_at__gte"):
                queryset = queryset.filter(
                    created_at__gte=params.get("created_at__gte")
                )
            if params.get("created_at__lte"):
                queryset = queryset.filter(
                    created_at__lte=params.get("created_at__lte")
                )
            if params.get("account"):
                queryset = queryset.filter(account_id=params.get("account"))
            if params.get("opportunity"):
                queryset = queryset.filter(opportunity_id=params.get("opportunity"))
            if params.get("case"):
                queryset = queryset.filter(case_id=params.get("case"))
            if params.get("lead"):
                queryset = queryset.filter(lead_id=params.get("lead"))
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
        tags=["Tasks"],
        operation_id="tasks_list",
        parameters=swagger_params.task_list_get_params,
        responses={
            200: inline_serializer(
                name="TaskListResponse",
                fields={
                    "tasks_count": serializers.IntegerField(),
                    "offset": serializers.IntegerField(allow_null=True),
                    "tasks": TaskSerializer(many=True),
                    "status": serializers.ListField(),
                    "priority": serializers.ListField(),
                    "accounts_list": AccountSerializer(many=True),
                    "contacts_list": ContactSerializer(many=True),
                },
            )
        },
    )
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return Response(context)

    @extend_schema(
        tags=["Tasks"],
        operation_id="tasks_create",
        parameters=swagger_params.organization_params,
        request=TaskCreateSwaggerSerializer,
        responses={
            200: inline_serializer(
                name="TaskCreateResponse",
                fields={
                    "error": serializers.BooleanField(),
                    "message": serializers.CharField(),
                },
            )
        },
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
                if isinstance(contacts_list, str):
                    contacts_list = json.loads(contacts_list)
                # Extract IDs if contacts_list contains objects with 'id' field
                contact_ids = [
                    item.get("id") if isinstance(item, dict) else item
                    for item in contacts_list
                ]
                contacts = Contact.objects.filter(
                    id__in=contact_ids, org=request.profile.org
                )
                task_obj.contacts.add(*contacts)

            if params.get("teams"):
                teams_list = params.get("teams")
                if isinstance(teams_list, str):
                    teams_list = json.loads(teams_list)
                # Extract IDs if teams_list contains objects with 'id' field
                team_ids = [
                    item.get("id") if isinstance(item, dict) else item
                    for item in teams_list
                ]
                teams = Teams.objects.filter(id__in=team_ids, org=request.profile.org)
                task_obj.teams.add(*teams)

            if params.get("assigned_to"):
                assinged_to_list = params.get("assigned_to")
                if isinstance(assinged_to_list, str):
                    assinged_to_list = json.loads(assinged_to_list)
                # Extract IDs if assinged_to_list contains objects with 'id' field
                assigned_ids = [
                    item.get("id") if isinstance(item, dict) else item
                    for item in assinged_to_list
                ]
                profiles = Profile.objects.filter(
                    id__in=assigned_ids, org=request.profile.org, is_active=True
                )
                task_obj.assigned_to.add(*profiles)

            if params.get("tags"):
                tags = params.get("tags")
                if isinstance(tags, str):
                    tags = json.loads(tags)
                # Extract IDs if tags contains objects with 'id' field
                tag_ids = [
                    item.get("id") if isinstance(item, dict) else item
                    for item in tags
                ]
                tag_objs = Tags.objects.filter(
                    id__in=tag_ids, org=request.profile.org, is_active=True
                )
                task_obj.tags.add(*tag_objs)

            # Handle new FK relationships with org validation
            if params.get("opportunity"):
                from opportunity.models import Opportunity

                opp = Opportunity.objects.filter(
                    id=params.get("opportunity"), org=request.profile.org
                ).first()
                if opp:
                    task_obj.opportunity = opp
                    task_obj.save()

            if params.get("case"):
                from cases.models import Case

                case = Case.objects.filter(
                    id=params.get("case"), org=request.profile.org
                ).first()
                if case:
                    task_obj.case = case
                    task_obj.save()

            if params.get("lead"):
                from leads.models import Lead

                lead = Lead.objects.filter(
                    id=params.get("lead"), org=request.profile.org
                ).first()
                if lead:
                    task_obj.lead = lead
                    task_obj.save()

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
    permission_classes = (IsAuthenticated, HasOrgContext)

    def get_object(self, pk):
        return Task.objects.get(pk=pk, org=self.request.profile.org)

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
            object_id=self.task_obj.id,
            org=self.request.profile.org,
        ).order_by("-id")
        attachments = Attachments.objects.filter(
            content_type=task_content_type,
            object_id=self.task_obj.id,
            org=self.request.profile.org,
        ).order_by("-id")

        assigned_data = self.task_obj.assigned_to.values("id", "user__email")

        if self.request.profile.is_admin or self.request.profile.role == "ADMIN":
            users_mention = list(
                Profile.objects.filter(
                    is_active=True, org=self.request.profile.org
                ).values("user__email")
            )
        elif self.request.profile != self.task_obj.created_by:
            users_mention = [{"username": self.task_obj.created_by.user.email}]
        else:
            users_mention = list(self.task_obj.assigned_to.all().values("user__email"))
        if self.request.profile.role == "ADMIN" or self.request.profile.is_admin:
            users = Profile.objects.filter(
                is_active=True, org=self.request.profile.org
            ).order_by("user__email")
        else:
            users = Profile.objects.filter(
                role="ADMIN", org=self.request.profile.org
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
        context["teams"] = TeamsSerializer(
            Teams.objects.filter(org=self.request.profile.org), many=True
        ).data
        return context

    @extend_schema(
        tags=["Tasks"],
        operation_id="tasks_retrieve",
        parameters=swagger_params.organization_params,
        responses={
            200: inline_serializer(
                name="TaskDetailResponse",
                fields={
                    "task_obj": TaskSerializer(),
                    "attachments": AttachmentsSerializer(many=True),
                    "comments": CommentSerializer(many=True),
                    "users_mention": serializers.ListField(),
                    "assigned_data": serializers.DictField(),
                    "users": ProfileSerializer(many=True),
                    "users_excluding_team": ProfileSerializer(many=True),
                    "teams": TeamsSerializer(many=True),
                },
            )
        },
    )
    def get(self, request, pk, **kwargs):
        self.task_obj = self.get_object(pk)
        context = self.get_context_data(**kwargs)
        return Response(context)

    @extend_schema(
        tags=["Tasks"],
        operation_id="tasks_comment_attachment",
        parameters=swagger_params.organization_params,
        request=TaskDetailEditSwaggerSerializer,
        responses={
            200: inline_serializer(
                name="TaskCommentAttachmentResponse",
                fields={
                    "task_obj": TaskSerializer(),
                    "attachments": AttachmentsSerializer(many=True),
                    "comments": CommentSerializer(many=True),
                },
            )
        },
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
            attachment.content_object = self.task_obj
            attachment.attachment = self.request.FILES.get("task_attachment")
            attachment.org = self.request.profile.org
            attachment.save()

        task_content_type = ContentType.objects.get_for_model(Task)
        comments = Comment.objects.filter(
            content_type=task_content_type,
            object_id=self.task_obj.id,
            org=self.request.profile.org,
        ).order_by("-id")
        attachments = Attachments.objects.filter(
            content_type=task_content_type,
            object_id=self.task_obj.id,
            org=self.request.profile.org,
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
        tags=["Tasks"],
        operation_id="tasks_update",
        parameters=swagger_params.organization_params,
        request=TaskCreateSwaggerSerializer,
        responses={
            200: inline_serializer(
                name="TaskUpdateResponse",
                fields={
                    "error": serializers.BooleanField(),
                    "message": serializers.CharField(),
                },
            )
        },
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
                if isinstance(contacts_list, str):
                    contacts_list = json.loads(contacts_list)
                # Extract IDs if contacts_list contains objects with 'id' field
                contact_ids = [
                    item.get("id") if isinstance(item, dict) else item
                    for item in contacts_list
                ]
                contacts = Contact.objects.filter(
                    id__in=contact_ids, org=request.profile.org
                )
                task_obj.contacts.add(*contacts)

            task_obj.teams.clear()
            if params.get("teams"):
                teams_list = params.get("teams")
                if isinstance(teams_list, str):
                    teams_list = json.loads(teams_list)
                # Extract IDs if teams_list contains objects with 'id' field
                team_ids = [
                    item.get("id") if isinstance(item, dict) else item
                    for item in teams_list
                ]
                teams = Teams.objects.filter(id__in=team_ids, org=request.profile.org)
                task_obj.teams.add(*teams)

            task_obj.assigned_to.clear()
            if params.get("assigned_to"):
                assinged_to_list = params.get("assigned_to")
                if isinstance(assinged_to_list, str):
                    assinged_to_list = json.loads(assinged_to_list)
                # Extract IDs if assinged_to_list contains objects with 'id' field
                assigned_ids = [
                    item.get("id") if isinstance(item, dict) else item
                    for item in assinged_to_list
                ]
                profiles = Profile.objects.filter(
                    id__in=assigned_ids, org=request.profile.org, is_active=True
                )
                task_obj.assigned_to.add(*profiles)

            task_obj.tags.clear()
            if params.get("tags"):
                tags = params.get("tags")
                if isinstance(tags, str):
                    tags = json.loads(tags)
                # Extract IDs if tags contains objects with 'id' field
                tag_ids = [
                    item.get("id") if isinstance(item, dict) else item
                    for item in tags
                ]
                tag_objs = Tags.objects.filter(
                    id__in=tag_ids, org=request.profile.org, is_active=True
                )
                task_obj.tags.add(*tag_objs)

            # Handle FK relationships with org validation
            if params.get("opportunity"):
                from opportunity.models import Opportunity

                opp = Opportunity.objects.filter(
                    id=params.get("opportunity"), org=request.profile.org
                ).first()
                task_obj.opportunity = opp
            elif "opportunity" in params:
                task_obj.opportunity = None

            if params.get("case"):
                from cases.models import Case

                case = Case.objects.filter(
                    id=params.get("case"), org=request.profile.org
                ).first()
                task_obj.case = case
            elif "case" in params:
                task_obj.case = None

            if params.get("lead"):
                from leads.models import Lead

                lead = Lead.objects.filter(
                    id=params.get("lead"), org=request.profile.org
                ).first()
                task_obj.lead = lead
            elif "lead" in params:
                task_obj.lead = None

            task_obj.save()

            return Response(
                {"error": False, "message": "Task updated Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @extend_schema(
        tags=["Tasks"],
        parameters=swagger_params.organization_params,
        request=TaskCreateSwaggerSerializer,
        description="Partial Task Update",
        responses={
            200: inline_serializer(
                name="TaskPatchResponse",
                fields={
                    "error": serializers.BooleanField(),
                    "message": serializers.CharField(),
                },
            )
        },
    )
    def patch(self, request, pk, **kwargs):
        """Handle partial updates to a task."""
        params = request.data
        self.task_obj = self.get_object(pk)
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

        serializer = TaskCreateSerializer(
            data=params,
            instance=self.task_obj,
            request_obj=request,
            partial=True,
        )
        if serializer.is_valid():
            task_obj = serializer.save()

            # Handle M2M fields if present in request
            if "contacts" in params:
                task_obj.contacts.clear()
                contacts_list = params.get("contacts")
                if contacts_list:
                    if isinstance(contacts_list, str):
                        contacts_list = json.loads(contacts_list)
                    # Extract IDs if contacts_list contains objects with 'id' field
                    contact_ids = [
                        item.get("id") if isinstance(item, dict) else item
                        for item in contacts_list
                    ]
                    contacts = Contact.objects.filter(
                        id__in=contact_ids, org=request.profile.org
                    )
                    task_obj.contacts.add(*contacts)

            if "teams" in params:
                task_obj.teams.clear()
                teams_list = params.get("teams")
                if teams_list:
                    if isinstance(teams_list, str):
                        teams_list = json.loads(teams_list)
                    # Extract IDs if teams_list contains objects with 'id' field
                    team_ids = [
                        item.get("id") if isinstance(item, dict) else item
                        for item in teams_list
                    ]
                    teams = Teams.objects.filter(
                        id__in=team_ids, org=request.profile.org
                    )
                    task_obj.teams.add(*teams)

            if "assigned_to" in params:
                task_obj.assigned_to.clear()
                assigned_to_list = params.get("assigned_to")
                if assigned_to_list:
                    if isinstance(assigned_to_list, str):
                        assigned_to_list = json.loads(assigned_to_list)
                    # Extract IDs if assigned_to_list contains objects with 'id' field
                    assigned_ids = [
                        item.get("id") if isinstance(item, dict) else item
                        for item in assigned_to_list
                    ]
                    profiles = Profile.objects.filter(
                        id__in=assigned_ids, org=request.profile.org, is_active=True
                    )
                    task_obj.assigned_to.add(*profiles)

            if "tags" in params:
                task_obj.tags.clear()
                tags_list = params.get("tags")
                if tags_list:
                    if isinstance(tags_list, str):
                        tags_list = json.loads(tags_list)
                    # Extract IDs if tags_list contains objects with 'id' field
                    tag_ids = [
                        tag.get("id") if isinstance(tag, dict) else tag
                        for tag in tags_list
                    ]
                    tag_objs = Tags.objects.filter(
                        id__in=tag_ids, org=request.profile.org, is_active=True
                    )
                    task_obj.tags.add(*tag_objs)

            # Handle FK relationships with org validation
            if "opportunity" in params:
                if params.get("opportunity"):
                    from opportunity.models import Opportunity

                    opp = Opportunity.objects.filter(
                        id=params.get("opportunity"), org=request.profile.org
                    ).first()
                    task_obj.opportunity = opp
                else:
                    task_obj.opportunity = None

            if "case" in params:
                if params.get("case"):
                    from cases.models import Case

                    case = Case.objects.filter(
                        id=params.get("case"), org=request.profile.org
                    ).first()
                    task_obj.case = case
                else:
                    task_obj.case = None

            if "lead" in params:
                if params.get("lead"):
                    from leads.models import Lead

                    lead = Lead.objects.filter(
                        id=params.get("lead"), org=request.profile.org
                    ).first()
                    task_obj.lead = lead
                else:
                    task_obj.lead = None

            task_obj.save()

            return Response(
                {"error": False, "message": "Task updated Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @extend_schema(
        tags=["Tasks"],
        operation_id="tasks_destroy",
        parameters=swagger_params.organization_params,
        responses={
            200: inline_serializer(
                name="TaskDeleteResponse",
                fields={
                    "error": serializers.BooleanField(),
                    "message": serializers.CharField(),
                },
            )
        },
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
    permission_classes = (IsAuthenticated, HasOrgContext)

    def get_object(self, pk):
        return self.model.objects.get(pk=pk, org=self.request.profile.org)

    @extend_schema(
        tags=["Tasks"],
        parameters=swagger_params.organization_params,
        request=TaskCommentEditSwaggerSerializer,
        responses={
            200: inline_serializer(
                name="TaskCommentUpdateResponse",
                fields={
                    "error": serializers.BooleanField(),
                    "message": serializers.CharField(),
                },
            )
        },
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
        tags=["Tasks"],
        parameters=swagger_params.organization_params,
        request=TaskCommentEditSwaggerSerializer,
        description="Partial Comment Update",
        responses={
            200: inline_serializer(
                name="TaskCommentPatchResponse",
                fields={
                    "error": serializers.BooleanField(),
                    "message": serializers.CharField(),
                },
            )
        },
    )
    def patch(self, request, pk, format=None):
        """Handle partial updates to a comment."""
        params = request.data
        obj = self.get_object(pk)
        if (
            request.profile.role == "ADMIN"
            or request.profile.is_admin
            or request.profile == obj.commented_by
        ):
            serializer = CommentSerializer(obj, data=params, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"error": False, "message": "Comment Updated"},
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
        tags=["Tasks"],
        parameters=swagger_params.organization_params,
        responses={
            200: inline_serializer(
                name="TaskCommentDeleteResponse",
                fields={
                    "error": serializers.BooleanField(),
                    "message": serializers.CharField(),
                },
            )
        },
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
    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(
        tags=["Tasks"],
        parameters=swagger_params.organization_params,
        responses={
            200: inline_serializer(
                name="TaskAttachmentDeleteResponse",
                fields={
                    "error": serializers.BooleanField(),
                    "message": serializers.CharField(),
                },
            )
        },
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
