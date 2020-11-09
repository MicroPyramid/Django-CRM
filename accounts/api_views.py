import pytz
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from accounts.forms import (
    AccountForm,
)
from accounts.models import Account, Tags
from accounts.tasks import send_email_to_assigned_user
from accounts import swagger_params
from accounts.serializer import AccountSerializer, TagsSerailizer
from common.models import User, Attachments
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
from emails.serializer import EmailSerailizer
from teams.models import Teams

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema


class AccountsListView(APIView):

    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    model = Account

    def get_queryset(self):
        queryset = self.model.objects.all()
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            queryset = queryset.filter(
                Q(created_by=self.request.user) | Q(
                    assigned_to=self.request.user)
            ).distinct()

        if self.request.GET.get("tag", None):
            queryset = queryset.filter(
                tags__in=self.request.GET.getlist("tag"))

        request_post = self.request.POST
        if request_post:
            if request_post.get("name"):
                queryset = queryset.filter(
                    name__icontains=request_post.get("name"))
            if request_post.get("city"):
                queryset = queryset.filter(
                    billing_city__contains=request_post.get("city")
                )
            if request_post.get("industry"):
                queryset = queryset.filter(
                    industry__icontains=request_post.get("industry")
                )
            if request_post.get("tag"):
                queryset = queryset.filter(
                    tags__in=request_post.getlist("tag"))

        return queryset.filter(company=self.request.company).distinct()

    def get_context_data(self, **kwargs):
        context = {}
        open_accounts = AccountSerializer(
            self.get_queryset().filter(status="open"), many=True).data
        close_accounts = AccountSerializer(
            self.get_queryset().filter(status="close"), many=True).data
        context["accounts_list"] = AccountSerializer(
            self.get_queryset(), many=True).data
        context["users"] = UserSerializer(User.objects.filter(
            is_active=True).order_by("email"), many=True).data
        context["open_accounts"] = open_accounts
        context["close_accounts"] = close_accounts
        context["industries"] = INDCHOICES
        context["per_page"] = self.request.POST.get("per_page")
        tag_ids = list(set(Account.objects.values_list("tags", flat=True)))
        context["tags"] = TagsSerailizer(
            Tags.objects.filter(id__in=tag_ids), many=True).data
        if self.request.POST.get("tag", None):
            context["request_tags"] = self.request.POST.getlist("tag")
        elif self.request.GET.get("tag", None):
            context["request_tags"] = self.request.GET.getlist("tag")
        else:
            context["request_tags"] = None

        search = False
        if (
            self.request.POST.get("name")
            or self.request.POST.get("city")
            or self.request.POST.get("industry")
            or self.request.POST.get("tag")
        ):
            search = True

        context["search"] = search

        tab_status = "Open"
        if self.request.POST.get("tab_status"):
            tab_status = self.request.POST.get("tab_status")
        context["tab_status"] = tab_status
        TIMEZONE_CHOICES = [(tz, tz) for tz in pytz.common_timezones]
        context["timezones"] = TIMEZONE_CHOICES
        context["settings_timezone"] = settings.TIME_ZONE

        return context

    @swagger_auto_schema(tags=["accounts"], manual_parameters=swagger_params.account_list_get_params)
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return Response(context)

    @swagger_auto_schema(tags=["accounts"], manual_parameters=swagger_params.account_list_post_params)
    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return Response(context)


