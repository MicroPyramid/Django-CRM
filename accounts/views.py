import json

from django.db.models import Q
from django.shortcuts import get_object_or_404

from drf_rw_serializers import generics

from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView

from accounts import swagger_params1
from accounts.models import Account, Tags
from accounts.serializer import (
    AccountCreateSerializer,
    AccountSerializer,
    EmailSerializer,
    TagsSerailizer,
    AccountReadSerializer,
    AccountWriteSerializer,
    AccountDetailEditSwaggerSerializer,
    AccountCommentEditSwaggerSerializer,
    EmailWriteSerializer
)
from teams.serializer import TeamsSerializer
from accounts.tasks import send_email, send_email_to_assigned_user
from cases.serializer import CaseSerializer
from common.models import Attachments, Comment, Profile
from leads.models import Lead
from leads.serializer import LeadSerializer

#from common.external_auth import CustomDualAuthentication
from common.serializer import (
    AttachmentsSerializer,
    CommentSerializer,
    ProfileSerializer,
)
from common.utils import (
    CASE_TYPE,
    COUNTRIES,
    CURRENCY_CODES,
    INDCHOICES,
    PRIORITY_CHOICE,
    STATUS_CHOICE,
)
from contacts.models import Contact
from contacts.serializer import ContactSerializer
from invoices.serializer import InvoiceSerailizer
from opportunity.models import SOURCES, STAGES, Opportunity
from opportunity.serializer import OpportunitySerializer
from tasks.serializer import TaskSerializer
from teams.models import Teams


