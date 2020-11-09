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
from accounts.models import (Account, Contact)
from opportunity.models import Opportunity
from cases.models import Case
from leads.models import Lead
from teams.models import Teams
from common.forms import DocumentForm
from common.utils import ROLES
from common.models import User, Company
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
    send_email_to_reset_password
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


class UserDetailView(APIView):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(tags=["users"], manual_parameters=swagger_params.dashboard_params)
    def get(self, request, *args, **kwargs):
        company = request.headers['company']
        user_id = kwargs['pk']
        user_obj = get_object_or_404(
            User, pk=user_id, company__sub_domain=company)
        users_data = []
        for each in User.objects.all():
            assigned_dict = {}
            assigned_dict["id"] = each.id
            assigned_dict["name"] = each.username
            users_data.append(assigned_dict)
        context = {}
        context["user_obj"] = UserSerializer(user_obj).data
        opportunity_list = Opportunity.objects.filter(assigned_to=user_obj.id)
        context["opportunity_list"] = OpportunitySerializer(
            opportunity_list, many=True).data
        contacts = Contact.objects.filter(assigned_to=user_obj.id)
        context["contacts"] = ContactSerializer(contacts, many=True).data
        cases = Case.objects.filter(assigned_to=user_obj.id)
        context["cases"] = CaseSerializer(cases, many=True).data
        # "accounts": Account.objects.filter(assigned_to=user_obj.id)
        # context["assigned_data"] = json.dumps(users_data)
        context["assigned_data"] = users_data
        comments = user_obj.user_comments.all()
        context["comments"] = CommentSerializer(comments, many=True).data
        return Response(context)


class GetTeamsAndUsersView(APIView):

    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(tags=["users"], manual_parameters=swagger_params.dashboard_params)
    def get(self, request, *args, **kwargs):
        data = {}
        teams = Teams.objects.filter(company=request.company)
        # teams_data = [
        #     {"team": team.id, "users": [user.id for user in team.users.all()]}
        #     for team in teams
        # ]
        teams_data = TeamsSerializer(teams, many=True).data
        users = User.objects.filter(company=request.company)
        users_data = UserSerializer(users, many=True).data

        users = User.objects.all().values_list("id", flat=True)
        data["teams"] = teams_data
        data["users_data"] = users_data
        data["users"] = list(users)
        return Response(data)


# to be checked
class UserDeleteView(APIView):
    model = User

    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(tags=["users"], manual_parameters=swagger_params.dashboard_params)
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        current_site = request.get_host()
        deleted_by = self.request.user.email
        send_email_user_delete.delay(
            self.object.email,
            deleted_by=deleted_by,
            domain=current_site,
            protocol=request.scheme,
        )
        self.object.delete()
        return Response({'status': 'success'}, status=status.HTTP_204_NO_CONTENT)


class ChangePasswordView(APIView):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(tags=["profile"], operation_description="This is change password api",
                         manual_parameters=swagger_params.change_password_params)
    def post(self, request, format=None):
        params = request.query_params if len(
            request.data) == 0 else request.data
        company = request.headers['company']
        old_password = params.get("old_password", None)
        new_password = params.get("new_password", None)
        retype_password = params.get("retype_password", None)
        company_obj = Company.objects.filter(sub_domain=company).first()
        errors = {}
        if request.company.id is not company_obj.id:
            errors["company"] = "Company header doesnot match."
        if old_password:
            if not request.user.check_password(old_password):
                errors["old_password"] = "old password entered is incorrect."

        if new_password:
            if len(new_password) < 8:
                errors['new_password'] = "Password must be at least 8 characters long!"
            if new_password == old_password:
                errors[
                    'new_password'] = "New password and old password should not be same"
        if retype_password:
            if new_password != retype_password:
                errors[
                    'retype_password'] = "new_password and retype_password did not match."

        if errors:
            return Response({'status': 'failure', 'errors': errors}, status=400)
        user = request.user
        user.set_password(new_password)
        user.save()
        return Response({'status': 'success'}, status=200)