class CreateAccountView(APIView):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    model = Account

    @swagger_auto_schema(tags=["accounts"], manual_parameters=swagger_params.account_create_post_params)
    def post(self, request):
        params = request.query_params if len(
            request.data) == 0 else request.data
        context = {}
        form = AccountForm(
            params, request.FILES, request_obj=request, account=True, request_user=self.request.user
        )
        # Save Account
        if form.is_valid():
            account_object = form.save(commit=False)
            account_object.created_by = self.request.user
            account_object.company = self.request.company
            account_object.save()

            if self.request.POST.get("tags", ""):
                tags = self.request.POST.get("tags")
                splitted_tags = tags.split(",")
                for t in splitted_tags:
                    tag = Tags.objects.filter(name=t)
                    if tag:
                        tag = tag[0]
                    else:
                        tag = Tags.objects.create(name=t)
                    account_object.tags.add(tag)
            if self.request.POST.getlist("contacts", []):
                account_object.contacts.add(
                    *self.request.POST.getlist("contacts"))
            if self.request.POST.getlist("assigned_to", []):
                account_object.assigned_to.add(
                    *self.request.POST.getlist("assigned_to"))
            if self.request.FILES.get("account_attachment"):
                attachment = Attachments()
                attachment.created_by = self.request.user
                attachment.file_name = self.request.FILES.get(
                    "account_attachment").name
                attachment.account = account_object
                attachment.attachment = self.request.FILES.get(
                    "account_attachment")
                attachment.save()
            if self.request.POST.getlist("teams", []):
                user_ids = Teams.objects.filter(
                    id__in=self.request.POST.getlist("teams")
                ).values_list("users", flat=True)
                assinged_to_users_ids = account_object.assigned_to.all().values_list(
                    "id", flat=True
                )
                for user_id in user_ids:
                    if user_id not in assinged_to_users_ids:
                        account_object.assigned_to.add(user_id)
            if self.request.POST.getlist("teams", []):
                account_object.teams.add(*self.request.POST.getlist("teams"))

            assigned_to_list = list(
                account_object.assigned_to.all().values_list("id", flat=True)
            )
            current_site = get_current_site(self.request)
            recipients = assigned_to_list
            send_email_to_assigned_user.delay(
                recipients,
                account_object.id,
                domain=current_site.domain,
                protocol=self.request.scheme,
            )
            return Response({'error': False})
        context["errors"] = form.errors
        return Response(context, status=status.HTTP_400_BAD_REQUEST)

    def get_context_data(self, **kwargs):
        context = {}
        if self.request.user.role == "ADMIN" or self.request.user.is_superuser:
            self.users = User.objects.filter(
                is_active=True, company=self.request.company
            ).order_by("email")
        elif self.request.user.google.all():
            self.users = []
        else:
            self.users = User.objects.filter(
                role="ADMIN", company=self.request.company
            ).order_by("email")
        context["users"] = UserSerializer(self.users, many=True).data
        context["industries"] = INDCHOICES
        context["countries"] = COUNTRIES
        contacts = Contact.objects.filter(company=self.request.company)
        leads = Lead.objects.exclude(
            status__in=["converted", "closed"], company=self.request.company)
        if self.request.user.role == "ADMIN" or self.request.user.is_superuser:
            context["leads"] = LeadSerializer(leads, many=True).data
            context["contacts"] = ContactSerializer(contacts, many=True).data
        else:
            leads = filter(
                Q(assigned_to__in=[self.request.user])
                | Q(created_by=self.request.user))
            context["leads"] = LeadSerializer(leads, many=True).data
        context["lead_count"] = leads.count()
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            context["lead_count"] = (
                Lead.objects.filter(
                    Q(assigned_to__in=[self.request.user])
                    | Q(created_by=self.request.user)
                )
                .filter(company=self.request.company,)
                .exclude(status="closed")
                .count()
            )
            contacts = contacts.filter(
                Q(assigned_to__in=[self.request.user]) | Q(
                    created_by=self.request.user)
            )
            context["contacts"] = ContactSerializer(contacts, many=True).data
        context["contact_count"] = contacts.count()
        context["teams"] = TeamsSerializer(Teams.objects.filter(
            company=self.request.company,), many=True).data
        return context

    @swagger_auto_schema(tags=["accounts"], manual_parameters=swagger_params.account_create_get_params)
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return Response(context)


class AccountUpdateView(APIView):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    model = Account

    def dispatch(self, request, *args, **kwargs):
        self.users = User.objects.filter(is_active=True).order_by("email")
        self.account_obj = Account.objects.filter(id=kwargs.get('pk')).first()
        if self.account_obj.company != request.company:
            raise PermissionDenied
        return super(AccountUpdateView, self).dispatch(request, *args, **kwargs)

    @swagger_auto_schema(tags=["accounts"], manual_parameters=swagger_params.account_update_post_params)
    def post(self, request, *args, **kwargs):
        params = request.query_params if len(
            request.data) == 0 else request.data
        context = {}
        form = AccountForm(params, request.FILES, instance=self.account_obj, request_obj=request, account=True, request_user=self.request.user
                           )
        if form.is_valid():
            account_object = form.save(commit=False)
            account_object.save()
            previous_assigned_to_users = list(
                account_object.assigned_to.all().values_list("id", flat=True)
            )
            account_object.tags.clear()
            if self.request.POST.get("tags", ""):
                tags = self.request.POST.get("tags")
                splitted_tags = tags.split(",")
                for t in splitted_tags:
                    tag = Tags.objects.filter(name=t.lower())
                    if tag:
                        tag = tag[0]
                    else:
                        tag = Tags.objects.create(name=t.lower())
                    account_object.tags.add(tag)
            if self.request.POST.getlist("contacts", []):
                account_object.contacts.clear()
                account_object.contacts.add(
                    *self.request.POST.getlist("contacts"))
            if self.request.POST.getlist("assigned_to", []):
                account_object.assigned_to.clear()
                account_object.assigned_to.add(
                    *self.request.POST.getlist("assigned_to"))
            else:
                account_object.assigned_to.clear()
            if self.request.FILES.get("account_attachment"):
                attachment = Attachments()
                attachment.created_by = self.request.user
                attachment.file_name = self.request.FILES.get(
                    "account_attachment").name
                attachment.account = account_object
                attachment.attachment = self.request.FILES.get(
                    "account_attachment")
                attachment.save()

            if self.request.POST.getlist("teams", []):
                account_object.teams.clear()
                account_object.teams.add(*self.request.POST.getlist("teams"))
            else:
                account_object.teams.clear()
            if self.request.POST.getlist("teams", []):
                user_ids = Teams.objects.filter(
                    id__in=self.request.POST.getlist("teams")
                ).values_list("users", flat=True)
                assinged_to_users_ids = account_object.assigned_to.all().values_list(
                    "id", flat=True
                )
                for user_id in user_ids:
                    if user_id not in assinged_to_users_ids:
                        account_object.assigned_to.add(user_id)

            assigned_to_list = list(
                account_object.assigned_to.all().values_list("id", flat=True)
            )
            current_site = get_current_site(self.request)
            recipients = list(set(assigned_to_list) -
                              set(previous_assigned_to_users))
            send_email_to_assigned_user.delay(
                recipients,
                account_object.id,
                domain=current_site.domain,
                protocol=self.request.scheme,
            )
            return Response({'error': False})
        context['errors'] = form.errors
        return Response(context, status=status.HTTP_400_BAD_REQUEST)

    def get_context_data(self, **kwargs):
        context = {}
        self.users = User.objects.filter(is_active=True).order_by("email")
        context["account_obj"] = AccountSerializer(self.account_obj).data
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            if (self.request.user != context["account_obj"].created_by) and (
                self.request.user not in context[
                    "account_obj"].assigned_to.all()
            ):
                raise PermissionDenied
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            self.users = self.users.filter(
                Q(role="ADMIN") | Q(id__in=[self.request.user.id, ])
            )
        context["users"] = UserSerializer(self.users, many=True).data
        context["industries"] = INDCHOICES
        context["countries"] = COUNTRIES
        context["contact_count"] = Contact.objects.count()
        context["edit_view"] = True
        leads = Lead.objects.exclude(
            status__in=["converted", "closed"])
        if self.request.user.role == "ADMIN":
            context["leads"] = LeadSerializer(leads, many=True).data
        else:
            leads = leads.filter(Q(assigned_to__in=[self.request.user]) | Q(
                created_by=self.request.user))
            context["leads"] = LeadSerializer(leads, many=True).data
        context["lead_count"] = leads.count()
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            context["lead_count"] = (
                Lead.objects.filter(
                    Q(assigned_to__in=[self.request.user])
                    | Q(created_by=self.request.user)
                )
                .exclude(status="closed")
                .count()
            )
        context["teams"] = TeamsSerializer(Teams.objects.all(), many=True).data
        return context

    @swagger_auto_schema(tags=["accounts"], manual_parameters=swagger_params.account_update_get_params)
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return Response(context)


