from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from django.shortcuts import get_object_or_404
from rest_framework import status
from django.http import Http404
from accounts.serializer import AccountSerializer
from contacts.serializer import ContactSerializer
from opportunity.serializer import OpportunitySerializer
from leads.serializer import LeadSerializer
from teams.serializer import TeamsSerializer
from common.serializer import *
from cases.serializer import CaseSerializer
from accounts.models import Account, Contact
from opportunity.models import Opportunity
from cases.models import Case
from leads.models import Lead
from teams.models import Teams
from common.forms import DocumentForm
from common.utils import ROLES
from common.models import User, Company, Document
from common.access_decorators_mixins import (
    MarketingAccessRequiredMixin,
    SalesAccessRequiredMixin,
    admin_login_required,
    marketing_access_required,
    sales_access_required,
)
from common.tasks import (
    resend_activation_link_to_user,
    send_email_to_new_user,
    send_email_user_delete,
    send_email_user_status,
    send_email_to_reset_password,
)
from django.utils.translation import gettext as _

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_jwt.serializers import jwt_encode_handler
from common.utils import jwt_payload_handler
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated
from common.custom_auth import JSONWebTokenAuthentication
from common import swagger_params
from django.db.models import Q
from rest_framework.decorators import api_view
import json
from marketing.models import BlockedDomain, BlockedEmail, ContactEmailCampaign
from marketing.serializer import (
    ContactEmailCampaignSerailizer,
    BlockedDomainSerailizer,
    BlockedEmailSerailizer,
    BlockedDomainAddSerailizer,
    BlockedEmailAddSerailizer,
)


class GetTeamsAndUsersView(APIView):

    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        tags=["Users"], manual_parameters=swagger_params.dashboard_params
    )
    def get(self, request, *args, **kwargs):
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            return Response(
                {"error": True, "Message": "Permission Denied"},
                status=status.HTTP_403_FORBIDDEN,
            )
        data = {}
        teams = Teams.objects.filter(company=request.company)
        teams_data = TeamsSerializer(teams, many=True).data
        users = User.objects.filter(company=request.company, is_active=True)
        users_data = UserSerializer(users, many=True).data
        data["teams"] = teams_data
        data["users_data"] = users_data
        return Response(data)