# check_header not working
class ApiHomeView(APIView):

    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(tags=["dashboard"], manual_parameters=swagger_params.dashboard_params)
    def get(self, request, format=None):

        accounts = Account.objects.filter(status="open")
        contacts = Contact.objects.all()
        leads = Lead.objects.exclude(
            status="converted").exclude(status="closed")
        opportunities = Opportunity.objects.all()
        if self.request.user.role == "ADMIN" or self.request.user.is_superuser:
            pass
        else:
            accounts = accounts.filter(Q(assigned_to__id__in=[self.request.user.id]) | Q(
                created_by=self.request.user.id))
            contacts = contacts.filter(Q(assigned_to__id__in=[self.request.user.id]) | Q(
                created_by=self.request.user.id))
            leads = leads.filter(Q(assigned_to__id__in=[self.request.user.id]) | Q(
                created_by=self.request.user.id)).exclude(status="closed")
            opportunities = opportunities.filter(
                Q(assigned_to__id__in=[self.request.user.id]) | Q(created_by=self.request.user.id))
        context = {}
        context["leads_count"] = leads.count()
        context["accounts_count"] = accounts.count()
        context["contacts_count"] = contacts.count()
        context["opportunities_count"] = opportunities.count()
        accounts = AccountSerializer(accounts, many=True).data
        opportunities = OpportunitySerializer(opportunities, many=True).data
        context["accounts"] = accounts
        context["opportunities"] = opportunities
        return Response(context)


class LoginView(APIView):

    @swagger_auto_schema(tags=["common"], operation_description="This is login api",
                         manual_parameters=swagger_params.login_page_params)
    def post(self, request, format=None):
        params = request.query_params if len(
            request.data) == 0 else request.data
        company = request.headers['company']
        username = params.get("email", None)
        password = params.get("password", None)
        company_obj = Company.objects.filter(sub_domain=company).first()
        if not company_obj:
            company_field = "doesnot exit"
            msg = _('company with this subdomin {company_field}')
            msg = msg.format(company_field=company_field)
            return Response({'status': 'failure', 'message': msg}, status=400)
            # raise APIException(msg)
        if not username:
            username_field = "User Name/Email"
            msg = _('Must include "{username_field}"')
            msg = msg.format(username_field=username_field)
            return Response({'status': 'failure', 'message': msg}, status=400)
            # raise APIException(msg)

        user = User.objects.filter(email=username, company=company_obj).first()
        if not user:
            return Response({'status': 'failure', 'message': 'user not avaliable in our records'}, status=400)
        if user.check_password(password):
            payload = jwt_payload_handler(user)
            response_data = {
                'token': jwt_encode_handler(payload),
                'status': 'success',
                'company': user.company.id,
                'subdomin': company_obj.sub_domain
            }
            return Response(response_data)
        else:
            password_field = "doesnot match"
            msg = _('Email and password {password_field}')
            msg = msg.format(password_field=password_field)
            return Response({'status': 'failure', 'message': msg}, status=400)


class RegistrationView(APIView):

    @swagger_auto_schema(tags=["common"], operation_description="This is registration api",
                         manual_parameters=swagger_params.registration_page_params)
    def post(self, request, format=None):
        params = request.query_params if len(
            request.data) == 0 else request.data
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
                errors['username'] = "User name already exit."
        if email:
            if User.objects.filter(email__iexact=email):
                errors['email'] = "Email already exit."

        if password:
            if len(password) < 8:
                errors['password'] = "Password must be at least 8 characters long!"

        if errors:
            return Response({'status': 'failure', 'errors': errors}, status=400)
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
            return Response({'status': 'success'}, status=201)


@swagger_auto_schema(method='post', tags=["common"], manual_parameters=swagger_params.check_sub_domain_params)
@api_view(['POST'])
def check_sub_domain(request):
    if request.method == "POST":
        params = request.query_params if len(
            request.data) == 0 else request.data
        sub_domain = params.get("sub_domain", None)
        msg = _('Given sub_domain {domain_name} is {validity_status}')
        company = Company.objects.filter(sub_domain=sub_domain).first()
        if company:
            request.session["company"] = company.id
            msg = msg.format(domain_name=sub_domain, validity_status="Valid")
            status_code = 200
            status_msg = "success"
        else:
            msg = msg.format(domain_name=sub_domain, validity_status="Invalid")
            status_code = 400
            status_msg = "failure"
        return Response({'status': status_msg, 'message': msg}, status=status_code)


class ProfileView(APIView):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(tags=["profile"], manual_parameters=swagger_params.dashboard_params)
    def get(self, request, format=None):
        context = {}
        context["user_obj"] = UserSerializer(request.user).data
        return Response(context)


