import pytz
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.db.models import Q

from accounts.models import Account, Tags, Email
from accounts.tasks import send_email_to_assigned_user, send_email
from accounts import swagger_params
from accounts.serializer import (
    AccountSerializer,
    TagsSerailizer,
    AccountCreateSerializer,
)
from common.models import User, Attachments, Comment
from common.utils import (
    COUNTRIES,
    INDCHOICES,
)
from common.custom_auth import JSONWebTokenAuthentication
from common.serializer import UserSerializer, CommentSerializer, AttachmentsSerializer
from common.utils import (
    CASE_TYPE,
    COUNTRIES,
    CURRENCY_CODES,
    INDCHOICES,
    PRIORITY_CHOICE,
    STATUS_CHOICE,
)
from django.shortcuts import get_object_or_404
from contacts.models import Contact
from leads.models import Lead
from opportunity.models import SOURCES, STAGES, Opportunity
from cases.models import Case
from cases.serializer import CaseSerializer
from contacts.serializer import ContactSerializer
from leads.serializer import LeadSerializer
from teams.serializer import TeamsSerializer
from tasks.serializer import TaskSerializer
from opportunity.serializer import OpportunitySerializer
from invoices.serializer import InvoiceSerailizer
from accounts.serializer import EmailSerializer
from teams.models import Teams

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import LimitOffsetPagination
from drf_yasg.utils import swagger_auto_schema
import json
from crm import settings


