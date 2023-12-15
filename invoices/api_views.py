import json

import pytz
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Account
from accounts.serializer import AccountSerializer
from common.models import Attachments, Comment, User

#from common.external_auth import CustomDualAuthentication
from common.serializer import (
    AttachmentsSerializer,
    BillingAddressSerializer,
    CommentSerializer,
    UserSerializer,
)
from common.utils import COUNTRIES, CURRENCY_CODES
from invoices import swagger_params1
from invoices.models import Invoice
from invoices.serializer import (
    InvoiceCreateSerializer,
    InvoiceHistorySerializer,
    InvoiceSerailizer,
)
from invoices.tasks import (
    create_invoice_history,
    send_email,
    send_invoice_email,
    send_invoice_email_cancel,
)
from teams.models import Teams
from teams.serializer import TeamsSerializer

INVOICE_STATUS = (
    ("Draft", "Draft"),
    ("Sent", "Sent"),
    ("Paid", "Paid"),
    ("Pending", "Pending"),
    ("Cancelled", "Cancel"),
)


class InvoiceListView(APIView, LimitOffsetPagination):

    #authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated,)
    model = Invoice

    def get_context_data(self, **kwargs):
        params = self.request.query_params
        queryset = self.model.objects.filter(company=self.request.company)
        accounts = Account.objects.filter(company=self.request.company)
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            queryset = queryset.filter(
                Q(created_by=self.request.user) | Q(assigned_to=self.request.user)
            ).distinct()
            accounts = accounts.filter(
                Q(created_by=self.request.user) | Q(assigned_to=self.request.user)
            ).distinct()

        if params:
            if params.get("invoice_title_or_number"):
                queryset = queryset.filter(
                    Q(invoice_title__icontains=params.get("invoice_title_or_number"))
                    | Q(invoice_number__icontains=params.get("invoice_title_or_number"))
                ).distinct()

            if params.get("created_by"):
                queryset = queryset.filter(created_by=params.get("created_by"))
            if params.get("assigned_users"):
                queryset = queryset.filter(
                    assigned_to__in=params.get("assigned_users")
                )
            if params.get("status"):
                queryset = queryset.filter(status=params.get("status"))
            if params.get("total_amount"):
                queryset = queryset.filter(
                    total_amount__icontains=params.get("total_amount")
                )

        context = {}
        search = False
        if (
            params.get("invoice_title_or_number")
            or params.get("created_by")
            or params.get("assigned_users")
            or params.get("status")
            or params.get("total_amount")
        ):
            search = True

        context["search"] = search
        results_invoice = self.paginate_queryset(
            queryset.distinct(), self.request, view=self
        )
        invoices = InvoiceSerailizer(results_invoice, many=True).data
        context["per_page"] = 10
        page_number = (int(self.offset / 10) + 1,)
        context["page_number"] = page_number
        context.update(
            {
                "invoices_count": self.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "page_number": int(self.offset / 10) + 1,
            }
        )
        context["invoices"] = invoices
        context["users"] = UserSerializer(
            User.objects.filter(is_active=True, company=self.request.company).order_by(
                "email"
            ),
            many=True,
        ).data
        context["accounts_list"] = AccountSerializer(accounts, many=True).data
        if self.request.user == "ADMIN":
            context["teams_list"] = TeamsSerializer(
                Teams.objects.filter(company=self.request.company), many=True
            ).data
        context["status"] = INVOICE_STATUS
        context["currency"] = CURRENCY_CODES
        context["countries"] = COUNTRIES

        return context

    @extend_schema(tags=["Invoices"], parameters=swagger_params1.invoice_list_get_params)
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return Response(context)

    @extend_schema(tags=["Invoices"], parameters=swagger_params1.organization_params,request=InvoiceSwaggerSerailizer)
    def post(self, request, *args, **kwargs):
        params = request.data
        data = {}
        serializer = InvoiceCreateSerializer(data=params, request_obj=request)
        from_address_serializer = BillingAddressSerializer(data=params)
        to_address_serializer = BillingAddressSerializer(data=params)
        if not from_address_serializer.is_valid():
            data["from_address_errors"] = from_address_serializer.errors
        if not to_address_serializer.is_valid():
            data["to_address_errors"] = to_address_serializer.errors
        if data:
            return Response({"error": True}, data)

        if serializer.is_valid():
            quality_hours = int(params.get("quality_hours"))
            rate = float(params.get("rate"))
            quantity = quality_hours * rate
            tax = quantity * float(params.get("tax")) / 100
            total_amount = quantity + tax

            from_address_obj = from_address_serializer.save(
                address_line=params.get("from_address_line"),
                street=params.get("from_street"),
                city=params.get("from_city"),
                state=params.get("from_state"),
                postcode=params.get("from_postcode"),
                country=params.get("from_country"),
            )
            to_address_obj = to_address_serializer.save(
                address_line=params.get("to_address_line"),
                street=params.get("to_street"),
                city=params.get("to_city"),
                state=params.get("to_state"),
                postcode=params.get("to_postcode"),
                country=params.get("to_country"),
            )

            invoice_obj = serializer.save(
                created_by=request.user,
                company=request.company,
                quantity=params.get("quality_hours"),
                total_amount=total_amount,
                from_address_id=from_address_obj.id,
                to_address_id=to_address_obj.id,
            )

            if params.get("accounts"):
                accounts = params.get("accounts")
                for account in accounts:
                    obj_account = Account.objects.filter(
                        id=account, company=request.company
                    )
                    if obj_account.exists():
                        invoice_obj.accounts.add(account)
                    else:
                        invoice_obj.delete()
                        data["accounts"] = "Please enter valid account"
                        return Response({"error": True}, data)

            if self.request.user.role == "ADMIN":
                if params.get("teams"):
                    teams = params.get("teams")
                    for team in teams:
                        obj_team = Teams.objects.filter(
                            id=team, company=request.company
                        )
                        if obj_team.exists():
                            invoice_obj.teams.add(team)
                        else:
                            invoice_obj.delete()
                            data["team"] = "Please enter valid Team"
                            return Response({"error": True}, data)
                if params.get("assigned_to"):
                    assinged_to_users_ids = params.get("assigned_to")

                    for user_id in assinged_to_users_ids:
                        user = User.objects.filter(id=user_id, company=request.company)
                        if user.exists():
                            invoice_obj.assigned_to.add(user_id)
                        else:
                            invoice_obj.delete()
                            data["assigned_to"] = "Please enter valid user"
                            return Response({"error": True}, data)
            create_invoice_history(invoice_obj.id, request.user.id, [])
            assigned_to_list = list(
                invoice_obj.assigned_to.all().values_list("id", flat=True)
            )

            recipients = assigned_to_list
            send_email.delay(
                recipients,
                invoice_obj.id,
                domain=settings.DOMAIN_NAME,
                protocol=self.request.scheme,
            )
            return Response({"error": False, "message": "Invoice Created Successfully"})
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class InvoiceDetailView(APIView):
    #authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated,)
    model = Invoice

    def get_object(self, pk):
        return self.model.objects.filter(id=pk).first()

    @swagger_auto_schema(
        tags=["Invoices"], manual_parameters=swagger_params1.invoice_create_post_params
    )
    def put(self, request, pk, format=None):
        params = request.data
        invoice_obj = self.get_object(pk=pk)
        from_address_obj = invoice_obj.from_address
        to_address_obj = invoice_obj.to_address
        data = {}
        if invoice_obj.company != request.company:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            if not (
                (self.request.user == invoice_obj.created_by)
                or (self.request.user in invoice_obj.assigned_to.all())
            ):
                return Response(
                    {
                        "error": True,
                        "errors": "You don't have Permission to perform this action",
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )

        serializer = InvoiceCreateSerializer(
            invoice_obj,
            data=params,
            request_obj=request,
            invoice=True,
        )
        from_address_serializer = BillingAddressSerializer(
            data=params, instance=from_address_obj
        )
        to_address_serializer = BillingAddressSerializer(
            data=params, instance=to_address_obj
        )
        if not from_address_serializer.is_valid():
            data["from_address_errors"] = from_address_serializer.errors
        if not to_address_serializer.is_valid():
            data["to_address_errors"] = to_address_serializer.errors
        if data:
            return Response({"error": True}, data)
        if serializer.is_valid():
            invoice_obj = serializer.save()
            previous_assigned_to_users = list(
                invoice_obj.assigned_to.all().values_list("id", flat=True)
            )
            from_address_obj = from_address_serializer.save(
                address_line=params.get("from_address_line"),
                street=params.get("from_street"),
                city=params.get("from_city"),
                state=params.get("from_state"),
                postcode=params.get("from_postcode"),
                country=params.get("from_country"),
            )
            to_address_obj = to_address_serializer.save(
                address_line=params.get("to_address_line"),
                street=params.get("to_street"),
                city=params.get("to_city"),
                state=params.get("to_state"),
                postcode=params.get("to_postcode"),
                country=params.get("to_country"),
            )
            invoice_obj.from_address = from_address_obj
            invoice_obj.to_address = to_address_obj

            quality_hours = int(params.get("quality_hours"))
            rate = float(params.get("rate"))
            quantity = quality_hours * rate
            tax = quantity * float(params.get("tax")) / 100
            invoice_obj.total_amount = quantity + tax
            invoice_obj.save()

            invoice_obj.accounts.clear()
            if params.get("accounts"):
                accounts = params.get("accounts")
                for account in accounts:
                    obj_account = Account.objects.filter(
                        id=account, company=request.company
                    )
                    if obj_account.exists():
                        invoice_obj.accounts.add(account)
                    else:
                        data["accounts"] = "Please enter valid account"
                        return Response({"error": True}, data)

            if self.request.user.role == "ADMIN":
                invoice_obj.teams.clear()
                if params.get("teams"):
                    teams = params.get("teams")
                    for team in teams:
                        obj_team = Teams.objects.filter(
                            id=team, company=request.company
                        )
                        if obj_team.exists():
                            invoice_obj.teams.add(team)
                        else:
                            data["team"] = "Please enter valid Team"
                            return Response({"error": True}, data)

                invoice_obj.assigned_to.clear()
                if params.get("assigned_to"):
                    assinged_to_users_ids = params.get("assigned_to")
                    for user_id in assinged_to_users_ids:
                        user = User.objects.filter(id=user_id, company=request.company)
                        if user.exists():
                            invoice_obj.assigned_to.add(user_id)
                        else:
                            data["assigned_to"] = "Please enter valid User"
                            return Response({"error": True}, data)

            assigned_to_list = list(
                invoice_obj.assigned_to.all().values_list("id", flat=True)
            )
            recipients = list(set(assigned_to_list) - set(previous_assigned_to_users))
            send_email.delay(
                recipients,
                invoice_obj.id,
                domain=settings.DOMAIN_NAME,
                protocol=self.request.scheme,
            )
            return Response(
                {"error": False, "message": "Invoice Updated Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @swagger_auto_schema(
        tags=["Invoices"], manual_parameters=swagger_params1.invoice_delete_params
    )
    def delete(self, request, pk, format=None):
        self.object = self.get_object(pk)
        if self.object.company != request.company:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."}
            )
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            if self.request.user != self.object.created_by:
                return Response(
                    {
                        "error": True,
                        "errors": "You do not have Permission to perform this action",
                    }
                )
        if self.object.from_address_id:
            self.object.from_address.delete()
        if self.object.to_address_id:
            self.object.to_address.delete()
        self.object.delete()
        return Response(
            {"error": False, "message": "Invoice Deleted Successfully."},
            status=status.HTTP_200_OK,
        )

    @swagger_auto_schema(
        tags=["Invoices"], manual_parameters=swagger_params1.invoice_delete_params
    )
    def get(self, request, pk, format=None):
        self.invoice = self.get_object(pk=pk)
        if self.invoice.company != request.company:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_404_NOT_FOUND,
            )
        context = {}
        context["invoice_obj"] = InvoiceSerailizer(self.invoice).data
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            if not (
                (self.request.user == self.invoice.created_by)
                or (self.request.user in self.invoice.assigned_to.all())
            ):
                return Response(
                    {
                        "error": True,
                        "errors": "You don't have Permission to perform this action",
                    }
                )

        comment_permission = (
            True
            if (
                self.request.user == self.invoice.created_by
                or self.request.user.is_superuser
                or self.request.user.role == "ADMIN"
            )
            else False
        )

        if self.request.user.is_superuser or self.request.user.role == "ADMIN":
            users_mention = list(
                User.objects.filter(
                    is_active=True,
                    company=self.request.company,
                ).values("username")
            )
        elif self.request.user != self.invoice.created_by:
            if self.invoice.created_by:
                users_mention = [{"username": self.invoice.created_by.username}]
            else:
                users_mention = []
        else:
            users_mention = []

        attachments = Attachments.objects.filter(invoice=self.invoice).order_by("-id")
        comments = Comment.objects.filter(invoice=self.invoice).order_by("-id")
        context.update(
            {
                "attachments": AttachmentsSerializer(attachments, many=True).data,
                "comments": CommentSerializer(comments, many=True).data,
                "invoice_history": InvoiceHistorySerializer(
                    self.invoice.invoice_history.all(), many=True
                ).data,
                "accounts": AccountSerializer(
                    self.invoice.accounts.all(), many=True
                ).data,
                "users": UserSerializer(
                    User.objects.filter(
                        is_active=True,
                        company=self.request.company,
                    ).order_by("email"),
                    many=True,
                ).data,
                "comment_permission": comment_permission,
                "users_mention": users_mention,
                "status": INVOICE_STATUS,
                "currency": CURRENCY_CODES,
                "countries": COUNTRIES,
            }
        )
        return Response(context)

    @swagger_auto_schema(
        tags=["Invoices"], manual_parameters=swagger_params1.invoice_detail_post_params
    )
    def post(self, request, pk, **kwargs):
        params = request.data
        context = {}
        self.invoice_obj = Invoice.objects.get(pk=pk)
        if self.invoice_obj.company != request.company:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."}
            )

        comment_serializer = CommentSerializer(data=params)
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            if not (
                (self.request.user == self.invoice_obj.created_by)
                or (self.request.user in self.invoice_obj.assigned_to.all())
            ):
                return Response(
                    {
                        "error": True,
                        "errors": "You don't have Permission to perform this action",
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )
        if comment_serializer.is_valid():
            if params.get("comment"):
                comment_serializer.save(
                    invoice_id=self.invoice_obj.id,
                    commented_by_id=self.request.user.id,
                )

        if self.request.FILES.get("invoice_attachment"):
            attachment = Attachments()
            attachment.created_by = self.request.user
            attachment.file_name = self.request.FILES.get("invoice_attachment").name
            attachment.invoice = self.invoice_obj
            attachment.attachment = self.request.FILES.get("invoice_attachment")
            attachment.save()

        comments = Comment.objects.filter(invoice=self.invoice_obj).order_by("-id")
        attachments = Attachments.objects.filter(invoice=self.invoice_obj).order_by(
            "-id"
        )
        context.update(
            {
                "invoice_obj": InvoiceSerailizer(self.invoice_obj).data,
                "attachments": AttachmentsSerializer(attachments, many=True).data,
                "comments": CommentSerializer(comments, many=True).data,
            }
        )
        return Response(context)


class InvoiceCommentView(APIView):
    model = Comment
    #authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        return self.model.objects.get(pk=pk)

    @swagger_auto_schema(
        tags=["Invoices"], manual_parameters=swagger_params1.invoice_comment_edit_params
    )
    def put(self, request, pk, format=None):
        params = request.data
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
                    "errors": "You don't have permission to perform this action.",
                }
            )

    @swagger_auto_schema(
        tags=["Invoices"], manual_parameters=swagger_params1.invoice_delete_params
    )
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
                }
            )


class InvoiceAttachmentView(APIView):
    model = Attachments
    #authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        tags=["Invoices"], manual_parameters=swagger_params1.invoice_delete_params
    )
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
                    "errors": "You don't have permission to perform this action.",
                }
            )