class UsersListView(APIView):

    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(tags=["users"], manual_parameters=swagger_params.user_list_params)
    def post(self, request, format=None):

        context = {}
        queryset = User.objects.filter(company=self.request.company)
        params = request.query_params if len(
            request.data) == 0 else request.data
        if params:
            if params.get("username"):
                queryset = queryset.filter(
                    username__icontains=params.get("username")
                )
            if params.get("email"):
                queryset = queryset.filter(
                    email__icontains=params.get("email"))
            if params.get("role"):
                queryset = queryset.filter(role=params.get("role"))
            if params.get("status"):
                queryset = queryset.filter(is_active=params.get("status"))
        active_users = queryset.filter(is_active=True)
        inactive_users = queryset.filter(is_active=False)
        context["active_users"] = UserSerializer(active_users, many=True).data
        context["inactive_users"] = UserSerializer(
            inactive_users, many=True).data
        context["per_page"] = self.request.POST.get("per_page")
        context["admin_email"] = settings.ADMIN_EMAIL
        context["roles"] = ROLES
        context["status"] = [("True", "Active"), ("False", "In Active")]

        return Response(context)

    @swagger_auto_schema(tags=["users"], manual_parameters=swagger_params.dashboard_params)
    def get(self, request, format=None):

        queryset = User.objects.filter(company=self.request.company)
        context = {}
        active_users = queryset.filter(is_active=True)
        inactive_users = queryset.filter(is_active=False)
        context["active_users"] = UserSerializer(active_users, many=True).data
        context["inactive_users"] = UserSerializer(
            inactive_users, many=True).data
        context["per_page"] = self.request.POST.get("per_page")
        context["admin_email"] = settings.ADMIN_EMAIL
        context["roles"] = ROLES
        context["status"] = [("True", "Active"), ("False", "In Active")]
        return Response(context)


class DocumentCreate(APIView):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(tags=["documents"], manual_parameters=swagger_params.dashboard_params)
    def get(self, request, format=None):
        users = []
        if request.user.role == "ADMIN" or request.user.is_superuser:
            users = User.objects.filter(is_active=True, company=request.company).order_by(
                "email"
            )
        else:
            users = User.objects.filter(role="ADMIN", company=request.company).order_by(
                "email"
            )
        context = {}
        context["users"] = UserSerializer(users, many=True).data
        teams = Teams.objects.filter(company=request.company)
        context["teams"] = TeamsSerializer(teams, many=True).data
        context['status'] = (("active", "active"), ("inactive", "inactive"))
        return Response(context)

    # to be checked file upload
    @swagger_auto_schema(tags=["documents"], manual_parameters=swagger_params.document_create_params)
    def post(self, request, format=None):
        params = request.query_params if len(
            request.data) == 0 else request.data
        context = {}
        users = []
        if request.user.role == "ADMIN" or request.user.is_superuser:
            users = User.objects.filter(is_active=True, company=request.company).order_by(
                "email"
            )
        else:
            users = User.objects.filter(role="ADMIN", company=request.company).order_by(
                "email"
            )
        form = DocumentForm(
            params, request.FILES, users=users, request_obj=request
        )
        if form.is_valid():
            doc = form.save(commit=False)
            doc.created_by = request.user
            doc.company = request.company
            doc.save()
            if params.getlist("shared_to"):
                doc.shared_to.add(*params.getlist("shared_to"))
            if params.getlist("teams", []):
                user_ids = Teams.objects.filter(
                    id__in=params.getlist("teams")
                ).values_list("users", flat=True)
                assinged_to_users_ids = doc.shared_to.all().values_list("id", flat=True)
                for user_id in user_ids:
                    if user_id not in assinged_to_users_ids:
                        doc.shared_to.add(user_id)

            if params.getlist("teams", []):
                doc.teams.add(*params.getlist("teams"))

            data = {"error": False}
            return Response(data)
        return Response({"error": True, "errors": form.errors})
        context["errors"] = form.errors
        return Response(context)