class AccountDeleteView(APIView):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    model = Account

    def get_object(self):
        return Account.objects.filter(id=self.kwargs.get('pk')).first()

    @swagger_auto_schema(tags=["accounts"], manual_parameters=swagger_params.account_delete_params)
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.company != request.company:
            raise PermissionDenied
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            if self.request.user != self.object.created_by:
                raise PermissionDenied
        self.object.delete()
        return Response({'status': 'success'}, status=status.HTTP_204_NO_CONTENT)


class AccountDetailView(APIView):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    model = Account

    def get_object(self):
        return Account.objects.filter(id=self.kwargs.get('pk')).first()

    def dispatch(self, request, *args, **kwargs):
        self.account = self.get_object()
        if self.account.company != request.company:
            raise PermissionDenied
        return super(AccountDetailView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = {}
        context["account_obj"] = AccountSerializer(self.account).data
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            if not (
                (self.request.user == self.account.created_by)
                or (self.request.user in self.account.assigned_to.all())
            ):
                raise PermissionDenied

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
            users_mention = list(
                User.objects.filter(
                    is_active=True, company=self.request.company,
                ).values("username")
            )
        elif self.request.user != self.account.created_by:
            if self.account.created_by:
                users_mention = [{"username": self.account.created_by.username}]
            else:
                users_mention = []
        else:
            users_mention = []

        context.update(
            {
                "comments": CommentSerializer(self.account.accounts_comments.all(), many=True).data,
                "attachments": AttachmentsSerializer(self.account.account_attachment.all(), many=True).data,
                "opportunity_list": OpportunitySerializer(Opportunity.objects.filter(account=self.account), many=True).data,
                "contacts": ContactSerializer(self.account.contacts.all(), many=True).data,
                "users": UserSerializer(User.objects.filter(
                    is_active=True, company=self.request.company,
                ).order_by("email"), many=True).data,
                "cases": CaseSerializer(Case.objects.filter(account=self.account), many=True).data,
                "stages": STAGES,
                "sources": SOURCES,
                "countries": COUNTRIES,
                "currencies": CURRENCY_CODES,
                "case_types": CASE_TYPE,
                "case_priority": PRIORITY_CHOICE,
                "case_status": STATUS_CHOICE,
                "comment_permission": comment_permission,
                "tasks": TaskSerializer(self.account.accounts_tasks.all(), many=True).data,
                "invoices": InvoiceSerailizer(self.account.accounts_invoices.all(), many=True).data,
                "emails": EmailSerailizer(self.account.sent_email.all(), many=True).data,
                "users_mention": users_mention,
            }
        )
        return context


    @swagger_auto_schema(tags=["accounts"], manual_parameters=swagger_params.account_list_get_params)
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return Response(context)