class AccountsListView(APIView, LimitOffsetPagination):

    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    model = Account

    def get_context_data(self, **kwargs):
        params = (
            self.request.query_params
            if len(self.request.data) == 0
            else self.request.data
        )
        queryset = self.model.objects.all()
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            queryset = queryset.filter(
                Q(created_by=self.request.user) | Q(assigned_to=self.request.user)
            ).distinct()

        if params:
            request_post = params
            if request_post:
                if request_post.get("name"):
                    queryset = queryset.filter(name__icontains=request_post.get("name"))
                if request_post.get("city"):
                    queryset = queryset.filter(
                        billing_city__contains=request_post.get("city")
                    )
                if request_post.get("industry"):
                    queryset = queryset.filter(
                        industry__icontains=request_post.get("industry")
                    )
                if request_post.get("tags"):
                    queryset = queryset.filter(
                        tags__in=json.loads(request_post.get("tags"))
                    ).distinct()
        context = {}
        search = False
        if (
            params.get("name")
            or params.get("city")
            or params.get("industry")
            or params.get("tag")
        ):
            search = True
        context["search"] = search

        queryset_open = queryset.filter(status="open").order_by("id")
        results_accounts_open = self.paginate_queryset(
            queryset_open.distinct(), self.request, view=self
        )
        accounts_open = AccountSerializer(results_accounts_open, many=True).data
        context["per_page"] = 10
        context["active_accounts"] = {
            "accounts_count": self.count,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "page_number": int(self.offset / 10) + 1,
            "open_accounts": accounts_open,
        }

        queryset_close = queryset.filter(status="close").order_by("id")
        results_accounts_close = self.paginate_queryset(
            queryset_close.distinct(), self.request, view=self
        )
        accounts_close = AccountSerializer(results_accounts_close, many=True).data

        context["closed_accounts"] = {
            "accounts_count": self.count,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "page_number": int(self.offset / 10) + 1,
            "close_accounts": accounts_close,
        }

        context["users"] = UserSerializer(
            User.objects.filter(is_active=True).order_by("email"),
            many=True,
        ).data
        context["industries"] = INDCHOICES
        tag_ids = Account.objects.all().values_list("tags", flat=True).distinct()
        context["tags"] = TagsSerailizer(
            Tags.objects.filter(id__in=tag_ids), many=True
        ).data
        if params.get("tag", None):
            context["request_tags"] = self.params.get("tag")
        else:
            context["request_tags"] = None

        TIMEZONE_CHOICES = [(tz, tz) for tz in pytz.common_timezones]
        context["timezones"] = TIMEZONE_CHOICES
        context["settings_timezone"] = settings.TIME_ZONE
        return context

    @swagger_auto_schema(
        tags=["Accounts"], manual_parameters=swagger_params.account_get_params
    )
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return Response(context)

    @swagger_auto_schema(
        tags=["Accounts"], manual_parameters=swagger_params.account_post_params
    )
    def post(self, request, *args, **kwargs):
        params = request.query_params if len(request.data) == 0 else request.data
        data = {}
        serializer = AccountCreateSerializer(
            data=params, request_obj=request, account=True
        )
        # Save Account
        if serializer.is_valid():
            account_object = serializer.save(created_by=request.user)
            if params.get("contacts"):
                contacts = json.loads(params.get("contacts"))
                for contact in contacts:
                    obj_contact = Contact.objects.filter(id=contact)
                    if obj_contact:
                        account_object.contacts.add(contact)
                    else:
                        account_object.delete()
                        data["contacts"] = "Please enter valid contact"
                        return Response(
                            {"error": True, "errors": data},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
            if params.get("tags"):
                tags = json.loads(params.get("tags"))
                for tag in tags:
                    tag_obj = Tags.objects.filter(slug=tag.lower())
                    if tag_obj:
                        tag_obj = tag_obj[0]
                    else:
                        tag_obj = Tags.objects.create(name=tag)
                    account_object.tags.add(tag_obj)
            if self.request.user.role == "ADMIN":
                if params.get("teams"):
                    teams = json.loads(params.get("teams"))
                    for team in teams:
                        teams_ids = Teams.objects.filter(id=team)
                        if teams_ids:
                            account_object.teams.add(team)
                        else:
                            account_object.delete()
                            data["team"] = "Please enter valid Team"
                            return Response(
                                {"error": True, "errors": data},
                                status=status.HTTP_400_BAD_REQUEST,
                            )
                if params.get("assigned_to"):
                    assinged_to_users_ids = json.loads(params.get("assigned_to"))

                    for user_id in assinged_to_users_ids:
                        user = User.objects.filter(id=user_id)
                        if user:
                            account_object.assigned_to.add(user_id)
                        else:
                            account_object.delete()
                            data["assigned_to"] = "Please enter valid user"
                            return Response(
                                {"error": True, "errors": data},
                                status=status.HTTP_400_BAD_REQUEST,
                            )

            if self.request.FILES.get("account_attachment"):
                attachment = Attachments()
                attachment.created_by = request.user
                attachment.file_name = request.FILES.get("account_attachment").name
                attachment.account = account_object
                attachment.attachment = request.FILES.get("account_attachment")
                attachment.save()

            assigned_to_list = list(
                account_object.assigned_to.all().values_list("id", flat=True)
            )

            recipients = assigned_to_list
            send_email_to_assigned_user.delay(
                recipients,
                account_object.id,
                domain=settings.Domain,
                protocol=self.request.scheme,
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
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        return get_object_or_404(Account, id=pk)

    @swagger_auto_schema(
        tags=["Accounts"], manual_parameters=swagger_params.account_post_params
    )
    def put(self, request, pk, format=None):
        params = request.query_params if len(request.data) == 0 else request.data
        account_object = self.get_object(pk=pk)
        data = {}
        serializer = AccountCreateSerializer(
            account_object, data=params, request_obj=request, account=True
        )

        if serializer.is_valid():
            if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
                if not (
                    (self.request.user == account_object.created_by)
                    or (self.request.user in account_object.assigned_to.all())
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
            if params.get("contacts"):
                contacts = json.loads(params.get("contacts"))
                for contact in contacts:
                    obj_contact = Contact.objects.filter(id=contact)
                    if obj_contact:
                        account_object.contacts.add(contact)
                    else:
                        data["contacts"] = "Please enter valid Contact"
                        return Response(
                            {"error": True, "errors": data},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
            account_object.tags.clear()
            if params.get("tags"):
                tags = json.loads(params.get("tags"))
                for tag in tags:
                    tag_obj = Tags.objects.filter(slug=tag.lower())
                    if tag_obj:
                        tag_obj = tag_obj[0]
                    else:
                        tag_obj = Tags.objects.create(name=tag)
                    account_object.tags.add(tag_obj)

            if self.request.user.role == "ADMIN":
                account_object.teams.clear()
                if params.get("teams"):
                    teams = json.loads(params.get("teams"))
                    for team in teams:
                        teams_ids = Teams.objects.filter(id=team)
                        if teams_ids:
                            account_object.teams.add(team)
                        else:
                            data["team"] = "Please enter valid Team"
                            return Response(
                                {"error": True, "errors": data},
                                status=status.HTTP_400_BAD_REQUEST,
                            )

                account_object.assigned_to.clear()
                if params.get("assigned_to"):
                    assinged_to_users_ids = json.loads(params.get("assigned_to"))
                    for user_id in assinged_to_users_ids:
                        user = User.objects.filter(id=user_id)
                        if user:
                            account_object.assigned_to.add(user_id)
                        else:
                            data["assigned_to"] = "Please enter valid User"
                            return Response(
                                {"error": True, "errors": data},
                                status=status.HTTP_400_BAD_REQUEST,
                            )

            if self.request.FILES.get("account_attachment"):
                attachment = Attachments()
                attachment.created_by = self.request.user
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
                domain=settings.Domain,
                protocol=self.request.scheme,
            )
            return Response(
                {"error": False, "message": "Account Updated Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @swagger_auto_schema(tags=["Accounts"])
    def delete(self, request, pk, format=None):
        self.object = self.get_object(pk)
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            if self.request.user != self.object.created_by:
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

    @swagger_auto_schema(
        tags=["Accounts"],
    )
    def get(self, request, pk, format=None):
        self.account = self.get_object(pk=pk)
        context = {}
        context["account_obj"] = AccountSerializer(self.account).data
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            if not (
                (self.request.user == self.account.created_by)
                or (self.request.user in self.account.assigned_to.all())
            ):
                return Response(
                    {
                        "error": True,
                        "errors": "You do not have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        comment_permission = (
            True
            if (
                self.request.user == self.account.created_by
                or self.request.user.is_superuser
                or self.request.user.role == "ADMIN"
            )
            else False
        )

        if self.request.user.is_superuser or self.request.user.role == "ADMIN":
            users_mention = list(User.objects.filter(is_active=True).values("username"))
        elif self.request.user != self.account.created_by:
            if self.account.created_by:
                users_mention = [{"username": self.account.created_by.username}]
            else:
                users_mention = []
        else:
            users_mention = []
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
                "users": UserSerializer(
                    User.objects.filter(is_active=True).order_by("email"),
                    many=True,
                ).data,
                "cases": CaseSerializer(
                    self.account.accounts_cases.all(), many=True
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
            }
        )
        return Response(context)

    @swagger_auto_schema(
        tags=["Accounts"], manual_parameters=swagger_params.account_detail_get_params
    )
    def post(self, request, pk, **kwargs):
        params = (
            self.request.query_params
            if len(self.request.data) == 0
            else self.request.data
        )
        context = {}
        self.account_obj = Account.objects.get(pk=pk)
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            if not (
                (self.request.user == self.account_obj.created_by)
                or (self.request.user in self.account_obj.assigned_to.all())
            ):
                return Response(
                    {
                        "error": True,
                        "errors": "You do not have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
        comment_serializer = CommentSerializer(data=params)
        if comment_serializer.is_valid():
            if params.get("comment"):
                comment_serializer.save(
                    account_id=self.account_obj.id,
                    commented_by_id=self.request.user.id,
                )

        if self.request.FILES.get("account_attachment"):
            attachment = Attachments()
            attachment.created_by = self.request.user
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
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        return self.model.objects.get(pk=pk)

    @swagger_auto_schema(
        tags=["Accounts"], manual_parameters=swagger_params.account_comment_edit_params
    )
    def put(self, request, pk, format=None):
        params = request.query_params if len(request.data) == 0 else request.data
        obj = self.get_object(pk)
        if (
            request.user.role == "ADMIN"
            or request.user.is_superuser
            or request.user == obj.commented_by
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
                    "errors": "You don't have permission to edit this Comment",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

    @swagger_auto_schema(tags=["Accounts"])
    def delete(self, request, pk, format=None):
        self.object = self.get_object(pk)
        if (
            request.user.role == "ADMIN"
            or request.user.is_superuser
            or request.user == self.object.commented_by
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
                    "errors": "You don't have permission to perform this action",
                },
                status=status.HTTP_403_FORBIDDEN,
            )


class AccountAttachmentView(APIView):
    model = Attachments
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(tags=["Accounts"])
    def delete(self, request, pk, format=None):
        self.object = self.model.objects.get(pk=pk)
        if (
            request.user.role == "ADMIN"
            or request.user.is_superuser
            or request.user == self.object.created_by
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
                    "errors": "You don't have permission to delete this Attachment",
                },
                status=status.HTTP_403_FORBIDDEN,
            )


class AccountCreateMailView(APIView):

    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    model = Account

    @swagger_auto_schema(
        tags=["Accounts"], manual_parameters=swagger_params.account_mail_params
    )
    def post(self, request, pk, *args, **kwargs):
        params = request.query_params if len(request.data) == 0 else request.data
        scheduled_later = params.get("scheduled_later")
        scheduled_date_time = params.get("scheduled_date_time")
        account = Account.objects.filter(id=pk).first()
        serializer = EmailSerializer(
            data=params,
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

            if params.get("recipients"):
                contacts = json.loads(params.get("recipients"))
                for contact in contacts:
                    obj_contact = Contact.objects.filter(id=contact)
                    if obj_contact:
                        email_obj.recipients.add(contact)
                    else:
                        email_obj.delete()
                        data["recipients"] = "Please enter valid recipient"
                        return Response({"error": True, "errors": data})
            if params.get("scheduled_later") != "true":
                send_email.delay(email_obj.id)
            else:
                email_obj.scheduled_later = True
                email_obj.scheduled_date_time = scheduled_date_time
            return Response(
                {"error": False, "message": "Email sent successfully"},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"error": True, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