# from common.forms import UserForm
# from common.utils import ROLES
# class CreateUserView(APIView):
#     # model = User
#     # form_class = UserForm
#     # template_name = "create.html"
#     # success_url = '/users/list/'
#     authentication_classes = (JSONWebTokenAuthentication,)
#     permission_classes = (IsAuthenticated,)
#     # def form_valid(self, form):
#     #     user = form.save(commit=False)
#     #     if form.cleaned_data.get("password"):
#     #         user.set_password(form.cleaned_data.get("password"))
#     #     user.company = self.request.company
#     #     user.save()

#     #     if self.request.POST.getlist("teams"):
#     #         for team in self.request.POST.getlist("teams"):
#     #             Teams.objects.filter(id=team).first().users.add(user)

#     #     current_site = self.request.get_host()
#     #     protocol = self.request.scheme
#     #     send_email_to_new_user.delay(
#     #         user.email, self.request.user.email, domain=current_site, protocol=protocol
#     #     )

#     #     if self.request.is_ajax():
#     #         data = {"success_url": reverse_lazy("common:users_list"), "error": False}
#     #         return Response(data)
#     #     return super(CreateUserView, self).form_valid(form)

#     # def form_invalid(self, form):
#     #     response = super(CreateUserView, self).form_invalid(form)
#     #     if self.request.is_ajax():
#     #         return Response({"error": True, "errors": form.errors})
#     #     return response

#     # def get_form_kwargs(self):
#     #     kwargs = super(CreateUserView, self).get_form_kwargs()
#     #     kwargs.update({"request_user": self.request.user})
#     #     return kwargs

#     # def get_context_data(self, **kwargs):
#     #     context = super(CreateUserView, self).get_context_data(**kwargs)
#     #     context["user_form"] = context["form"]
#     #     context["teams"] = Teams.objects.all()
#     #     if "errors" in kwargs:
#     #         context["errors"] = kwargs["errors"]
#     #     return context

#     @swagger_auto_schema(tags=["user create"], manual_parameters=swagger_params.dashboard_params)
#     def get(self, request, format=None):
#         context = {}
#         context['role'] = ROLES
#         teams = Teams.objects.filter(company=request.company)
#         context["teams"] = TeamsSerializer(teams, many=True).data
#         return Response(context)


#     @swagger_auto_schema(tags=["user create"], operation_description="Create user",
#                          manual_parameters=swagger_params.user_create_params)
#     def post(self, request, format=None):
#         params = request.query_params if len(request.data) == 0 else request.data

#         form = UserForm(params, request_user=self.request)

#         if form.is_valid():
#             user = form.save(commit=False)
#             if form.cleaned_data.get("password"):
#                 user.set_password(form.cleaned_data.get("password"))
#             user.company = self.request.company
#             user.save()

#             if self.request.POST.getlist("teams"):
#                 for team in self.request.POST.getlist("teams"):
#                     Teams.objects.filter(id=team).first().users.add(user)

#             data = { "error": False}
#             return Response(data)

#         # if self.request.is_ajax():
#         return Response({"error": True, "errors": form.errors})


class ForgotPasswordView(APIView):

    @swagger_auto_schema(tags=["common"], manual_parameters=swagger_params.forgot_password_params)
    def post(self, request, format=None):
        params = request.query_params if len(
            request.data) == 0 else request.data
        serializer = ForgotPasswordSerializer(data=params)
        if serializer.is_valid():
            user = get_object_or_404(User, email=params.get('email'))
            current_site = self.request.get_host()
            protocol = self.request.scheme
            send_email_to_reset_password.delay(
                user.email, protocol=protocol, domain=current_site)
            data = {"error": False,
                    "message": "We have sent you an email. please reset password"}
            return Response(data)
        else:
            data = {"error": True, "errors": serializer.errors}
            response_status = status.HTTP_400_BAD_REQUEST
        return Response(data, status=response_status)


class ResetPasswordView(APIView):

    @swagger_auto_schema(tags=["common"], manual_parameters=swagger_params.reset_password_params)
    def post(self, request, format=None):
        params = request.query_params if len(
            request.data) == 0 else request.data
        serializer = ResetPasswordSerailizer(data=params)
        if serializer.is_valid():
            password = params.get('new_password1')
            user = serializer.user
            user.set_password(password)
            user.save()
            data = {"error": False,
                    "message": "Password Updated Successfully. Please login"}
        else:
            data = {"error": True, "errors": serializer.errors}
        return Response(data, status=status.HTTP_400_BAD_REQUEST)