class UserDetailView(APIView):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        user = get_object_or_404(User, pk=pk)
        return user

    @swagger_auto_schema(
        tags=["Users"], manual_parameters=swagger_params.dashboard_params
    )
    def get(self, request, pk, format=None):
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            return Response(
                {"error": True, "message": "Permission Denied"},
                status=status.HTTP_403_FORBIDDEN,
            )
        user_obj = self.get_object(pk)
        if user_obj.company != request.company:
            # return Response({'error': 'Id Not found'}, status=status.HTTP_404_NOT_FOUND)
            raise Http404
        users_data = []
        for each in User.objects.filter(company=request.company):
            assigned_dict = {}
            assigned_dict["id"] = each.id
            assigned_dict["name"] = each.username
            users_data.append(assigned_dict)
        context = {}
        context["user_obj"] = UserSerializer(user_obj).data
        opportunity_list = Opportunity.objects.filter(assigned_to=user_obj)
        context["opportunity_list"] = OpportunitySerializer(
            opportunity_list, many=True
        ).data
        contacts = Contact.objects.filter(assigned_to=user_obj)
        context["contacts"] = ContactSerializer(contacts, many=True).data
        cases = Case.objects.filter(assigned_to=user_obj)
        context["cases"] = CaseSerializer(cases, many=True).data
        context["assigned_data"] = users_data
        comments = user_obj.user_comments.all()
        context["comments"] = CommentSerializer(comments, many=True).data
        return Response({"error": False, "data": context}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        tags=["Users"], manual_parameters=swagger_params.user_update_params
    )
    def put(self, request, pk, format=None):
        if request.user.role != "ADMIN" and not request.user.is_superuser:
            return Response(
                {"error": True, "Message": "Permission Denied"},
                status=status.HTTP_403_FORBIDDEN,
            )
            # raise PermissionDenied
        params = request.query_params if len(request.data) == 0 else request.data
        user = self.get_object(pk)
        if user.company != request.company:
            # return Response({'error': 'Id Not found'}, status=status.HTTP_404_NOT_FOUND)
            raise Http404
        serializer = CreateUserSerializer(user, data=params, request_user=request.user)
        if serializer.is_valid():
            user = serializer.save()
            if params.getlist("teams"):
                user_teams = user.user_teams.all()

                team_obj = Teams.objects.filter(company=request.company)
                for team in params.getlist("teams"):
                    try:
                        team_obj = team_obj.filter(id=team).first()
                        if team_obj != user_teams:
                            team_obj.users.add(user)
                    except:
                        return Response(
                            {"detail": "No such Team Available"},
                            status=status.HTTP_404_NOT_FOUND,
                        )
            return Response(
                {"error": False, "message": "User Updated Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @swagger_auto_schema(
        tags=["Users"], manual_parameters=swagger_params.dashboard_params
    )
    def delete(self, request, pk, format=None):
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            return Response(
                {"error": True, "Message": "Permission Denied"},
                status=status.HTTP_403_FORBIDDEN,
            )
            # raise PermissionDenied
        self.object = self.get_object(pk)
        if self.object.company == request.company:
            if self.object.id == request.user.id:
                return Response(
                    {"error": True, "Message": "Permission Denied"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            current_site = request.get_host()
            deleted_by = self.request.user.email
            send_email_user_delete.delay(
                self.object.email,
                deleted_by=deleted_by,
                domain=current_site,
                protocol=request.scheme,
            )
            self.object.delete()
            return Response({"status": "success"}, status=status.HTTP_200_OK)
        return Response(
            {"error": True, "Message": "Id Not Found"}, status=status.HTTP_404_NOT_FOUND
        )


class ChangePasswordView(APIView):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        tags=["Profile"],
        operation_description="This is change password api",
        manual_parameters=swagger_params.change_password_params,
    )
    def post(self, request, format=None):
        params = request.query_params if len(request.data) == 0 else request.data
        old_password = params.get("old_password", None)
        new_password = params.get("new_password", None)
        retype_password = params.get("retype_password", None)
        errors = {}
        if old_password:
            if not request.user.check_password(old_password):
                errors["old_password"] = "old password entered is incorrect."

        if new_password:
            if len(new_password) < 8:
                errors["new_password"] = "Password must be at least 8 characters long!"
            if new_password == old_password:
                errors[
                    "new_password"
                ] = "New password and old password should not be same"
        if retype_password:
            if new_password != retype_password:
                errors[
                    "retype_password"
                ] = "New_password and Retype_password did not match."

        if errors:
            return Response(
                {"error": True, "errors": errors}, status=status.HTTP_400_BAD_REQUEST
            )
        user = request.user
        user.set_password(new_password)
        user.save()
        return Response(
            {"error": False, "message": "Password Changed Successfully"},
            status=status.HTTP_200_OK,
        )


# check_header not working
class ApiHomeView(APIView):

    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        tags=["dashboard"], manual_parameters=swagger_params.dashboard_params
    )
    def get(self, request, format=None):

        accounts = Account.objects.filter(status="open", company=request.company)
        contacts = Contact.objects.filter(company=request.company)
        leads = Lead.objects.filter(company=request.company).exclude(
            Q(status="converted") | Q(status="closed")
        )
        opportunities = Opportunity.objects.filter(company=request.company)

        if self.request.user.role == "ADMIN" or self.request.user.is_superuser:
            pass
        else:
            accounts = accounts.filter(
                Q(assigned_to__id__in=[self.request.user.id])
                | Q(created_by=self.request.user.id)
            )
            contacts = contacts.filter(
                Q(assigned_to__id__in=[self.request.user.id])
                | Q(created_by=self.request.user.id)
            )
            leads = leads.filter(
                Q(assigned_to__id__in=[self.request.user.id])
                | Q(created_by=self.request.user.id)
            ).exclude(status="closed")
            opportunities = opportunities.filter(
                Q(assigned_to__id__in=[self.request.user.id])
                | Q(created_by=self.request.user.id)
            )
        context = {}
        context["accounts_count"] = accounts.count()
        context["contacts_count"] = contacts.count()
        context["leads_count"] = leads.count()
        context["opportunities_count"] = opportunities.count()
        context["accounts"] = AccountSerializer(accounts, many=True).data
        context["contacts"] = ContactSerializer(contacts, many=True).data
        context["leads"] = LeadSerializer(leads, many=True).data
        context["opportunities"] = OpportunitySerializer(opportunities, many=True).data
        return Response(context, status=status.HTTP_200_OK)


class LoginView(APIView):
    @swagger_auto_schema(
        tags=["Auth"],
        operation_description="This is login api",
        manual_parameters=swagger_params.login_page_params,
    )
    def post(self, request, format=None):
        params = request.query_params if len(request.data) == 0 else request.data
        company = request.headers["company"]
        username = params.get("email", None)
        password = params.get("password", None)
        company_obj = Company.objects.filter(sub_domain=company).first()
        if not company_obj:
            company_field = "doesnot exit"
            msg = _("company with this subdomin {company_field}")
            msg = msg.format(company_field=company_field)
            return Response(
                {"error": True, "message": msg}, status=status.HTTP_400_BAD_REQUEST
            )
        if not username:
            username_field = "User Name/Email"
            msg = _('Must include "{username_field}"')
            msg = msg.format(username_field=username_field)
            return Response(
                {"error": True, "message": msg}, status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects.filter(email=username, company=company_obj).first()
        if not user:
            return Response(
                {"error": True, "message": "user not avaliable in our records"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if user.check_password(password):
            payload = jwt_payload_handler(user)
            response_data = {
                "token": jwt_encode_handler(payload),
                "error": False,
                "company": user.company.id,
                "subdomin": company_obj.sub_domain,
            }
            return Response(response_data)
        else:
            password_field = "doesnot match"
            msg = _("Email and password {password_field}")
            msg = msg.format(password_field=password_field)
            return Response(
                {"error": True, "message": msg}, status=status.HTTP_400_BAD_REQUEST
            )


class RegistrationView(APIView):
    @swagger_auto_schema(
        tags=["Auth"],
        operation_description="This is registration api",
        manual_parameters=swagger_params.registration_page_params,
    )
    def post(self, request, format=None):
        params = request.query_params if len(request.data) == 0 else request.data
        sub_domain = params.get("sub_domain", None)
        username = params.get("username", None)
        email = params.get("email", None)
        password = params.get("password", None)
        errors = {}
        if sub_domain:
            if Company.objects.filter(sub_domain__iexact=sub_domain):
                errors["sub_domain"] = "company with this subdomin already exit"

        if username:
            if User.objects.filter(username__iexact=username):
                errors["username"] = "User name already exit."
        if email:
            if User.objects.filter(email__iexact=email):
                errors["email"] = "Email already exit."

        if password:
            if len(password) < 8:
                errors["password"] = "Password must be at least 8 characters long!"

        if errors:
            return Response(
                {"error": True, "errors": errors}, status=status.HTTP_400_BAD_REQUEST
            )
        else:
            user = User.objects.create(username=username, email=email)
            company = Company.objects.create(sub_domain=sub_domain)
            company.save()
            user.company = company
            user.role = "ADMIN"
            user.is_superuser = False
            user.has_marketing_access = True
            user.has_sales_access = True
            user.is_admin = True
            user.set_password(password)
            user.save()
            return Response({"error": False}, status=status.HTTP_201_CREATED)


@swagger_auto_schema(
    method="post",
    tags=["Auth"],
    manual_parameters=swagger_params.check_sub_domain_params,
)
@api_view(["POST"])
def check_sub_domain(request):
    if request.method == "POST":
        params = request.query_params if len(request.data) == 0 else request.data
        sub_domain = params.get("sub_domain", None)
        msg = _("Given sub_domain {domain_name} is {validity_status}")
        company = Company.objects.filter(sub_domain=sub_domain).first()
        if company:
            request.session["company"] = company.id
            msg = msg.format(domain_name=sub_domain, validity_status="Valid")
            status_code = status.HTTP_200_OK
            status_msg = False
        else:
            msg = msg.format(domain_name=sub_domain, validity_status="Invalid")
            status_code = status.HTTP_400_BAD_REQUEST
            status_msg = True
        return Response({"error": status_msg, "message": msg}, status=status_code)


class ProfileView(APIView):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        tags=["Profile"], manual_parameters=swagger_params.dashboard_params
    )
    def get(self, request, format=None):
        context = {}
        context["user_obj"] = UserSerializer(request.user).data
        return Response(context, status=status.HTTP_200_OK)


class UsersListView(APIView):

    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        tags=["Users"], manual_parameters=swagger_params.user_create_params
    )
    def post(self, request, format=None):
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            return Response(
                {"error": True, "Message": "Permission Denied"},
                status=status.HTTP_403_FORBIDDEN,
            )
        else:
            params = request.query_params if len(request.data) == 0 else request.data
            if params:
                user_serializer = CreateUserSerializer(
                    data=params, request_user=request.user
                )
                if user_serializer.is_valid():
                    user = user_serializer.save()
                    if params.get("password"):
                        user.set_password(params.get("password"))
                    user.company = self.request.company
                    user.save()

                    current_site = request.get_host()
                    protocol = request.scheme
                    send_email_to_new_user.delay(
                        user.email,
                        self.request.user.email,
                        domain=current_site,
                        protocol=protocol,
                    )
                    return Response(
                        {"error": False, "message": "User Created Successfully"},
                        status=status.HTTP_201_CREATED,
                    )
                return Response(
                    {"error": True, "errors": user_serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

    @swagger_auto_schema(
        tags=["Users"], manual_parameters=swagger_params.user_list_params
    )
    def get(self, request, format=None):
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            return Response(
                {"error": True, "Message": "Permission Denied"},
                status=status.HTTP_403_FORBIDDEN,
            )
        else:
            queryset = User.objects.filter(company=self.request.company)
            params = (
                self.request.query_params
                if len(self.request.data) == 0
                else self.request.data
            )
            if params:
                if params.get("username"):
                    queryset = queryset.filter(
                        username__icontains=params.get("username")
                    )
                if params.get("email"):
                    queryset = queryset.filter(email__icontains=params.get("email"))
                if params.get("role"):
                    queryset = queryset.filter(role=params.get("role"))
                if params.get("status"):
                    queryset = queryset.filter(is_active=params.get("status"))

            context = {}
            active_users = queryset.filter(is_active=True)
            inactive_users = queryset.filter(is_active=False)
            context["active_users"] = UserSerializer(active_users, many=True).data
            context["inactive_users"] = UserSerializer(inactive_users, many=True).data
            context["admin_email"] = settings.ADMIN_EMAIL
            context["roles"] = ROLES
            context["status"] = [("True", "Active"), ("False", "In Active")]
            return Response(context)


class DocumentListView(APIView):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    model = Document

    def get_context_data(self, **kwargs):
        params = (
            self.request.query_params
            if len(self.request.data) == 0
            else self.request.data
        )
        queryset = self.model.objects.filter(company=self.request.company)
        if self.request.user.is_superuser or self.request.user.role == "ADMIN":
            queryset = queryset
        else:
            if self.request.user.documents():
                doc_ids = self.request.user.documents().values_list("id", flat=True)
                shared_ids = queryset.filter(
                    Q(status="active") & Q(shared_to__id__in=[self.request.user.id])
                ).values_list("id", flat=True)
                queryset = queryset.filter(Q(id__in=doc_ids) | Q(id__in=shared_ids))
            else:
                queryset = queryset.filter(
                    Q(status="active") & Q(shared_to__id__in=[self.request.user.id])
                )

        request_post = params
        if request_post:
            if request_post.get("title"):
                queryset = queryset.filter(title__icontains=request_post.get("title"))
            if request_post.get("status"):
                queryset = queryset.filter(status=request_post.get("status"))

            if request_post.get("shared_to"):
                queryset = queryset.filter(
                    shared_to__id__in=json.loads(request_post.get("shared_to"))
                )

        context = {}
        if self.request.user.role == "ADMIN" or self.request.user.is_superuser:
            users = User.objects.filter(
                is_active=True, company=self.request.company
            ).order_by("email")
        else:
            users = User.objects.filter(
                role="ADMIN", company=self.request.company
            ).order_by("email")
        search = False
        if (
            params.get("document_file")
            or params.get("status")
            or params.get("shared_to")
        ):
            search = True
        context["search"] = search
        context["documents_active"] = DocumentSerializer(
            queryset.filter(status="active").distinct(), many=True
        ).data
        context["documents_inactive"] = DocumentSerializer(
            queryset.filter(status="inactive").distinct(), many=True
        ).data
        context["users"] = UserSerializer(users, many=True).data
        context["status_choices"] = Document.DOCUMENT_STATUS_CHOICE
        return context

    @swagger_auto_schema(
        tags=["documents"], manual_parameters=swagger_params.document_get_params
    )
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return Response(context)

    @swagger_auto_schema(
        tags=["documents"], manual_parameters=swagger_params.document_create_params
    )
    def post(self, request, *args, **kwargs):
        params = request.query_params if len(request.data) == 0 else request.data
        serializer = DocumentCreateSerializer(data=params, request_obj=request)
        if serializer.is_valid():
            doc = serializer.save(
                created_by=request.user,
                company=request.company,
                document_file=request.FILES.get("document_file"),
            )
            if params.get("shared_to"):
                assinged_to_users_ids = json.loads(params.get("shared_to"))
                for user_id in assinged_to_users_ids:
                    user = User.objects.filter(id=user_id, company=request.company)
                    if user:
                        doc.shared_to.add(user_id)
                    else:
                        doc.delete()
                        return Response({"error": True, "error": "Enter Valid User"})
            if self.request.user.role == "ADMIN":
                if params.get("teams"):
                    teams = json.loads(params.get("teams"))
                    for team in teams:
                        teams_ids = Teams.objects.filter(
                            id=team, company=request.company
                        )
                        if teams_ids:
                            doc.teams.add(team)
                        else:
                            doc.delete()
                            return Response(
                                {"error": True, "error": "Enter Valid Team"}
                            )

            return Response(
                {"error": False, "message": "Document Created Successfully"},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class DocumentDetailView(APIView):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        return Document.objects.filter(id=pk).first()

    @swagger_auto_schema(
        tags=["documents"], manual_parameters=swagger_params.dashboard_params
    )
    def get(self, request, pk, format=None):
        self.object = self.get_object(pk)
        if not self.object or self.object.company != self.request.company:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            if not (
                (self.request.user == self.object.created_by)
                or (self.request.user in self.object.shared_to.all())
            ):
                return Response(
                    {
                        "error": True,
                        "errors": "You do not have Permission to perform this action",
                    }
                )
        if request.user.role == "ADMIN" or request.user.is_superuser:
            users = User.objects.filter(
                is_active=True, company=request.company
            ).order_by("email")
        else:
            users = User.objects.filter(role="ADMIN").order_by("email")
        context = {}
        context.update(
            {
                "doc_obj": DocumentSerializer(self.object).data,
                "file_type_code": self.object.file_type()[1],
                "users": UserSerializer(users, many=True).data,
            }
        )
        return Response(context, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        tags=["documents"], manual_parameters=swagger_params.dashboard_params
    )
    def delete(self, request, pk, format=None):
        document = self.get_object(pk)
        if not document or document.company != self.request.company:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            if (
                self.request.user != document.created_by
            ):  # or (self.request.user not in document.shared_to.all()):
                return Response(
                    {
                        "error": True,
                        "errors": "You do not have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
        document.delete()
        return Response(
            {"error": False, "message": "Document deleted Successfully"},
            status=status.HTTP_200_OK,
        )

    @swagger_auto_schema(
        tags=["documents"], manual_parameters=swagger_params.document_update_params
    )
    def put(self, request, pk, format=None):
        self.object = self.get_object(pk)
        params = request.query_params if len(request.data) == 0 else request.data
        if not self.object or self.object.company != self.request.company:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            if not (
                (self.request.user == self.object.created_by)
                or (self.request.user in self.object.shared_to.all())
            ):
                return Response(
                    {
                        "error": True,
                        "errors": "You do not have Permission to perform this action",
                    }
                )
        serializer = DocumentCreateSerializer(
            data=params, instance=self.object, request_obj=request
        )
        if serializer.is_valid():
            doc = serializer.save(
                document_file=request.FILES.get("document_file"),
                status=params.get("status"),
            )
            doc.shared_to.clear()
            if params.get("shared_to"):
                assinged_to_users_ids = json.loads(params.get("shared_to"))
                for user_id in assinged_to_users_ids:
                    user = User.objects.filter(id=user_id, company=request.company)
                    if user:
                        doc.shared_to.add(user_id)
                    else:
                        return Response({"error": True, "error": "Enter Valid User"})

            if self.request.user.role == "ADMIN":
                doc.teams.clear()
                if params.get("teams"):
                    teams = json.loads(params.get("teams"))
                    for team in teams:
                        teams_ids = Teams.objects.filter(
                            id=team, company=request.company
                        )
                        if teams_ids:
                            doc.teams.add(team)
                        else:
                            return Response(
                                {"error": True, "error": "Enter Valid Team"}
                            )
            return Response(
                {"error": False, "message": "Document Updated Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class ForgotPasswordView(APIView):
    @swagger_auto_schema(
        tags=["Auth"], manual_parameters=swagger_params.forgot_password_params
    )
    def post(self, request, format=None):
        params = request.query_params if len(request.data) == 0 else request.data
        serializer = ForgotPasswordSerializer(data=params)
        if serializer.is_valid():
            user = get_object_or_404(User, email=params.get("email"))
            current_site = self.request.get_host()
            protocol = self.request.scheme
            send_email_to_reset_password.delay(
                user.email, protocol=protocol, domain=current_site
            )
            data = {
                "error": False,
                "message": "We have sent you an email. please reset password",
            }
            return Response(data, status=status.HTTP_200_OK)
        else:
            data = {"error": True, "errors": serializer.errors}
            response_status = status.HTTP_400_BAD_REQUEST
        return Response(data, status=response_status)


class ResetPasswordView(APIView):
    @swagger_auto_schema(
        tags=["Auth"], manual_parameters=swagger_params.reset_password_params
    )
    def post(self, request, format=None):
        params = request.query_params if len(request.data) == 0 else request.data
        serializer = ResetPasswordSerailizer(data=params)
        if serializer.is_valid():
            password = params.get("new_password1")
            user = serializer.user
            user.set_password(password)
            user.save()
            data = {
                "error": False,
                "message": "Password Updated Successfully. Please login",
            }
        else:
            data = {"error": True, "errors": serializer.errors}
        return Response(data, status=status.HTTP_400_BAD_REQUEST)


class ContactsEmailCampaignListView(APIView):
    model = ContactEmailCampaign
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_context_data(self, **kwargs):
        params = (
            self.request.query_params
            if len(self.request.data) == 0
            else self.request.data
        )
        queryset = self.model.objects.filter(company=self.request.company)

        context = {}
        search = False
        if params:
            if params.get("name"):
                queryset = queryset.filter(
                    Q(name__icontains=params.get("name"))
                    | Q(last_name__icontains=params.get("name"))
                )
            if params.get("email"):
                queryset = queryset.filter(email__icontains=params.get("email"))
            if params.get("created_by"):
                queryset = queryset.filter(created_by=params.get("created_by"))
            search = True

        context["search"] = search

        context["contacts"] = ContactEmailCampaignSerailizer(queryset, many=True).data
        users = User.objects.filter(
            is_active=True, role="ADMIN", company=self.request.company
        ).order_by("email")

        context["users"] = UserSerializer(users, many=True).data
        return context

    @swagger_auto_schema(
        tags=["Settings"], manual_parameters=swagger_params.settings_contact_get_params
    )
    def get(self, request, *args, **kwargs):
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            return Response(
                {
                    "error": True,
                    "errors": "You do not have permission to perform this action",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        context = self.get_context_data(**kwargs)
        return Response(context)

    @swagger_auto_schema(
        tags=["Settings"],
        manual_parameters=swagger_params.settings_contact_create_params,
    )
    def post(self, request, *args, **kwargs):
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            return Response(
                {
                    "error": True,
                    "errors": "You do not have permission to perform this action",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        params = (
            self.request.query_params
            if len(self.request.data) == 0
            else self.request.data
        )

        serializer = ContactEmailCampaignSerailizer(data=params, request_obj=request)
        if serializer.is_valid():
            serializer.save(created_by=request.user, company=request.company)
            return Response(
                {"error": False, "message": "Email for Campaign created Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class ContactsEmailCampaignDetailView(APIView):
    model = ContactEmailCampaign
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        return self.model.objects.get(pk=pk)

    # def get_context_data(self, **kwargs):
    #     context = {}
    #     context["contacts"] = ContactEmailCampaignSerailizer(
    #                                 self.contact_obj).data
    #     users = User.objects.filter(
    #             is_active=True,
    #             role = "ADMIN",
    #             company=self.request.company).order_by("email")

    #     context["users"] = UserSerializer(users, many=True).data
    #     return context

    # @swagger_auto_schema(
    #     tags=["Settings"], manual_parameters=swagger_params.dashboard_params
    # )
    # def get(self, request, pk, **kwargs):
    #     if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
    #         return Response({
    #             "error": True,
    #             "errors": "You do not have permission to perform this action"},
    #              status = status.HTTP_403_FORBIDDEN
    #         )
    #     self.contact_obj = self.get_object(pk)
    #     if self.contact_obj.company != request.company:
    #         return Response(
    #             {"error": True,
    #              "errors": "User company doesnot match with header...."}
    #         )
    #     context = self.get_context_data(**kwargs)
    #     return Response(context)

    @swagger_auto_schema(
        tags=["Settings"],
        manual_parameters=swagger_params.settings_contact_create_params,
    )
    def put(self, request, pk, format=None):
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            return Response(
                {
                    "error": True,
                    "errors": "You do not have permission to perform this action",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        params = request.query_params if len(request.data) == 0 else request.data
        obj = self.get_object(pk)
        if obj.company != request.company:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."}
            )
        serializer = ContactEmailCampaignSerailizer(obj, data=params)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"error": False, "message": "Email for Campaign Updated Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @swagger_auto_schema(
        tags=["Settings"], manual_parameters=swagger_params.dashboard_params
    )
    def delete(self, request, pk, format=None):
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            return Response(
                {
                    "error": True,
                    "errors": "You do not have permission to perform this action",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        self.object = self.get_object(pk)
        if self.object.company != request.company:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."}
            )
        self.object.delete()
        return Response(
            {"error": True, "errors": "Email for Campaign Deleted Successfully"},
            status=status.HTTP_200_OK,
        )


class BlockDomainsListView(APIView):
    model = BlockedDomain
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_context_data(self, **kwargs):
        params = (
            self.request.query_params
            if len(self.request.data) == 0
            else self.request.data
        )
        queryset = self.model.objects.filter(company=self.request.company)

        context = {}
        search = False
        if params:
            if params.get("domain"):
                queryset = queryset.filter(Q(domain__icontains=params.get("domain")))
            search = True

        context["search"] = search

        context["blocked_domains"] = BlockedDomainSerailizer(queryset, many=True).data
        return context

    @swagger_auto_schema(
        tags=["Settings"],
        manual_parameters=swagger_params.settings_blockdomains_create_params,
    )
    def get(self, request, *args, **kwargs):
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            return Response(
                {
                    "error": True,
                    "errors": "You do not have permission to perform this action",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        context = self.get_context_data(**kwargs)
        return Response(context)

    @swagger_auto_schema(
        tags=["Settings"],
        manual_parameters=swagger_params.settings_blockdomains_create_params,
    )
    def post(self, request, *args, **kwargs):
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            return Response(
                {
                    "error": True,
                    "errors": "You do not have permission to perform this action",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        params = (
            self.request.query_params
            if len(self.request.data) == 0
            else self.request.data
        )

        serializer = BlockedDomainAddSerailizer(data=params, request_obj=request)
        if serializer.is_valid():
            serializer.save(created_by=request.user, company=request.company)
            return Response(
                {"error": False, "message": "Blocked Domain created Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class BlockDomainsDetailView(APIView):
    model = BlockedDomain
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        return self.model.objects.get(pk=pk)

    # def get_context_data(self, **kwargs):
    #     context = {}
    #     context["blocked_domains"] = BlockedDomainSerailizer(
    #                                 self.obj).data
    #     return context

    # @swagger_auto_schema(
    #     tags=["Settings"], manual_parameters=swagger_params.dashboard_params
    # )
    # def get(self, request, pk, **kwargs):
    #     if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
    #         return Response({
    #             "error": True,
    #             "errors": "You do not have permission to perform this action"},
    #              status = status.HTTP_403_FORBIDDEN
    #         )
    #     self.obj = self.get_object(pk)
    #     if self.obj.company != request.company:
    #         return Response(
    #             {"error": True,
    #              "errors": "User company doesnot match with header...."}
    #         )
    #     context = self.get_context_data(**kwargs)
    #     return Response(context)

    @swagger_auto_schema(
        tags=["Settings"],
        manual_parameters=swagger_params.settings_blockdomains_create_params,
    )
    def put(self, request, pk, format=None):
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            return Response(
                {
                    "error": True,
                    "errors": "You do not have permission to perform this action",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        params = request.query_params if len(request.data) == 0 else request.data
        obj = self.get_object(pk)
        if obj.company != request.company:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."}
            )
        serializer = BlockedDomainAddSerailizer(obj, data=params, request_obj=request)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"error": False, "message": "Blocked Domain Updated Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @swagger_auto_schema(
        tags=["Settings"], manual_parameters=swagger_params.dashboard_params
    )
    def delete(self, request, pk, format=None):
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            return Response(
                {
                    "error": True,
                    "errors": "You do not have permission to perform this action",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        self.object = self.get_object(pk)
        if self.object.company != request.company:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."}
            )
        self.object.delete()
        return Response(
            {"error": True, "errors": "Blocked Domain Deleted Successfully"},
            status=status.HTTP_200_OK,
        )


class BlockEmailsListView(APIView):
    model = BlockedEmail
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_context_data(self, **kwargs):
        params = (
            self.request.query_params
            if len(self.request.data) == 0
            else self.request.data
        )
        queryset = self.model.objects.filter(company=self.request.company)

        context = {}
        search = False
        if params:
            if params.get("email"):
                queryset = queryset.filter(Q(email__icontains=params.get("email")))
            search = True

        context["search"] = search

        context["blocked_emails"] = BlockedEmailSerailizer(queryset, many=True).data
        return context

    @swagger_auto_schema(
        tags=["Settings"],
        manual_parameters=swagger_params.settings_blockemails_create_params,
    )
    def get(self, request, *args, **kwargs):
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            return Response(
                {
                    "error": True,
                    "errors": "You do not have permission to perform this action",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        context = self.get_context_data(**kwargs)
        return Response(context)

    @swagger_auto_schema(
        tags=["Settings"],
        manual_parameters=swagger_params.settings_blockemails_create_params,
    )
    def post(self, request, *args, **kwargs):
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            return Response(
                {
                    "error": True,
                    "errors": "You do not have permission to perform this action",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        params = (
            self.request.query_params
            if len(self.request.data) == 0
            else self.request.data
        )

        serializer = BlockedEmailAddSerailizer(data=params, request_obj=request)
        if serializer.is_valid():
            serializer.save(created_by=request.user, company=request.company)
            return Response(
                {"error": False, "message": "Blocked Email added Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class BlockEmailsDetailView(APIView):
    model = BlockedEmail
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        return self.model.objects.get(pk=pk)

    # def get_context_data(self, **kwargs):
    #     context = {}
    #     context["blocked_emails"] = BlockedEmailSerailizer(
    #                                 self.obj).data
    #     return context

    # @swagger_auto_schema(
    #     tags=["Settings"],
    #     manual_parameters=swagger_params.dashboard_params
    # )
    # def get(self, request, pk, **kwargs):
    #     if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
    #         return Response({
    #             "error": True,
    #             "errors": "You do not have permission to perform this action"},
    #              status = status.HTTP_403_FORBIDDEN
    #         )
    #     self.obj = self.get_object(pk)
    #     if self.obj.company != request.company:
    #         return Response(
    #             {"error": True,
    #              "errors": "User company doesnot match with header...."}
    #         )
    #     context = self.get_context_data(**kwargs)
    #     return Response(context)

    @swagger_auto_schema(
        tags=["Settings"],
        manual_parameters=swagger_params.settings_blockemails_create_params,
    )
    def put(self, request, pk, format=None):
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            return Response(
                {
                    "error": True,
                    "errors": "You do not have permission to perform this action",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        params = request.query_params if len(request.data) == 0 else request.data
        obj = self.get_object(pk)
        if obj.company != request.company:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."}
            )
        serializer = BlockedEmailAddSerailizer(obj, data=params, request_obj=request)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"error": False, "message": "Blocked Email Updated Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @swagger_auto_schema(
        tags=["Settings"], manual_parameters=swagger_params.dashboard_params
    )
    def delete(self, request, pk, format=None):
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            return Response(
                {
                    "error": True,
                    "errors": "You do not have permission to perform this action",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        self.object = self.get_object(pk)
        if self.object.company != request.company:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."}
            )
        self.object.delete()
        return Response(
            {"error": True, "errors": "Blocked Email Deleted Successfully"},
            status=status.HTTP_200_OK,
        )


class UserStatusView(APIView):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        tags=["Users"], manual_parameters=swagger_params.users_status_params
    )
    def post(self, request, pk, format=None):
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            return Response(
                {
                    "error": True,
                    "errors": "You do not have permission to perform this action",
                }
            )
        params = request.query_params if len(request.data) == 0 else request.data
        user = User.objects.get(id=pk, company=request.company)
        if user.company != request.company:
            return Response(
                {
                    "error": True,
                    "errors": "User company does not match with the header",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if params.get("status"):
            status = params.get("status")
            if status == "Active":
                user.is_active = True
            elif status == "Inactive":
                user.is_active = False
            else:
                return Response(
                    {"error": True, "errors": "Please enter Valid Status for user"}
                )
            user.save()

        context = {}
        users_Active = User.objects.filter(is_active=True, company=request.company)
        users_Inactive = User.objects.filter(is_active=False, company=request.company)
        context["Users_Active"] = UserSerializer(users_Active, many=True).data
        context["Users_Inactive"] = UserSerializer(users_Inactive, many=True).data
        return Response(context)
