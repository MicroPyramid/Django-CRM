from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.models import Attachments, Comment, Profile, Tags, Teams, User
from common.permissions import HasOrgContext
from common.serializer import (
    AttachmentsSerializer,
    CommentSerializer,
    LeadCommentSerializer,
    ProfileSerializer,
    TeamsSerializer,
)
from common.utils import COUNTRIES, INDCHOICES, LEAD_SOURCE, LEAD_STATUS
from contacts.models import Contact
from leads import swagger_params
from leads.models import Lead
from leads.serializer import (
    LeadCreateSerializer,
    LeadCreateSwaggerSerializer,
    LeadDetailEditSwaggerSerializer,
    LeadSerializer,
    TagsSerializer,
)
from leads.tasks import send_email_to_assigned_user


class LeadListView(APIView, LimitOffsetPagination):
    model = Lead
    permission_classes = (IsAuthenticated, HasOrgContext)

    def get_context_data(self, **kwargs):
        params = self.request.query_params
        queryset = (
            self.model.objects.filter(org=self.request.profile.org)
            .exclude(status="converted")
            .select_related("created_by")
            .prefetch_related(
                "tags",
                "assigned_to",
            )
        ).order_by("-id")
        if self.request.profile.role != "ADMIN" and not self.request.user.is_superuser:
            queryset = queryset.filter(
                Q(assigned_to__in=[self.request.profile])
                | Q(created_by=self.request.profile.user)
            )

        if params:
            if params.get("name"):
                queryset = queryset.filter(
                    Q(first_name__icontains=params.get("name"))
                    & Q(last_name__icontains=params.get("name"))
                )
            if params.get("salutation"):
                queryset = queryset.filter(
                    salutation__icontains=params.get("salutation")
                )
            if params.get("source"):
                queryset = queryset.filter(source=params.get("source"))
            if params.getlist("assigned_to"):
                queryset = queryset.filter(
                    assigned_to__id__in=params.get("assigned_to")
                )
            if params.get("status"):
                queryset = queryset.filter(status=params.get("status"))
            if params.get("tags"):
                queryset = queryset.filter(tags__in=params.get("tags"))
            if params.get("city"):
                queryset = queryset.filter(city__icontains=params.get("city"))
            if params.get("email"):
                queryset = queryset.filter(email__icontains=params.get("email"))
            if params.get("rating"):
                queryset = queryset.filter(rating=params.get("rating"))
            if params.get("search"):
                search = params.get("search")
                queryset = queryset.filter(
                    Q(first_name__icontains=search)
                    | Q(last_name__icontains=search)
                    | Q(company_name__icontains=search)
                    | Q(email__icontains=search)
                )
            if params.get("created_at__gte"):
                queryset = queryset.filter(
                    created_at__gte=params.get("created_at__gte")
                )
            if params.get("created_at__lte"):
                queryset = queryset.filter(
                    created_at__lte=params.get("created_at__lte")
                )
            if params.get("close_date__gte"):
                queryset = queryset.filter(
                    close_date__gte=params.get("close_date__gte")
                )
            if params.get("close_date__lte"):
                queryset = queryset.filter(
                    close_date__lte=params.get("close_date__lte")
                )
        context = {}
        queryset_open = queryset.exclude(status="closed")
        results_leads_open = self.paginate_queryset(
            queryset_open.distinct(), self.request, view=self
        )
        open_leads = LeadSerializer(results_leads_open, many=True).data
        if results_leads_open:
            offset = queryset_open.filter(id__gte=results_leads_open[-1].id).count()
            if offset == queryset_open.count():
                offset = None
        else:
            offset = 0
        context["per_page"] = 10
        page_number = (int(self.offset / 10) + 1,)
        context["page_number"] = page_number
        context["open_leads"] = {
            "leads_count": self.count,
            "open_leads": open_leads,
            "offset": offset,
        }

        queryset_close = queryset.filter(status="closed")
        results_leads_close = self.paginate_queryset(
            queryset_close.distinct(), self.request, view=self
        )
        close_leads = LeadSerializer(results_leads_close, many=True).data
        if results_leads_close:
            offset = queryset_close.filter(id__gte=results_leads_close[-1].id).count()
            if offset == queryset_close.count():
                offset = None
        else:
            offset = 0

        context["close_leads"] = {
            "leads_count": self.count,
            "close_leads": close_leads,
            "offset": offset,
        }
        contacts = Contact.objects.filter(org=self.request.profile.org).values(
            "id", "first_name"
        )

        context["contacts"] = contacts
        context["status"] = LEAD_STATUS
        context["source"] = LEAD_SOURCE
        context["tags"] = TagsSerializer(
            Tags.objects.filter(org=self.request.profile.org, is_active=True), many=True
        ).data

        users = Profile.objects.filter(
            is_active=True, org=self.request.profile.org
        ).values("id", "user__email")
        context["users"] = users
        context["countries"] = COUNTRIES
        context["industries"] = INDCHOICES
        return context

    @extend_schema(
        tags=["Leads"],
        operation_id="leads_list",
        parameters=swagger_params.lead_list_get_params,
        responses={
            200: inline_serializer(
                name="LeadListResponse",
                fields={
                    "per_page": serializers.IntegerField(),
                    "page_number": serializers.IntegerField(),
                    "open_leads": serializers.DictField(),
                    "close_leads": serializers.DictField(),
                    "contacts": serializers.ListField(),
                    "status": serializers.ListField(),
                    "source": serializers.ListField(),
                    "tags": TagsSerializer(many=True),
                    "users": serializers.ListField(),
                    "countries": serializers.ListField(),
                    "industries": serializers.ListField(),
                },
            )
        },
    )
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return Response(context)

    @extend_schema(
        tags=["Leads"],
        operation_id="leads_create",
        description="Leads Create",
        parameters=swagger_params.organization_params,
        request=LeadCreateSwaggerSerializer,
        responses={
            200: inline_serializer(
                name="LeadCreateResponse",
                fields={
                    "error": serializers.BooleanField(),
                    "message": serializers.CharField(),
                    "account_id": serializers.CharField(required=False),
                    "contact_id": serializers.CharField(
                        required=False, allow_null=True
                    ),
                    "opportunity_id": serializers.CharField(
                        required=False, allow_null=True
                    ),
                },
            )
        },
    )
    def post(self, request, *args, **kwargs):
        data = request.data
        serializer = LeadCreateSerializer(data=data, request_obj=request)
        if serializer.is_valid():
            lead_obj = serializer.save(
                created_by=request.profile.user, org=request.profile.org
            )
            if data.get("tags", None):
                tags = data.get("tags")
                tag_objs = Tags.objects.filter(
                    id__in=tags, org=request.profile.org, is_active=True
                )
                lead_obj.tags.add(*tag_objs)

            if data.get("contacts", None):
                obj_contact = Contact.objects.filter(
                    id__in=data.get("contacts"), org=request.profile.org
                )
                lead_obj.contacts.add(*obj_contact)

            recipients = list(lead_obj.assigned_to.all().values_list("id", flat=True))
            send_email_to_assigned_user.delay(
                recipients,
                lead_obj.id,
                str(request.profile.org.id),
            )

            if request.FILES.get("lead_attachment"):
                attachment = Attachments()
                attachment.created_by = request.profile.user
                attachment.file_name = request.FILES.get("lead_attachment").name
                attachment.content_object = lead_obj
                attachment.attachment = request.FILES.get("lead_attachment")
                attachment.org = request.profile.org
                attachment.save()

            if data.get("teams", None):
                teams_list = data.get("teams")
                if isinstance(teams_list, str):
                    teams_list = json.loads(teams_list)
                # Extract IDs if teams_list contains objects with 'id' field
                team_ids = [
                    item.get("id") if isinstance(item, dict) else item
                    for item in teams_list
                ]
                teams = Teams.objects.filter(id__in=team_ids, org=request.profile.org)
                lead_obj.teams.add(*teams)

            if data.get("assigned_to", None):
                assinged_to_list = data.get("assigned_to")
                if isinstance(assinged_to_list, str):
                    assinged_to_list = json.loads(assinged_to_list)
                # Extract IDs if assinged_to_list contains objects with 'id' field
                assigned_ids = [
                    item.get("id") if isinstance(item, dict) else item
                    for item in assinged_to_list
                ]
                profiles = Profile.objects.filter(
                    id__in=assigned_ids, org=request.profile.org
                )
                lead_obj.assigned_to.add(*profiles)

            if data.get("status") == "converted":
                from leads.services import convert_lead_to_account

                account, contact, opportunity = convert_lead_to_account(
                    lead_obj, request
                )

                if data.get("assigned_to", None):
                    assigned_to_list = data.getlist("assigned_to")
                    send_email_to_assigned_user.delay(
                        assigned_to_list,
                        lead_obj.id,
                        str(request.profile.org.id),
                    )
                return Response(
                    {
                        "error": False,
                        "message": "Lead Converted Successfully",
                        "account_id": str(account.id),
                        "contact_id": str(contact.id) if contact else None,
                        "opportunity_id": str(opportunity.id) if opportunity else None,
                    },
                    status=status.HTTP_200_OK,
                )
            return Response(
                {"error": False, "message": "Lead Created Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class LeadDetailView(APIView):
    model = Lead
    permission_classes = (IsAuthenticated, HasOrgContext)

    def get_object(self, pk):
        return get_object_or_404(Lead, id=pk, org=self.request.profile.org)

    def get_context_data(self, **kwargs):
        params = self.request.query_params
        context = {}
        user_assgn_list = [
            assigned_to.id for assigned_to in self.lead_obj.assigned_to.all()
        ]
        if self.request.profile.user == self.lead_obj.created_by:
            user_assgn_list.append(self.request.profile.user)
        if self.request.profile.role != "ADMIN" and not self.request.user.is_superuser:
            if self.request.profile.id not in user_assgn_list:
                return Response(
                    {
                        "error": True,
                        "errors": "You do not have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        lead_content_type = ContentType.objects.get_for_model(Lead)
        comments = Comment.objects.filter(
            content_type=lead_content_type, object_id=self.lead_obj.id
        ).order_by("-id")
        attachments = Attachments.objects.filter(
            content_type=lead_content_type, object_id=self.lead_obj.id
        ).order_by("-id")
        assigned_data = []
        for each in self.lead_obj.assigned_to.all():
            assigned_dict = {}
            assigned_dict["id"] = each.id
            assigned_dict["name"] = each.user.email
            assigned_data.append(assigned_dict)

        if self.request.user.is_superuser or self.request.profile.role == "ADMIN":
            users_mention = list(
                Profile.objects.filter(
                    is_active=True, org=self.request.profile.org
                ).values("user__email")
            )
        elif self.request.profile.user != self.lead_obj.created_by:
            users_mention = [{"username": self.lead_obj.created_by.username}]
        else:
            users_mention = list(self.lead_obj.assigned_to.all().values("user__email"))
        lead_content_type = ContentType.objects.get_for_model(Lead)
        comments = Comment.objects.filter(
            content_type=lead_content_type,
            object_id=self.lead_obj.id,
            org=self.request.profile.org,
        ).order_by("-id")
        attachments = Attachments.objects.filter(
            content_type=lead_content_type,
            object_id=self.lead_obj.id,
            org=self.request.profile.org,
        ).order_by("-id")
        if self.request.profile.role == "ADMIN" or self.request.user.is_superuser:
            users = Profile.objects.filter(
                is_active=True, org=self.request.profile.org
            ).order_by("user__email")
        else:
            users = Profile.objects.filter(
                role="ADMIN", org=self.request.profile.org
            ).order_by("user__email")
        user_assgn_list = [
            assigned_to.id
            for assigned_to in self.lead_obj.get_assigned_users_not_in_teams
        ]

        if self.request.profile.user == self.lead_obj.created_by:
            user_assgn_list.append(self.request.profile.id)
        if self.request.profile.role != "ADMIN" and not self.request.user.is_superuser:
            if self.request.profile.id not in user_assgn_list:
                return Response(
                    {
                        "error": True,
                        "errors": "You do not have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
        team_ids = [user.id for user in self.lead_obj.get_team_users]
        all_user_ids = [user.id for user in users]
        users_excluding_team_id = set(all_user_ids) - set(team_ids)
        users_excluding_team = Profile.objects.filter(id__in=users_excluding_team_id)
        context.update(
            {
                "lead_obj": LeadSerializer(self.lead_obj).data,
                "attachments": AttachmentsSerializer(attachments, many=True).data,
                "comments": LeadCommentSerializer(comments, many=True).data,
                "users_mention": users_mention,
                "assigned_data": assigned_data,
            }
        )
        context["users"] = ProfileSerializer(users, many=True).data
        context["users_excluding_team"] = ProfileSerializer(
            users_excluding_team, many=True
        ).data
        context["source"] = LEAD_SOURCE
        context["status"] = LEAD_STATUS
        context["teams"] = TeamsSerializer(
            Teams.objects.filter(org=self.request.profile.org), many=True
        ).data
        context["countries"] = COUNTRIES

        return context

    @extend_schema(
        tags=["Leads"],
        operation_id="leads_retrieve",
        parameters=swagger_params.organization_params,
        description="Lead Detail",
        responses={
            200: inline_serializer(
                name="LeadDetailResponse",
                fields={
                    "lead_obj": LeadSerializer(),
                    "attachments": AttachmentsSerializer(many=True),
                    "comments": LeadCommentSerializer(many=True),
                    "users_mention": serializers.ListField(),
                    "assigned_data": serializers.ListField(),
                    "users": ProfileSerializer(many=True),
                    "users_excluding_team": ProfileSerializer(many=True),
                    "source": serializers.ListField(),
                    "status": serializers.ListField(),
                    "teams": TeamsSerializer(many=True),
                    "countries": serializers.ListField(),
                },
            )
        },
    )
    def get(self, request, pk, **kwargs):
        self.lead_obj = self.get_object(pk)
        context = self.get_context_data(**kwargs)
        return Response(context)

    @extend_schema(
        tags=["Leads"],
        operation_id="leads_comment_attachment",
        parameters=swagger_params.organization_params,
        request=LeadDetailEditSwaggerSerializer,
        responses={
            200: inline_serializer(
                name="LeadCommentAttachmentResponse",
                fields={
                    "lead_obj": LeadSerializer(),
                    "attachments": AttachmentsSerializer(many=True),
                    "comments": LeadCommentSerializer(many=True),
                },
            )
        },
    )
    def post(self, request, pk, **kwargs):
        params = request.data

        context = {}
        self.lead_obj = Lead.objects.get(pk=pk)
        if self.lead_obj.org != request.profile.org:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if self.request.profile.role != "ADMIN" and not self.request.user.is_superuser:
            if not (
                (self.request.profile.user == self.lead_obj.created_by)
                or (self.request.profile in self.lead_obj.assigned_to.all())
            ):
                return Response(
                    {
                        "error": True,
                        "errors": "You do not have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
        if params.get("comment"):
            lead_content_type = ContentType.objects.get_for_model(Lead)
            Comment.objects.create(
                content_type=lead_content_type,
                object_id=self.lead_obj.id,
                comment=params.get("comment"),
                commented_by=self.request.profile,
                org=self.request.profile.org,
            )

            if self.request.FILES.get("lead_attachment"):
                attachment = Attachments()
                attachment.created_by = User.objects.get(
                    id=self.request.profile.user.id
                )

                attachment.file_name = self.request.FILES.get("lead_attachment").name
                attachment.content_object = self.lead_obj
                attachment.attachment = self.request.FILES.get("lead_attachment")
                attachment.org = self.request.profile.org
                attachment.save()

        lead_content_type = ContentType.objects.get_for_model(Lead)
        comments = Comment.objects.filter(
            content_type=lead_content_type,
            object_id=self.lead_obj.id,
            org=self.request.profile.org,
        ).order_by("-id")
        attachments = Attachments.objects.filter(
            content_type=lead_content_type,
            object_id=self.lead_obj.id,
            org=self.request.profile.org,
        ).order_by("-id")
        context.update(
            {
                "lead_obj": LeadSerializer(self.lead_obj).data,
                "attachments": AttachmentsSerializer(attachments, many=True).data,
                "comments": LeadCommentSerializer(comments, many=True).data,
            }
        )
        return Response(context)

    @extend_schema(
        tags=["Leads"],
        parameters=swagger_params.organization_params,
        request=LeadCreateSwaggerSerializer,
        responses={
            200: inline_serializer(
                name="LeadUpdateResponse",
                fields={
                    "error": serializers.BooleanField(),
                    "message": serializers.CharField(),
                    "account_id": serializers.CharField(required=False),
                    "contact_id": serializers.CharField(
                        required=False, allow_null=True
                    ),
                    "opportunity_id": serializers.CharField(
                        required=False, allow_null=True
                    ),
                },
            )
        },
    )
    def put(self, request, pk, **kwargs):
        params = request.data
        self.lead_obj = self.get_object(pk)
        if self.lead_obj.org != request.profile.org:
            return Response(
                {
                    "error": True,
                    "errors": "User company does not match with header....",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = LeadCreateSerializer(
            data=params,
            instance=self.lead_obj,
            request_obj=request,
        )
        if serializer.is_valid():
            lead_obj = serializer.save()
            previous_assigned_to_users = list(
                lead_obj.assigned_to.all().values_list("id", flat=True)
            )
            lead_obj.tags.clear()
            if params.get("tags"):
                tags = params.get("tags")
                tag_objs = Tags.objects.filter(
                    id__in=tags, org=request.profile.org, is_active=True
                )
                lead_obj.tags.add(*tag_objs)

            assigned_to_list = list(
                lead_obj.assigned_to.all().values_list("id", flat=True)
            )
            recipients = list(set(assigned_to_list) - set(previous_assigned_to_users))
            send_email_to_assigned_user.delay(
                recipients,
                lead_obj.id,
                str(request.profile.org.id),
            )
            if request.FILES.get("lead_attachment"):
                attachment = Attachments()
                attachment.created_by = request.profile.user
                attachment.file_name = request.FILES.get("lead_attachment").name
                attachment.content_object = lead_obj
                attachment.attachment = request.FILES.get("lead_attachment")
                attachment.org = request.profile.org
                attachment.save()

            lead_obj.contacts.clear()
            if params.get("contacts"):
                contacts_list = params.get("contacts")
                if isinstance(contacts_list, str):
                    contacts_list = json.loads(contacts_list)
                # Extract IDs if contacts_list contains objects with 'id' field
                contact_ids = [
                    item.get("id") if isinstance(item, dict) else item
                    for item in contacts_list
                ]
                obj_contact = Contact.objects.filter(
                    id__in=contact_ids, org=request.profile.org
                )
                lead_obj.contacts.add(*obj_contact)

            lead_obj.teams.clear()
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
                lead_obj.teams.add(*teams)

            lead_obj.assigned_to.clear()
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
                    id__in=assigned_ids, org=request.profile.org
                )
                lead_obj.assigned_to.add(*profiles)

            if params.get("status") == "converted":
                from leads.services import convert_lead_to_account

                account, contact, opportunity = convert_lead_to_account(
                    lead_obj, request
                )

                if params.get("assigned_to"):
                    assigned_to_list = params.get("assigned_to")
                    send_email_to_assigned_user.delay(
                        assigned_to_list,
                        lead_obj.id,
                        str(request.profile.org.id),
                    )

                return Response(
                    {
                        "error": False,
                        "message": "Lead Converted Successfully",
                        "account_id": str(account.id),
                        "contact_id": str(contact.id) if contact else None,
                        "opportunity_id": str(opportunity.id) if opportunity else None,
                    },
                    status=status.HTTP_200_OK,
                )
            return Response(
                {"error": False, "message": "Lead updated Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @extend_schema(
        tags=["Leads"],
        parameters=swagger_params.organization_params,
        request=LeadDetailEditSwaggerSerializer,
        description="Partial Lead Update",
        responses={
            200: inline_serializer(
                name="LeadPatchResponse",
                fields={
                    "error": serializers.BooleanField(),
                    "message": serializers.CharField(),
                    "account_id": serializers.CharField(required=False),
                    "contact_id": serializers.CharField(
                        required=False, allow_null=True
                    ),
                    "opportunity_id": serializers.CharField(
                        required=False, allow_null=True
                    ),
                },
            )
        },
    )
    def patch(self, request, pk, **kwargs):
        """Handle partial updates to a lead, including conversion."""
        params = request.data
        self.lead_obj = self.get_object(pk)

        if self.lead_obj.org != request.profile.org:
            return Response(
                {
                    "error": True,
                    "errors": "User company does not match with header....",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if self.request.profile.role != "ADMIN" and not self.request.user.is_superuser:
            if not (
                (self.request.profile.user == self.lead_obj.created_by)
                or (self.request.profile in self.lead_obj.assigned_to.all())
            ):
                return Response(
                    {
                        "error": True,
                        "errors": "You do not have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        # Handle conversion if status is being set to converted
        if params.get("status") == "converted" or params.get("is_converted"):
            from leads.services import convert_lead_to_account

            account, contact, opportunity = convert_lead_to_account(
                self.lead_obj, request
            )

            return Response(
                {
                    "error": False,
                    "message": "Lead Converted Successfully",
                    "account_id": str(account.id),
                    "contact_id": str(contact.id) if contact else None,
                    "opportunity_id": str(opportunity.id) if opportunity else None,
                },
                status=status.HTTP_200_OK,
            )

        # Handle regular partial updates
        serializer = LeadCreateSerializer(
            data=params,
            instance=self.lead_obj,
            request_obj=request,
            partial=True,
        )
        if serializer.is_valid():
            lead_obj = serializer.save()

            # Handle M2M fields if present in request
            if "tags" in params:
                lead_obj.tags.clear()
                tags = params.get("tags")
                if tags:
                    if isinstance(tags, str):
                        tags = json.loads(tags)
                    # Extract IDs if tags contains objects with 'id' field
                    tag_ids = [
                        tag.get("id") if isinstance(tag, dict) else tag
                        for tag in tags
                    ]
                    tag_objs = Tags.objects.filter(
                        id__in=tag_ids, org=request.profile.org, is_active=True
                    )
                    lead_obj.tags.add(*tag_objs)

            if "contacts" in params:
                lead_obj.contacts.clear()
                contacts_list = params.get("contacts")
                if contacts_list:
                    if isinstance(contacts_list, str):
                        contacts_list = json.loads(contacts_list)
                    # Extract IDs if contacts_list contains objects with 'id' field
                    contact_ids = [
                        item.get("id") if isinstance(item, dict) else item
                        for item in contacts_list
                    ]
                    obj_contact = Contact.objects.filter(
                        id__in=contact_ids, org=request.profile.org
                    )
                    lead_obj.contacts.add(*obj_contact)

            if "teams" in params:
                lead_obj.teams.clear()
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
                    lead_obj.teams.add(*teams)

            if "assigned_to" in params:
                lead_obj.assigned_to.clear()
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
                        id__in=assigned_ids, org=request.profile.org
                    )
                    lead_obj.assigned_to.add(*profiles)

            return Response(
                {"error": False, "message": "Lead updated Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @extend_schema(
        tags=["Leads"],
        parameters=swagger_params.organization_params,
        description="Lead Delete",
        responses={
            200: inline_serializer(
                name="LeadDeleteResponse",
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
            or request.user.is_superuser
            or request.profile.user == self.object.created_by
        ) and self.object.org == request.profile.org:
            self.object.delete()
            return Response(
                {"error": False, "message": "Lead deleted Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": "you don't have permission to delete this lead"},
            status=status.HTTP_403_FORBIDDEN,
        )
