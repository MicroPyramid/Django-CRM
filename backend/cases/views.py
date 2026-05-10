import json

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from drf_spectacular.utils import (
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
from cases.models import Case, ReopenPolicy, Solution
from cases.models import EmailMessage as _EmailMessageModel  # noqa: F401  (used below)
from cases.serializer import EmailMessageSerializer
from cases.serializer import (
    CaseCommentEditSwaggerSerializer,
    CaseCreateSerializer,
    CaseCreateSwaggerSerializer,
    CaseDetailEditSwaggerSerializer,
    CaseSerializer,
    ReopenPolicySerializer,
)
from cases.solution_serializers import SolutionSerializer
from cases.tasks import send_email_to_assigned_user
from common.custom_fields import validate_payload as validate_custom_fields_payload
from common.models import (
    Activity,
    Attachments,
    Comment,
    CustomFieldDefinition,
    Profile,
    Tags,
    Teams,
)
from common.serializer import (
    ActivitySerializer,
    AttachmentsSerializer,
    CommentSerializer,
    CustomFieldDefinitionSerializer,
)
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
        # COORDINATION_DECISIONS.md D4: hide soft-deleted cases by default; admins may opt in.
        include_deleted = (
            params.get("include_deleted") == "true"
            and (
                self.request.profile.role == "ADMIN"
                or self.request.profile.is_admin
            )
        )
        if not include_deleted:
            queryset = queryset.filter(is_active=True)
        # Hide merged duplicates by default. Agents can opt in with
        # `?show_merged=true` to audit prior merges.
        if params.get("show_merged") != "true":
            queryset = queryset.filter(merged_into__isnull=True).exclude(
                status="Duplicate"
            )
        accounts = Account.objects.filter(org=self.request.profile.org).order_by("-id")
        contacts = Contact.objects.filter(org=self.request.profile.org).order_by("-id")
        profiles = Profile.objects.filter(is_active=True, org=self.request.profile.org)
        if self.request.profile.role != "ADMIN" and not self.request.profile.is_admin:
            # Watcher allowance: a non-admin who is a watcher must still be
            # able to see the case even when un-assigned. See
            # docs/cases/tier2/watchers-mentions.md "Watcher who loses access".
            queryset = queryset.filter(
                Q(created_by=self.request.profile.user)
                | Q(assigned_to=self.request.profile)
                | Q(watchers=self.request.profile)
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
            # Custom-field filters: ?cf_<key>=<value> -> custom_fields contains pair.
            for raw_key, raw_value in params.items():
                if raw_key.startswith("cf_") and raw_value:
                    cf_key = raw_key[3:]
                    if cf_key:
                        queryset = queryset.filter(
                            custom_fields__contains={cf_key: raw_value}
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
            cf_payload = params.get("custom_fields")
            if isinstance(cf_payload, str):
                try:
                    cf_payload = json.loads(cf_payload)
                except (TypeError, ValueError):
                    cf_payload = None
            cleaned_cf, cf_errors = validate_custom_fields_payload(
                "Case", cf_payload or {}, request.profile.org
            )
            if cf_errors:
                return Response(
                    {"error": True, "errors": {"custom_fields": cf_errors}},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            cases_obj = serializer.save(
                created_by=request.profile.user,
                org=request.profile.org,
                closed_on=params.get("closed_on"),
                case_type=params.get("case_type"),
                custom_fields=cleaned_cf,
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
            cf_payload = params.get("custom_fields")
            if isinstance(cf_payload, str):
                try:
                    cf_payload = json.loads(cf_payload)
                except (TypeError, ValueError):
                    cf_payload = None
            cleaned_cf, cf_errors = validate_custom_fields_payload(
                "Case",
                cf_payload or {},
                request.profile.org,
                existing=cases_object.custom_fields or {},
            )
            if cf_errors:
                return Response(
                    {"error": True, "errors": {"custom_fields": cf_errors}},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            cases_object = serializer.save(
                closed_on=params.get("closed_on"),
                case_type=params.get("case_type"),
                custom_fields=cleaned_cf,
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
        # Merged duplicate → tell the client to redirect. JSON form (200) keeps
        # the SvelteKit route's error handling simple. The query param
        # `?show_merged=true` lets agents view the duplicate directly via
        # bookmark / list-view escape hatch.
        if (
            self.cases.merged_into_id
            and request.query_params.get("show_merged") != "true"
        ):
            return Response(
                {
                    "redirect_to": str(self.cases.merged_into_id),
                    "merged_into": str(self.cases.merged_into_id),
                    "source_case_id": str(self.cases.id),
                    "source_case_name": self.cases.name,
                },
                status=status.HTTP_200_OK,
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
        comments_qs = Comment.objects.filter(
            content_type=case_content_type,
            object_id=self.cases.id,
            org=self.request.profile.org,
        ).order_by("-id")
        public_comments = comments_qs.filter(is_internal=False)
        internal_notes = comments_qs.filter(is_internal=True)

        linked_solutions = self.cases.solutions.filter(
            org=self.request.profile.org
        )

        recent_activities = Activity.objects.filter(
            entity_type="Case",
            entity_id=self.cases.id,
            org=self.request.profile.org,
        ).select_related("user__user")[:20]

        custom_field_defs = CustomFieldDefinition.objects.filter(
            org=self.request.profile.org,
            target_model="Case",
            is_active=True,
        ).order_by("display_order", "label")

        # Inbound emails associated with this case (most recent first), so the
        # discussion tab can render them with an "Email" badge.
        email_messages = _EmailMessageModel.objects.filter(
            case=self.cases, drop_reason=""
        ).order_by("-received_at")[:50]

        merged_from = list(
            self.cases.merged_from_cases.filter(org=self.request.profile.org)
            .order_by("-merged_at")
            .values("id", "name", "merged_at")
        )

        context.update(
            {
                "attachments": AttachmentsSerializer(attachments, many=True).data,
                "comments": CommentSerializer(public_comments, many=True).data,
                "internal_notes": CommentSerializer(internal_notes, many=True).data,
                "contacts": ContactSerializer(
                    self.cases.contacts.all(), many=True
                ).data,
                "solutions": SolutionSerializer(linked_solutions, many=True).data,
                "activities": ActivitySerializer(recent_activities, many=True).data,
                "email_messages": EmailMessageSerializer(
                    email_messages, many=True
                ).data,
                "merged_from_cases": merged_from,
                "custom_field_definitions": CustomFieldDefinitionSerializer(
                    custom_field_defs, many=True
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
        comment_text = params.get("comment")
        if comment_text:
            is_internal_raw = params.get("is_internal", False)
            if isinstance(is_internal_raw, str):
                is_internal = is_internal_raw.lower() in ("true", "1", "yes")
            else:
                is_internal = bool(is_internal_raw)
            Comment.objects.create(
                comment=comment_text,
                content_type=ContentType.objects.get_for_model(Case),
                object_id=self.cases_obj.id,
                commented_by=self.request.profile,
                is_internal=is_internal,
                org=self.request.profile.org,
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
        comments_qs = Comment.objects.filter(
            content_type=case_content_type,
            object_id=self.cases_obj.id,
            org=request.profile.org,
        ).order_by("-id")

        context.update(
            {
                "cases_obj": CaseSerializer(self.cases_obj).data,
                "attachments": AttachmentsSerializer(attachments, many=True).data,
                "comments": CommentSerializer(
                    comments_qs.filter(is_internal=False), many=True
                ).data,
                "internal_notes": CommentSerializer(
                    comments_qs.filter(is_internal=True), many=True
                ).data,
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
            save_kwargs = {
                "closed_on": params.get("closed_on")
                if "closed_on" in params
                else cases_object.closed_on,
                "case_type": params.get("case_type")
                if "case_type" in params
                else cases_object.case_type,
            }
            if "custom_fields" in params:
                cf_payload = params.get("custom_fields")
                if isinstance(cf_payload, str):
                    try:
                        cf_payload = json.loads(cf_payload)
                    except (TypeError, ValueError):
                        cf_payload = None
                cleaned_cf, cf_errors = validate_custom_fields_payload(
                    "Case",
                    cf_payload or {},
                    request.profile.org,
                    existing=cases_object.custom_fields or {},
                )
                if cf_errors:
                    return Response(
                        {"error": True, "errors": {"custom_fields": cf_errors}},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                save_kwargs["custom_fields"] = cleaned_cf
            cases_object = serializer.save(**save_kwargs)

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


class CaseSolutionLinkView(APIView):
    """Link or unlink Solutions (Knowledge Base articles) to a Case."""

    permission_classes = (IsAuthenticated, HasOrgContext)

    def _get_case(self, pk, org):
        return Case.objects.filter(pk=pk, org=org).first()

    def _get_solution(self, pk, org):
        return Solution.objects.filter(pk=pk, org=org).first()

    @extend_schema(
        tags=["Cases"],
        request=inline_serializer(
            name="CaseSolutionLinkRequest",
            fields={"solution_id": serializers.CharField()},
        ),
    )
    def post(self, request, pk):
        case = self._get_case(pk, request.profile.org)
        if not case:
            return Response(
                {"error": True, "errors": "Case not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        solution_id = request.data.get("solution_id")
        if not solution_id:
            return Response(
                {"error": True, "errors": "solution_id required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sol = self._get_solution(solution_id, request.profile.org)
        if not sol:
            return Response(
                {"error": True, "errors": "Solution not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        already_linked = case.solutions.filter(pk=sol.pk).exists()
        if not already_linked:
            case.solutions.add(sol)
        return Response(
            {"error": False, "solution": SolutionSerializer(sol).data},
            status=(
                status.HTTP_200_OK if already_linked else status.HTTP_201_CREATED
            ),
        )

    @extend_schema(tags=["Cases"])
    def delete(self, request, pk, solution_pk):
        case = self._get_case(pk, request.profile.org)
        if not case:
            return Response(
                {"error": True, "errors": "Case not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        sol = self._get_solution(solution_pk, request.profile.org)
        if not sol:
            return Response(
                {"error": True, "errors": "Solution not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        case.solutions.remove(sol)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CaseActivityListView(APIView, LimitOffsetPagination):
    """Paginated audit-log feed for a single Case (newest-first)."""

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(
        tags=["Cases"],
        parameters=swagger_params.organization_params,
        responses={
            200: inline_serializer(
                name="CaseActivityListResponse",
                fields={
                    "activities": ActivitySerializer(many=True),
                    "count": serializers.IntegerField(),
                    "offset": serializers.IntegerField(allow_null=True),
                },
            )
        },
    )
    def get(self, request, pk):
        case = Case.objects.filter(pk=pk, org=request.profile.org).first()
        if not case:
            return Response(
                {"error": True, "errors": "Case not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        if request.profile.role != "ADMIN" and not request.profile.is_admin:
            if not (
                request.profile.user == case.created_by
                or request.profile in case.assigned_to.all()
            ):
                return Response(
                    {
                        "error": True,
                        "errors": "You don't have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        queryset = Activity.objects.filter(
            entity_type="Case",
            entity_id=case.id,
            org=request.profile.org,
        ).select_related("user__user")

        page = self.paginate_queryset(queryset, request, view=self)
        data = ActivitySerializer(page, many=True).data
        if page:
            offset = queryset.filter(id__gte=page[-1].id).count()
            if offset == queryset.count():
                offset = None
        else:
            offset = 0
        return Response(
            {"activities": data, "count": self.count, "offset": offset}
        )


class ReopenPolicyView(APIView):
    """Per-org reopen policy. Admin-only. Auto-creates the singleton on first read."""

    permission_classes = (IsAuthenticated, HasOrgContext)

    def _is_admin(self, request):
        return request.profile.role == "ADMIN" or request.profile.is_admin

    def _get_or_create_policy(self, org):
        policy = ReopenPolicy.objects.filter(org=org).first()
        if policy is None:
            policy = ReopenPolicy.objects.create(org=org)
        return policy

    @extend_schema(
        tags=["Cases"],
        parameters=swagger_params.organization_params,
        responses={200: ReopenPolicySerializer},
    )
    def get(self, request, format=None):
        if not self._is_admin(request):
            return Response(
                {"error": True, "errors": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN,
            )
        policy = self._get_or_create_policy(request.profile.org)
        return Response(ReopenPolicySerializer(policy).data)

    @extend_schema(
        tags=["Cases"],
        parameters=swagger_params.organization_params,
        request=ReopenPolicySerializer,
        responses={200: ReopenPolicySerializer},
    )
    def put(self, request, format=None):
        if not self._is_admin(request):
            return Response(
                {"error": True, "errors": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN,
            )
        policy = self._get_or_create_policy(request.profile.org)
        serializer = ReopenPolicySerializer(policy, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(
                {"error": True, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save()
        return Response(serializer.data)