class AccountsListView(APIView, LimitOffsetPagination):
    #authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated,)
    model = Account
    serializer_class = AccountReadSerializer

    def get_context_data(self, **kwargs):
        params = self.request.query_params
        queryset = self.model.objects.filter(org=self.request.profile.org).order_by("-id")
        if self.request.profile.role != "ADMIN" and not self.request.profile.is_admin:
            queryset = queryset.filter(
                Q(created_by=self.request.profile.user) | Q(assigned_to=self.request.profile)
            ).distinct()

        if params:
            if params.get("name"):
                queryset = queryset.filter(name__icontains=params.get("name"))
            if params.get("city"):
                queryset = queryset.filter(billing_city__contains=params.get("city"))
            if params.get("industry"):
                queryset = queryset.filter(industry__icontains=params.get("industry"))
            if params.get("tags"):
                queryset = queryset.filter(
                    tags__in=params.get("tags")
                ).distinct()

        context = {}
        queryset_open = queryset.filter(status="open")
        results_accounts_open = self.paginate_queryset(
            queryset_open.distinct(), self.request, view=self
        )
        if results_accounts_open:
            offset = queryset_open.filter(id__gte=results_accounts_open[-1].id).count()
            if offset == queryset_open.count():
                offset = None
        else:
            offset = 0
        accounts_open = AccountSerializer(results_accounts_open, many=True).data
        context["per_page"] = 10
        page_number = (int(self.offset / 10) + 1,)
        context["page_number"] = page_number
        context["active_accounts"] = {
            "offset": offset,
            "open_accounts": accounts_open,
        }

        queryset_close = queryset.filter(status="close")
        results_accounts_close = self.paginate_queryset(
            queryset_close.distinct(), self.request, view=self
        )
        if results_accounts_close:
            offset = queryset_close.filter(
                id__gte=results_accounts_close[-1].id
            ).count()
            if offset == queryset_close.count():
                offset = None
        else:
            offset = 0
        accounts_close = AccountSerializer(results_accounts_close, many=True).data

        contacts = Contact.objects.filter(org=self.request.profile.org).values(
            "id", "first_name"
        )
        context["contacts"] = contacts
        context["closed_accounts"] = {
            "offset": offset,
            "close_accounts": accounts_close,
        }
        context["teams"] = TeamsSerializer(
            Teams.objects.filter(org=self.request.profile.org), many=True
        ).data
        context["countries"] = COUNTRIES
        context["industries"] = INDCHOICES

        tags = Tags.objects.all()
        tags = TagsSerailizer(tags, many=True).data

        context["tags"] = tags
        users = Profile.objects.filter(is_active=True, org=self.request.profile.org).values(
            "id", "user__email"
        )
        context["users"] = users
        leads = Lead.objects.filter(org=self.request.profile.org).exclude(
            Q(status="converted") | Q(status="closed")
        )
        context["users"] = users
        context["leads"] = LeadSerializer(leads, many=True).data
        context["status"] = ["open","close"]
        return context

    @extend_schema(tags=["Accounts"], parameters=swagger_params1.account_get_params)
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return Response(context)

    @extend_schema(tags=["Accounts"], parameters=swagger_params1.organization_params,request=AccountWriteSerializer)
    def post(self, request, *args, **kwargs):
        data = request.data
        serializer = AccountCreateSerializer(
            data=data, request_obj=request, account=True
        )
        # Save Account
        if serializer.is_valid():
            account_object = serializer.save(
                org=request.profile.org
            )
            if data.get("contacts"):
                contacts_list = json.loads(data.get("contacts"))
                contacts = Contact.objects.filter(id__in=contacts_list, org=request.profile.org)
                if contacts:
                    account_object.contacts.add(*contacts)
            if data.get("tags"):
                tags = json.loads(data.get("tags"))
                for tag in tags:
                    tag_obj = Tags.objects.filter(slug=tag.lower())
                    if tag_obj.exists():
                        tag_obj = tag_obj[0]
                    else:
                        tag_obj = Tags.objects.create(name=tag)
                    account_object.tags.add(tag_obj)
            if data.get("teams"):
                teams_list = json.loads(data.get("teams"))
                teams = Teams.objects.filter(id__in=teams_list, org=request.profile.org)
                if teams:
                    account_object.teams.add(*teams)
                if data.get("assigned_to"):
                    assigned_to_list = json.loads(data.get("assigned_to"))
                    profiles = Profile.objects.filter(
                        id__in=assigned_to_list, org=request.profile.org, is_active=True
                    )
                    if profiles:
                        account_object.assigned_to.add(*profiles)

            if self.request.FILES.get("account_attachment"):
                attachment = Attachments()
                attachment.created_by = request.profile.user
                attachment.file_name = request.FILES.get("account_attachment").name
                attachment.account = account_object
                attachment.attachment = request.FILES.get("account_attachment")
                attachment.save()

            recipients = list(
                account_object.assigned_to.all().values_list("id", flat=True)
            )
            send_email_to_assigned_user.delay(
                recipients,
                account_object.id,
            )
            return Response(
                {"error": False, "message": "Account Created Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class AccountDetailView(APIView):
    #authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = AccountReadSerializer

    def get_object(self, pk):
        return get_object_or_404(Account, id=pk)

    @extend_schema(tags=["Accounts"], parameters=swagger_params1.organization_params,request=AccountWriteSerializer)
    def put(self, request, pk, format=None):
        data = request.data
        account_object = self.get_object(pk=pk)
        if account_object.org != request.profile.org:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = AccountCreateSerializer(
            account_object, data=data, request_obj=request, account=True
        )

        if serializer.is_valid():
            if (
                self.request.profile.role != "ADMIN"
                and not self.request.profile.is_admin
            ):
                if not (
                    (self.request.profile == account_object.created_by)
                    or (self.request.profile in account_object.assigned_to.all())
                ):
                    return Response(
                        {
                            "error": True,
                            "errors": "You do not have Permission to perform this action",
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )
            account_object = serializer.save()
            previous_assigned_to_users = list(
                account_object.assigned_to.all().values_list("id", flat=True)
            )

            account_object.contacts.clear()
            if data.get("contacts"):
                contacts_list = json.loads(data.get("contacts"))
                contacts = Contact.objects.filter(id__in=contacts_list, org=request.profile.org)
                if contacts:
                    account_object.contacts.add(*contacts)

            account_object.tags.clear()
            if data.get("tags"):
                tags = json.loads(data.get("tags"))
                for tag in tags:
                    tag_obj = Tags.objects.filter(slug=tag.lower())
                    if tag_obj.exists():
                        tag_obj = tag_obj[0]
                    else:
                        tag_obj = Tags.objects.create(name=tag)
                    account_object.tags.add(tag_obj)

            account_object.teams.clear()
            if data.get("teams"):
                teams_list = json.loads(data.get("teams"))
                teams = Teams.objects.filter(id__in=teams_list, org=request.profile.org)
                if teams:
                    account_object.teams.add(*teams)

            account_object.assigned_to.clear()
            if data.get("assigned_to"):
                assigned_to_list = json.loads(data.get("assigned_to"))
                profiles = Profile.objects.filter(
                    id__in=assigned_to_list, org=request.profile.org, is_active=True
                )
                if profiles:
                    account_object.assigned_to.add(*profiles)

            if self.request.FILES.get("account_attachment"):
                attachment = Attachments()
                attachment.created_by = self.request.profile.user
                attachment.file_name = self.request.FILES.get("account_attachment").name
                attachment.account = account_object
                attachment.attachment = self.request.FILES.get("account_attachment")
                attachment.save()

            assigned_to_list = list(
                account_object.assigned_to.all().values_list("id", flat=True)
            )
            recipients = list(set(assigned_to_list) - set(previous_assigned_to_users))
            send_email_to_assigned_user.delay(
                recipients,
                account_object.id,
            )
            return Response(
                {"error": False, "message": "Account Updated Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @extend_schema(tags=["Accounts"], parameters=swagger_params1.organization_params)
    def delete(self, request, pk, format=None):
        self.object = self.get_object(pk)
        if self.object.org != request.profile.org:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if self.request.profile.role != "ADMIN" and not self.request.profile.is_admin:
            if self.request.profile != self.object.created_by:
                return Response(
                    {
                        "error": True,
                        "errors": "You do not have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
        self.object.delete()
        return Response(
            {"error": False, "message": "Account Deleted Successfully."},
            status=status.HTTP_200_OK,
        )

    @extend_schema(tags=["Accounts"], parameters=swagger_params1.organization_params)
    def get(self, request, pk, format=None):
        self.account = self.get_object(pk=pk)
        if self.account.org != request.profile.org:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_404_NOT_FOUND,
            )
        context = {}
        context["account_obj"] = AccountSerializer(self.account).data
        if self.request.profile.role != "ADMIN" and not self.request.profile.is_admin:
            if not (
                (self.request.profile == self.account.created_by)
                or (self.request.profile in self.account.assigned_to.all())
            ):
                return Response(
                    {
                        "error": True,
                        "errors": "You do not have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        comment_permission = False
        if (
            self.request.profile == self.account.created_by
            or self.request.profile.is_admin
            or self.request.profile.role == "ADMIN"
        ):
            comment_permission = True

        if self.request.profile.is_admin or self.request.profile.role == "ADMIN":
            users_mention = list(
                Profile.objects.filter(is_active=True, org=self.request.profile.org).values(
                    "user__email"
                )
            )
        elif self.request.profile != self.account.created_by:
            if self.account.created_by:
                users_mention = [{"username": self.account.created_by.user.email}]
            else:
                users_mention = []
        else:
            users_mention = []
        leads = Lead.objects.filter(org=self.request.profile.org).exclude(
            Q(status="converted") | Q(status="closed")
        )
        context.update(
            {
                "attachments": AttachmentsSerializer(
                    self.account.account_attachment.all(), many=True
                ).data,
                "comments": CommentSerializer(
                    self.account.accounts_comments.all(), many=True
                ).data,
                "contacts": ContactSerializer(
                    self.account.contacts.all(), many=True
                ).data,
                "opportunity_list": OpportunitySerializer(
                    Opportunity.objects.filter(account=self.account), many=True
                ).data,
                "users": ProfileSerializer(
                    Profile.objects.filter(
                        is_active=True, org=self.request.profile.org
                    ).order_by("user__email"),
                    many=True,
                ).data,
                "cases": CaseSerializer(
                    self.account.accounts_cases.all(), many=True
                ).data,
               "teams" : TeamsSerializer(
                    Teams.objects.filter(org=self.request.profile.org), many=True
                ).data,
                "stages": STAGES,
                "sources": SOURCES,
                "countries": COUNTRIES,
                "currencies": CURRENCY_CODES,
                "case_types": CASE_TYPE,
                "case_priority": PRIORITY_CHOICE,
                "case_status": STATUS_CHOICE,
                "comment_permission": comment_permission,
                "tasks": TaskSerializer(
                    self.account.accounts_tasks.all(), many=True
                ).data,
                "invoices": InvoiceSerailizer(
                    self.account.accounts_invoices.all(), many=True
                ).data,
                "emails": EmailSerializer(
                    self.account.sent_email.all(), many=True
                ).data,
                "users_mention": users_mention,
               "leads" : LeadSerializer(leads, many=True).data,
               "status" : ["open","close"]
            }
        )
        return Response(context)

    @extend_schema(
        tags=["Accounts"], parameters=swagger_params1.organization_params,request=AccountDetailEditSwaggerSerializer
    )
    def post(self, request, pk, **kwargs):
        data = request.data
        context = {}
        self.account_obj = Account.objects.get(pk=pk)
        if self.account_obj.org != request.profile.org:
            return Response(
                {
                    "error": True,
                    "errors": "User company does not match with header....",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        if self.request.profile.role != "ADMIN" and not self.request.profile.is_admin:
            if not (
                (self.request.profile == self.account_obj.created_by)
                or (self.request.profile in self.account_obj.assigned_to.all())
            ):
                return Response(
                    {
                        "error": True,
                        "errors": "You do not have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
        comment_serializer = CommentSerializer(data=data)
        if comment_serializer.is_valid():
            if data.get("comment"):
                comment_serializer.save(
                    account_id=self.account_obj.id,
                    commented_by=self.request.profile,
                )

        if self.request.FILES.get("account_attachment"):
            attachment = Attachments()
            attachment.created_by = self.request.profile.user
            attachment.file_name = self.request.FILES.get("account_attachment").name
            attachment.account = self.account_obj
            attachment.attachment = self.request.FILES.get("account_attachment")
            attachment.save()

        comments = Comment.objects.filter(account__id=self.account_obj.id).order_by(
            "-id"
        )
        attachments = Attachments.objects.filter(
            account__id=self.account_obj.id
        ).order_by("-id")
        context.update(
            {
                "account_obj": AccountSerializer(self.account_obj).data,
                "attachments": AttachmentsSerializer(attachments, many=True).data,
                "comments": CommentSerializer(comments, many=True).data,
            }
        )
        return Response(context)


class AccountCommentView(APIView):
    model = Comment
    #authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = AccountCommentEditSwaggerSerializer

    def get_object(self, pk):
        return self.model.objects.get(pk=pk)

    @extend_schema(
        tags=["Accounts"], parameters=swagger_params1.organization_params,request=AccountCommentEditSwaggerSerializer
    )
    def put(self, request, pk, format=None):
        data = request.data
        obj = self.get_object(pk)
        if (
            request.profile.role == "ADMIN"
            or request.profile.is_admin
            or request.profile == obj.commented_by
        ):
            serializer = CommentSerializer(obj, data=data)
            if data.get("comment"):
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
                "errors": "You don't have permission to edit this Comment",
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    @extend_schema(tags=["Accounts"], parameters=swagger_params1.organization_params)
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
                "errors": "You don't have permission to perform this action",
            },
            status=status.HTTP_403_FORBIDDEN,
        )


class AccountAttachmentView(APIView):
    model = Attachments
    #authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = AccountDetailEditSwaggerSerializer

    @extend_schema(tags=["Accounts"], parameters=swagger_params1.organization_params)
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
                "errors": "You don't have permission to delete this Attachment",
            },
            status=status.HTTP_403_FORBIDDEN,
        )


class AccountCreateMailView(APIView):
    #authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated,)
    model = Account
    serializer_class = EmailWriteSerializer

    @extend_schema(tags=["Accounts"], parameters=swagger_params1.organization_params,request=EmailWriteSerializer)
    def post(self, request, pk, *args, **kwargs):
        data = request.data
        scheduled_later = data.get("scheduled_later")
        scheduled_date_time = data.get("scheduled_date_time")
        account = Account.objects.filter(id=pk).first()
        serializer = EmailSerializer(
            data=data,
            request_obj=request,  # account=account,
        )

        data = {}
        if serializer.is_valid():
            email_obj = serializer.save(from_account=account)
            if scheduled_later not in ["", None, False, "false"]:
                if scheduled_date_time in ["", None]:
                    return Response(
                        {"error": True, "errors": serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            if data.get("recipients"):
                contacts = json.loads(data.get("recipients"))
                for contact in contacts:
                    obj_contact = Contact.objects.filter(id=contact, org=request.profile.org)
                    if obj_contact.exists():
                        email_obj.recipients.add(contact)
                    else:
                        email_obj.delete()
                        data["recipients"] = "Please enter valid recipient"
                        return Response({"error": True, "errors": data})
            if data.get("scheduled_later") != "true":
                send_email.delay(email_obj.id)
            else:
                email_obj.scheduled_later = True
                email_obj.scheduled_date_time = scheduled_date_time
            return Response(
                {"error": False, "message": "Email sent successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )
