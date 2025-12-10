import json

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    extend_schema,
    inline_serializer,
)
from rest_framework import serializers, status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.permissions import HasOrgContext
from rest_framework.views import APIView

from accounts.models import Account
from accounts.serializer import AccountSerializer
from cases import swagger_params
from cases.models import Case
from cases.serializer import (
    CaseCommentEditSwaggerSerializer,
    CaseCreateSerializer,
    CaseCreateSwaggerSerializer,
    CaseDetailEditSwaggerSerializer,
    CaseSerializer,
)
from cases.tasks import send_email_to_assigned_user
from common.models import Attachments, Comment, Profile, Tags, Teams
from common.serializer import AttachmentsSerializer, CommentSerializer
from common.utils import CASE_TYPE, PRIORITY_CHOICE, STATUS_CHOICE
from contacts.models import Contact
from contacts.serializer import ContactSerializer


class CaseListView(APIView, LimitOffsetPagination):
    permission_classes = (IsAuthenticated, HasOrgContext)
    model = Case

    def get_context_data(self, **kwargs):
        params = self.request.query_params
        queryset = self.model.objects.filter(org=self.request.profile.org).order_by(
            "-id"
        )
        accounts = Account.objects.filter(org=self.request.profile.org).order_by("-id")
        contacts = Contact.objects.filter(org=self.request.profile.org).order_by("-id")
        profiles = Profile.objects.filter(is_active=True, org=self.request.profile.org)
        if self.request.profile.role != "ADMIN" and not self.request.profile.is_admin:
            queryset = queryset.filter(
                Q(created_by=self.request.profile.user)
                | Q(assigned_to=self.request.profile)
            ).distinct()
            accounts = accounts.filter(
                Q(created_by=self.request.profile.user)
                | Q(assigned_to=self.request.profile)
            ).distinct()
            contacts = contacts.filter(
                Q(created_by=self.request.profile.user)
                | Q(assigned_to=self.request.profile)
            ).distinct()
            profiles = profiles.filter(role="ADMIN")

        if params:
            if params.get("name"):
                queryset = queryset.filter(name__icontains=params.get("name"))
            if params.get("status"):
                queryset = queryset.filter(status=params.get("status"))
            if params.get("priority"):
                queryset = queryset.filter(priority=params.get("priority"))
            if params.get("account"):
                queryset = queryset.filter(account=params.get("account"))
            if params.get("case_type"):
                queryset = queryset.filter(case_type=params.get("case_type"))
            if params.getlist("assigned_to"):
                queryset = queryset.filter(
                    assigned_to__id__in=params.getlist("assigned_to")
                ).distinct()
            if params.get("tags"):
                queryset = queryset.filter(
                    tags__id__in=params.getlist("tags")
                ).distinct()
            if params.get("search"):
                queryset = queryset.filter(name__icontains=params.get("search"))
            if params.get("created_at__gte"):
                queryset = queryset.filter(
                    created_at__gte=params.get("created_at__gte")
                )
            if params.get("created_at__lte"):
                queryset = queryset.filter(
                    created_at__lte=params.get("created_at__lte")
                )

        context = {}

        results_cases = self.paginate_queryset(queryset, self.request, view=self)
        cases = CaseSerializer(results_cases, many=True).data

        if results_cases:
            offset = queryset.filter(id__gte=results_cases[-1].id).count()
            if offset == queryset.count():
                offset = None
        else:
            offset = 0
        context.update(
            {
                "cases_count": self.count,
                "offset": offset,
            }
        )
        context["cases"] = cases
        context["status"] = STATUS_CHOICE
        context["priority"] = PRIORITY_CHOICE
        context["type_of_case"] = CASE_TYPE
        context["accounts_list"] = AccountSerializer(accounts, many=True).data
        context["contacts_list"] = ContactSerializer(contacts, many=True).data
        return context

    @extend_schema(
        operation_id="cases_list",
        tags=["Cases"],
        parameters=swagger_params.cases_list_get_params,
        responses={
            200: inline_serializer(
                name="CaseListResponse",
                fields={
                    "cases_count": serializers.IntegerField(),
                    "offset": serializers.IntegerField(allow_null=True),
                    "cases": CaseSerializer(many=True),
                    "status": serializers.ListField(),
                    "priority": serializers.ListField(),
                    "type_of_case": serializers.ListField(),
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
        operation_id="cases_create",
        tags=["Cases"],
        parameters=swagger_params.organization_params,
        request=CaseCreateSwaggerSerializer,
        responses={
            200: inline_serializer(
                name="CaseCreateResponse",
                fields={
                    "error": serializers.BooleanField(),
                    "message": serializers.CharField(),
                    "id": serializers.CharField(),
                    "cases_obj": CaseSerializer(),
                },
            )
        },
    )
    def post(self, request, *args, **kwargs):
        params = request.data
        serializer = CaseCreateSerializer(data=params, request_obj=request)
        if serializer.is_valid():
            cases_obj = serializer.save(
                created_by=request.profile.user,
                org=request.profile.org,
                closed_on=params.get("closed_on"),
                case_type=params.get("case_type"),
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
                if contacts:
                    cases_obj.contacts.add(*contacts)

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
                if teams.exists():
                    cases_obj.teams.add(*teams)

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
                if profiles:
                    cases_obj.assigned_to.add(*profiles)

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
                cases_obj.tags.add(*tag_objs)

            if self.request.FILES.get("case_attachment"):
                attachment = Attachments()
                attachment.created_by = self.request.profile.user
                attachment.file_name = self.request.FILES.get("case_attachment").name
                attachment.content_object = cases_obj
                attachment.attachment = self.request.FILES.get("case_attachment")
                attachment.org = self.request.profile.org
                attachment.save()

            recipients = list(cases_obj.assigned_to.all().values_list("id", flat=True))
            send_email_to_assigned_user.delay(
                recipients,
                cases_obj.id,
                str(request.profile.org.id),
            )
            return Response(
                {
                    "error": False,
                    "message": "Case Created Successfully",
                    "id": str(cases_obj.id),
                    "cases_obj": CaseSerializer(cases_obj).data,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class CaseDetailView(APIView):
    permission_classes = (IsAuthenticated, HasOrgContext)
    model = Case

    def get_object(self, pk):
        return self.model.objects.filter(id=pk, org=self.request.profile.org).first()

    @extend_schema(
        operation_id="cases_update",
        tags=["Cases"],
        parameters=swagger_params.organization_params,
        request=CaseCreateSwaggerSerializer,
        responses={
            200: inline_serializer(
                name="CaseUpdateResponse",
                fields={
                    "error": serializers.BooleanField(),
                    "message": serializers.CharField(),
                },
            )
        },
    )
    def put(self, request, pk, format=None):
        params = request.data
        cases_object = self.get_object(pk=pk)
        if cases_object.org != request.profile.org:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if self.request.profile.role != "ADMIN" and not self.request.profile.is_admin:
            if not (
                (self.request.profile.user == cases_object.created_by)
                or (self.request.profile in cases_object.assigned_to.all())
            ):
                return Response(
                    {
                        "error": True,
                        "errors": "You do not have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        serializer = CaseCreateSerializer(
            cases_object,
            data=params,
            request_obj=request,
        )

        if serializer.is_valid():
            cases_object = serializer.save(
                closed_on=params.get("closed_on"), case_type=params.get("case_type")
            )
            previous_assigned_to_users = list(
                cases_object.assigned_to.all().values_list("id", flat=True)
            )
            cases_object.contacts.clear()
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
                if contacts:
                    cases_object.contacts.add(*contacts)

            cases_object.teams.clear()
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
                if teams.exists():
                    cases_object.teams.add(*teams)

            cases_object.assigned_to.clear()
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
                if profiles:
                    cases_object.assigned_to.add(*profiles)

            cases_object.tags.clear()
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
                cases_object.tags.add(*tag_objs)

            if self.request.FILES.get("case_attachment"):
                attachment = Attachments()
                attachment.created_by = self.request.profile.user
                attachment.file_name = self.request.FILES.get("case_attachment").name
                attachment.content_object = cases_object
                attachment.attachment = self.request.FILES.get("case_attachment")
                attachment.org = self.request.profile.org
                attachment.save()

            assigned_to_list = list(
                cases_object.assigned_to.all().values_list("id", flat=True)
            )
            recipients = list(set(assigned_to_list) - set(previous_assigned_to_users))
            send_email_to_assigned_user.delay(
                recipients,
                cases_object.id,
                str(request.profile.org.id),
            )
            return Response(
                {"error": False, "message": "Case Updated Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @extend_schema(
        operation_id="cases_destroy",
        tags=["Cases"],
        parameters=swagger_params.organization_params,
        responses={
            200: inline_serializer(
                name="CaseDeleteResponse",
                fields={
                    "error": serializers.BooleanField(),
                    "message": serializers.CharField(),
                },
            )
        },
    )
    def delete(self, request, pk, format=None):
        self.object = self.get_object(pk)
        if self.object.org != request.profile.org:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if self.request.profile.role != "ADMIN" and not self.request.profile.is_admin:
            if self.request.profile.user != self.object.created_by:
                return Response(
                    {
                        "error": True,
                        "errors": "You do not have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
        self.object.delete()
        return Response(
            {"error": False, "message": "Case Deleted Successfully."},
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        operation_id="cases_retrieve",
        tags=["Cases"],
        parameters=swagger_params.organization_params,
        responses={
            200: inline_serializer(
                name="CaseDetailResponse",
                fields={
                    "cases_obj": CaseSerializer(),
                    "attachments": AttachmentsSerializer(many=True),
                    "comments": CommentSerializer(many=True),
                    "comment_permission": serializers.BooleanField(),
                    "users_mention": serializers.ListField(),
                },
            )
        },
    )
    def get(self, request, pk, format=None):
        self.cases = self.get_object(pk=pk)
        if not self.cases:
            return Response(
                {"error": True, "errors": "Case not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        if self.cases.org != request.profile.org:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN,
            )
        context = {}
        context["cases_obj"] = CaseSerializer(self.cases).data
        if self.request.profile.role != "ADMIN" and not self.request.profile.is_admin:
            if not (
                (self.request.profile.user == self.cases.created_by)
                or (self.request.profile in self.cases.assigned_to.all())
            ):
                return Response(
                    {
                        "error": True,
                        "errors": "You don't have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        comment_permission = False

        if (
            self.request.profile.user == self.cases.created_by
            or self.request.profile.is_admin
            or self.request.profile.role == "ADMIN"
        ):
            comment_permission = True

        if self.request.profile.is_admin or self.request.profile.role == "ADMIN":
            users_mention = list(
                Profile.objects.filter(
                    is_active=True, org=self.request.profile.org
                ).values("user__email")
            )
        elif self.request.profile != self.cases.created_by:
            if self.cases.created_by:
                users_mention = [{"username": self.cases.created_by.user.email}]
            else:
                users_mention = []
        else:
            users_mention = []

        case_content_type = ContentType.objects.get_for_model(Case)
        attachments = Attachments.objects.filter(
            content_type=case_content_type,
            object_id=self.cases.id,
            org=self.request.profile.org,
        ).order_by("-id")
        comments = Comment.objects.filter(
            content_type=case_content_type,
            object_id=self.cases.id,
            org=self.request.profile.org,
        ).order_by("-id")

        context.update(
            {
                "attachments": AttachmentsSerializer(attachments, many=True).data,
                "comments": CommentSerializer(comments, many=True).data,
                "contacts": ContactSerializer(
                    self.cases.contacts.all(), many=True
                ).data,
                "status": STATUS_CHOICE,
                "priority": PRIORITY_CHOICE,
                "type_of_case": CASE_TYPE,
                "comment_permission": comment_permission,
                "users_mention": users_mention,
            }
        )
        return Response(context)

    @extend_schema(
        operation_id="cases_comment_attachment",
        tags=["Cases"],
        parameters=swagger_params.organization_params,
        request=CaseDetailEditSwaggerSerializer,
        responses={
            200: inline_serializer(
                name="CaseCommentAttachmentResponse",
                fields={
                    "cases_obj": CaseSerializer(),
                    "attachments": AttachmentsSerializer(many=True),
                    "comments": CommentSerializer(many=True),
                },
            )
        },
    )
    def post(self, request, pk, **kwargs):
        params = request.data
        self.cases_obj = Case.objects.get(pk=pk, org=request.profile.org)
        if self.cases_obj.org != request.profile.org:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN,
            )
        context = {}
        comment_serializer = CommentSerializer(data=params)
        if self.request.profile.role != "ADMIN" and not self.request.profile.is_admin:
            if not (
                (self.request.profile.user == self.cases_obj.created_by)
                or (self.request.profile in self.cases_obj.assigned_to.all())
            ):
                return Response(
                    {
                        "error": True,
                        "errors": "You don't have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
        if comment_serializer.is_valid():
            if params.get("comment"):
                comment_serializer.save(
                    case_id=self.cases_obj.id,
                    commented_by_id=self.request.profile.id,
                )

        if self.request.FILES.get("case_attachment"):
            attachment = Attachments()
            attachment.created_by = self.request.profile.user
            attachment.file_name = self.request.FILES.get("case_attachment").name
            attachment.content_object = self.cases_obj
            attachment.attachment = self.request.FILES.get("case_attachment")
            attachment.org = self.request.profile.org
            attachment.save()

        case_content_type = ContentType.objects.get_for_model(Case)
        attachments = Attachments.objects.filter(
            content_type=case_content_type,
            object_id=self.cases_obj.id,
            org=request.profile.org,
        ).order_by("-id")
        comments = Comment.objects.filter(
            content_type=case_content_type,
            object_id=self.cases_obj.id,
            org=request.profile.org,
        ).order_by("-id")

        context.update(
            {
                "cases_obj": CaseSerializer(self.cases_obj).data,
                "attachments": AttachmentsSerializer(attachments, many=True).data,
                "comments": CommentSerializer(comments, many=True).data,
            }
        )
        return Response(context)

    @extend_schema(
        tags=["Cases"],
        parameters=swagger_params.organization_params,
        request=CaseCreateSwaggerSerializer,
        description="Partial Case Update",
        responses={
            200: inline_serializer(
                name="CasePatchResponse",
                fields={
                    "error": serializers.BooleanField(),
                    "message": serializers.CharField(),
                },
            )
        },
    )
    def patch(self, request, pk, format=None):
        """Handle partial updates to a case."""
        params = request.data
        cases_object = self.get_object(pk=pk)
        if cases_object.org != request.profile.org:
            return Response(
                {
                    "error": True,
                    "errors": "User company does not match with header....",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        if self.request.profile.role != "ADMIN" and not self.request.profile.is_admin:
            if not (
                (self.request.profile.user == cases_object.created_by)
                or (self.request.profile in cases_object.assigned_to.all())
            ):
                return Response(
                    {
                        "error": True,
                        "errors": "You do not have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        serializer = CaseCreateSerializer(
            cases_object,
            data=params,
            request_obj=request,
            partial=True,
        )

        if serializer.is_valid():
            cases_object = serializer.save(
                closed_on=params.get("closed_on")
                if "closed_on" in params
                else cases_object.closed_on,
                case_type=params.get("case_type")
                if "case_type" in params
                else cases_object.case_type,
            )

            # Handle M2M fields if present in request
            if "contacts" in params:
                cases_object.contacts.clear()
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
                    cases_object.contacts.add(*contacts)

            if "teams" in params:
                cases_object.teams.clear()
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
                    cases_object.teams.add(*teams)

            if "assigned_to" in params:
                cases_object.assigned_to.clear()
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
                    cases_object.assigned_to.add(*profiles)

            if "tags" in params:
                cases_object.tags.clear()
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
                    cases_object.tags.add(*tag_objs)

            return Response(
                {"error": False, "message": "Case Updated Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class CaseCommentView(APIView):
    model = Comment
    permission_classes = (IsAuthenticated, HasOrgContext)

    def get_object(self, pk):
        return self.model.objects.get(pk=pk, org=self.request.profile.org)

    @extend_schema(
        tags=["Cases"],
        parameters=swagger_params.organization_params,
        request=CaseCommentEditSwaggerSerializer,
        responses={
            200: inline_serializer(
                name="CaseCommentUpdateResponse",
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
                "errors": "You don't have permission to perform this action.",
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    @extend_schema(
        tags=["Cases"],
        parameters=swagger_params.organization_params,
        request=CaseCommentEditSwaggerSerializer,
        description="Partial Comment Update",
        responses={
            200: inline_serializer(
                name="CaseCommentPatchResponse",
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
                "errors": "You don't have permission to perform this action.",
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    @extend_schema(
        tags=["Cases"],
        parameters=swagger_params.organization_params,
        responses={
            200: inline_serializer(
                name="CaseCommentDeleteResponse",
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
                "errors": "You do not have permission to perform this action",
            },
            status=status.HTTP_403_FORBIDDEN,
        )


class CaseAttachmentView(APIView):
    model = Attachments
    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(
        tags=["Cases"],
        parameters=swagger_params.organization_params,
        responses={
            200: inline_serializer(
                name="CaseAttachmentDeleteResponse",
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
                "errors": "You don't have permission to perform this action.",
            },
            status=status.HTTP_403_FORBIDDEN,
        )
