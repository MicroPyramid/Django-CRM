from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import get_object_or_404, redirect
from rest_framework import status
from accounts.serializer import AccountSerializer
from contacts.serializer import ContactSerializer
from opportunity.serializer import OpportunitySerializer
from leads.serializer import LeadSerializer
from teams.serializer import TeamsSerializer
from common.serializer import *
from cases.serializer import CaseSerializer
from accounts.models import Account, Contact
from opportunity.models import Opportunity
from accounts.models import Tags
from cases.models import Case
from leads.models import Lead
from teams.models import Teams
from common.utils import ROLES
from common.serializer import (
    RegisterOrganizationSerializer,
    CreateUserSerializer,
    PasswordChangeSerializer
)
from common.models import User, Org, Document, APISettings, Profile
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
from rest_framework.pagination import LimitOffsetPagination
from common.custom_auth import JSONWebTokenAuthentication
from common import swagger_params
from django.db.models import Q
from rest_framework.decorators import api_view
import json
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from common.token_generator import account_activation_token
from common.models import Profile
from django.utils import timezone
from django.conf import settings
from common.utils import COUNTRIES


class GetTeamsAndUsersView(APIView):

    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        tags=["Users"], manual_parameters=swagger_params.organization_params
    )
    def get(self, request, *args, **kwargs):
        if self.request.profile.role != "ADMIN" and not self.request.profile.is_admin:
            return Response(
                {"error": True, "errors": "Permission Denied"},
                status=status.HTTP_403_FORBIDDEN,
            )
        data = {}
        teams = Teams.objects.filter(org=request.org)
        teams_data = TeamsSerializer(teams, many=True).data
        users = Profile.objects.filter(is_active=True, org=request.org)
        users_data = ProfileSerializer(users, many=True).data
        data["teams"] = teams_data
        data["users_data"] = users_data
        return Response(data)


class UserDetailView(APIView):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        profile = get_object_or_404(Profile, pk=pk)
        return profile

    @swagger_auto_schema(
        tags=["Users"], manual_parameters=swagger_params.organization_params
    )
    def get(self, request, pk, format=None):
        user_obj = self.get_object(pk)
        if (
            self.request.profile.role != "ADMIN"
            and not self.request.profile.is_admin
            and self.request.profile.id != user_obj.id
        ):
            return Response(
                {"error": True, "errors": "Permission Denied"},
                status=status.HTTP_403_FORBIDDEN,
            )
        if user_obj.org != request.org:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_404_NOT_FOUND,
            )
        users_data = []
        for each in Profile.objects.filter(org=request.org, is_active=True):
            assigned_dict = {}
            assigned_dict["id"] = each.id
            assigned_dict["name"] = each.user.first_name
            users_data.append(assigned_dict)
        context = {}
        context["user_obj"] = ProfileSerializer(user_obj).data
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
        context["countries"] = COUNTRIES
        return Response(
            {"error": False, "data": context},
            status=status.HTTP_200_OK,
        )

    @swagger_auto_schema(
        tags=["Users"], manual_parameters=swagger_params.user_update_params
    )
    def put(self, request, pk, format=None):
        params = request.query_params if len(
            request.data) == 0 else request.data
        profile = self.get_object(pk)
        address_obj = profile.address
        if (
            self.request.profile.role != "ADMIN"
            and not self.request.user.is_admin
            and self.request.profile.id != profile.id
        ):
            return Response(
                {"error": True, "errors": "Permission Denied"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if profile.org != request.org:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = CreateUserSerializer(
            data=params, instance=profile.user, org=request.org)
        address_serializer = BillingAddressSerializer(
            data=params, instance=address_obj)
        profile_serializer = CreateProfileSerializer(
            data=params, instance=profile)
        data = {}
        if not serializer.is_valid():
            data["contact_errors"] = serializer.errors
        if not address_serializer.is_valid():
            data["address_errors"] = (address_serializer.errors,)
        if not profile_serializer.is_valid():
            data["profile_errors"] = (profile_serializer.errors,)
        if data:
            data["error"] = True
            return Response(
                data,
                status=status.HTTP_400_BAD_REQUEST,
            )
        if serializer.is_valid():
            address_obj = address_serializer.save()
            user = serializer.save()
            user.username = user.first_name
            user.save()
            profile = profile_serializer.save()
            if self.request.profile.role == "ADMIN":
                if params.getlist("teams"):
                    user_teams = profile.user_teams.all()

                    team_obj = Teams.objects.filter(org=request.org)
                    for team in params.getlist("teams"):
                        try:
                            team_obj = team_obj.filter(id=team).first()
                            if team_obj != user_teams:
                                team_obj.users.add(profile)
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
        tags=["Users"], manual_parameters=swagger_params.organization_params
    )
    def delete(self, request, pk, format=None):
        if self.request.profile.role != "ADMIN" and not self.request.profile.is_admin:
            return Response(
                {"error": True, "errors": "Permission Denied"},
                status=status.HTTP_403_FORBIDDEN,
            )
        self.object = self.get_object(pk)
        if self.object.id == request.profile.id:
            return Response(
                {"error": True, "errors": "Permission Denied"},
                status=status.HTTP_403_FORBIDDEN,
            )
        deleted_by = self.request.profile.user.email
        send_email_user_delete.delay(
            self.object.user.email,
            deleted_by=deleted_by,
            domain=settings.DOMAIN_NAME,
            protocol=request.scheme,
        )
        self.object.delete()
        return Response({"status": "success"}, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        tags=["Profile"],
        operation_description="This is change password api",
        manual_parameters=swagger_params.change_password_params,
    )
    def post(self, request, format=None):
        params = request.query_params if len(
            request.data) == 0 else request.data
        context = {'user': request.user}
        serializer = PasswordChangeSerializer(data=params, context=context)
        if serializer.is_valid():
            user = request.user
            user.set_password(params.get('new_password'))
            user.save()
            return Response(
                {"error": False, "message": "Password Changed Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


# check_header not working
class ApiHomeView(APIView):

    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        tags=["dashboard"], manual_parameters=swagger_params.organization_params
    )
    def get(self, request, format=None):
        accounts = Account.objects.filter(
            status="open", org=request.org)
        contacts = Contact.objects.filter(org=request.org)
        leads = Lead.objects.filter(org=request.org).exclude(
            Q(status="converted") | Q(status="closed"))
        opportunities = Opportunity.objects.filter(org=request.org)

        if self.request.profile.role == "ADMIN" or self.request.user.is_superuser:
            pass
        else:
            accounts = accounts.filter(
                Q(assigned_to__id__in=[self.request.profile.id])
                | Q(created_by=self.request.profile.id)
            )
            contacts = contacts.filter(
                Q(assigned_to__id__in=[self.request.profile.id])
                | Q(created_by=self.request.profile.id)
            )
            leads = leads.filter(
                Q(assigned_to__id__in=[self.request.profile.id])
                | Q(created_by=self.request.profile.id)
            ).exclude(status="closed")
            opportunities = opportunities.filter(
                Q(assigned_to__id__in=[self.request.profile.id])
                | Q(created_by=self.request.profile.id)
            )
        context = {}
        context["accounts_count"] = accounts.count()
        context["contacts_count"] = contacts.count()
        context["leads_count"] = leads.count()
        context["opportunities_count"] = opportunities.count()
        context["accounts"] = AccountSerializer(accounts, many=True).data
        context["contacts"] = ContactSerializer(contacts, many=True).data
        context["leads"] = LeadSerializer(leads, many=True).data
        context["opportunities"] = OpportunitySerializer(
            opportunities, many=True).data
        return Response(context, status=status.HTTP_200_OK)


class LoginView(APIView):
    @swagger_auto_schema(
        tags=["Auth"],
        operation_description="This is login api",
        manual_parameters=swagger_params.login_page_params,
    )
    def post(self, request, format=None):
        params = request.query_params if len(
            request.data) == 0 else request.data
        email = params.get("email", None)
        password = params.get("password", None)
        errors = {}
        if not email:
            errors['email'] = ['This field is required']
        if not password:
            errors['password'] = ['This field is required']
        if errors:
            return Response({'error': True, 'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email=email).first()
        if not user:
            return Response(
                {"error": True, "errors": "user not avaliable in our records"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not user.is_active:
            return Response(
                {"error": True, "errors": "Please activate account to proceed."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if user.check_password(password):
            payload = jwt_payload_handler(user)
            response_data = {
                "token": jwt_encode_handler(payload),
                "error": False,
            }
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            password_field = "doesnot match"
            msg = _("Email and password {password_field}")
            msg = msg.format(password_field=password_field)
            return Response(
                {"error": True, "errors": msg},
                status=status.HTTP_400_BAD_REQUEST,
            )


class RegistrationView(APIView):
    @swagger_auto_schema(
        tags=["Auth"],
        operation_description="This is registration api",
        manual_parameters=swagger_params.registration_page_params,
    )
    def post(self, request, format=None):
        params = request.query_params if len(
            request.data) == 0 else request.data

        form = RegisterOrganizationSerializer(data=params)
        if form.is_valid():
            org_name = params.get('org_name')
            email = params.get('email')
            first_name = params.get('first_name')
            password = params.get('password')
            user, created = User.objects.get_or_create(email=email)
            user.first_name = first_name
            user.set_password(password)
            user.save()
            org = Org.objects.create(name=org_name)
            user.set_password(password)
            user.save()
            profile = Profile.objects.create(
                user=user, org=org, date_of_joining=timezone.now()
            )
            if created:
                user.is_active = False
                user.save()
                protocol = request.scheme
                current_site = get_current_site(self.request)
                send_email_to_new_user.delay(
                    profile.id,
                    org.id,
                    domain=current_site.domain,
                    protocol=protocol,
                )
                return Response(
                    {"error": False, "message": "User created Successfully."},
                    status=status.HTTP_200_OK,
                )
            return Response(
                {"error": False,
                 "message": "Please login to check the account"},
                status=status.HTTP_200_OK,
            )
        return Response({'error': True, 'errors': form.errors},
                        status=status.HTTP_400_BAD_REQUEST)


class ProfileView(APIView):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        tags=["Profile"], manual_parameters=swagger_params.organization_params
    )
    def get(self, request, format=None):
        context = {}
        context["user_obj"] = ProfileSerializer(request.profile).data
        return Response(context, status=status.HTTP_200_OK)


class UsersListView(APIView, LimitOffsetPagination):

    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        tags=["Users"], manual_parameters=swagger_params.user_create_params
    )
    def post(self, request, format=None):
        if self.request.profile.role != "ADMIN" and not self.request.user.is_superuser:
            return Response(
                {"error": True, "errors": "Permission Denied"},
                status=status.HTTP_403_FORBIDDEN,
            )
        else:
            params = request.query_params if len(
                request.data) == 0 else request.data
            if params:
                user_serializer = CreateUserSerializer(
                    data=params, org=request.org
                )
                address_serializer = BillingAddressSerializer(data=params)
                profile_serializer = CreateProfileSerializer(data=params)
                data = {}
                if not user_serializer.is_valid():
                    data["user_errors"] = dict(user_serializer.errors)
                if not profile_serializer.is_valid():
                    data['profile_errors'] = profile_serializer.errors
                if not address_serializer.is_valid():
                    data["address_errors"] = (address_serializer.errors,)
                if data:
                    return Response(
                        {"error": True, "errors": data},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if user_serializer.is_valid():
                    address_obj = address_serializer.save()
                    user = user_serializer.save(
                        is_active=False,
                    )
                    user.username = user.first_name
                    user.save()
                    if params.get("password"):
                        user.set_password(params.get("password"))
                        user.save()
                    profile = Profile.objects.create(user=user,
                                                     date_of_joining=timezone.now(),
                                                     role=params.get(
                                                         'role'),
                                                     address=address_obj,
                                                     org=request.org,
                                                     ),

                    current_site = get_current_site(self.request)
                    protocol = request.scheme
                    send_email_to_new_user.delay(
                        profile[0].id,
                        request.org.id,
                        domain=current_site.domain,
                        protocol=protocol,
                    )
                    return Response(
                        {"error": False, "message": "User Created Successfully"},
                        status=status.HTTP_201_CREATED,
                    )

    @swagger_auto_schema(
        tags=["Users"], manual_parameters=swagger_params.user_list_params
    )
    def get(self, request, format=None):
        if self.request.profile.role != "ADMIN" and not self.request.user.is_superuser:
            return Response(
                {"error": True, "errors": "Permission Denied"},
                status=status.HTTP_403_FORBIDDEN,
            )
        else:
            queryset = Profile.objects.filter(org=request.org)
            params = (
                self.request.query_params
                if len(self.request.data) == 0
                else self.request.data
            )
            if params:
                if params.get("email"):
                    queryset = queryset.filter(
                        user__email__icontains=params.get("email"))
                if params.get("role"):
                    queryset = queryset.filter(role=params.get("role"))
                if params.get("status"):
                    queryset = queryset.filter(is_active=params.get("status"))

            context = {}
            queryset_active_users = queryset.filter(is_active=True)
            results_active_users = self.paginate_queryset(
                queryset_active_users.distinct(), self.request, view=self
            )
            active_users = ProfileSerializer(
                results_active_users, many=True).data
            context["per_page"] = 10
            context["active_users"] = {
                "active_users_count": self.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "page_number": int(self.offset / 10) + 1,
                "active_users": active_users,
            }

            queryset_inactive_users = queryset.filter(is_active=False)
            results_inactive_users = self.paginate_queryset(
                queryset_inactive_users.distinct(), self.request, view=self
            )
            inactive_users = ProfileSerializer(
                results_inactive_users, many=True).data
            context["inactive_users"] = {
                "inactive_users_count": self.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "page_number": int(self.offset / 10) + 1,
                "inactive_users": inactive_users,
            }

            context["admin_email"] = settings.ADMIN_EMAIL
            context["roles"] = ROLES
            context["status"] = [("True", "Active"), ("False", "In Active")]
            return Response(context)


class DocumentListView(APIView, LimitOffsetPagination):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    model = Document

    def get_context_data(self, **kwargs):
        params = (
            self.request.query_params
            if len(self.request.data) == 0
            else self.request.data
        )
        queryset = self.model.objects.filter(org=self.request.org)
        if self.request.user.is_superuser or self.request.profile.role == "ADMIN":
            queryset = queryset
        else:
            if self.request.profile.documents():
                doc_ids = self.request.profile.documents().values_list("id", flat=True)
                shared_ids = queryset.filter(
                    Q(status="active") & Q(
                        shared_to__id__in=[self.request.profile.id])
                ).values_list("id", flat=True)
                queryset = queryset.filter(
                    Q(id__in=doc_ids) | Q(id__in=shared_ids))
            else:
                queryset = queryset.filter(
                    Q(status="active") & Q(
                        shared_to__id__in=[self.request.profile.id])
                )

        request_post = params
        if request_post:
            if request_post.get("title"):
                queryset = queryset.filter(
                    title__icontains=request_post.get("title"))
            if request_post.get("status"):
                queryset = queryset.filter(status=request_post.get("status"))

            if request_post.get("shared_to"):
                queryset = queryset.filter(
                    shared_to__id__in=json.loads(request_post.get("shared_to"))
                )

        context = {}
        profile_list = Profile.objects.filter(
            is_active=True, org=self.request.org)
        if self.request.profile.role == "ADMIN" or self.request.profile.is_admin:
            profiles = profile_list.order_by("user__email")
        else:
            profiles = profile_list.filter(
                role="ADMIN").order_by("user__email")
        search = False
        if (
            params.get("document_file")
            or params.get("status")
            or params.get("shared_to")
        ):
            search = True
        context["search"] = search

        queryset_documents_active = queryset.filter(status="active")
        results_documents_active = self.paginate_queryset(
            queryset_documents_active.distinct(), self.request, view=self
        )
        documents_active = DocumentSerializer(
            results_documents_active, many=True).data
        context["per_page"] = 10
        context["documents_active"] = {
            "documents_active_count": self.count,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "page_number": int(self.offset / 10) + 1,
            "documents_active": documents_active,
        }

        queryset_documents_inactive = queryset.filter(status="inactive")
        results_documents_inactive = self.paginate_queryset(
            queryset_documents_inactive.distinct(), self.request, view=self
        )
        documents_inactive = DocumentSerializer(
            results_documents_inactive, many=True
        ).data

        context["documents_inactive"] = {
            "documents_inactive_count": self.count,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "page_number": int(self.offset / 10) + 1,
            "documents_inactive": documents_inactive,
        }

        context["users"] = ProfileSerializer(profiles, many=True).data
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
        params = request.query_params if len(
            request.data) == 0 else request.data
        serializer = DocumentCreateSerializer(data=params, request_obj=request)
        if serializer.is_valid():
            doc = serializer.save(
                created_by=request.profile,
                org=request.org,
                document_file=request.FILES.get("document_file"),
            )
            if params.get("shared_to"):
                assinged_to_users_ids = json.loads(params.get("shared_to"))
                for user_id in assinged_to_users_ids:
                    user = Profile.objects.filter(
                        id=user_id, org=request.org)
                    if user.exists():
                        doc.shared_to.add(user_id)
                    else:
                        doc.delete()
                        return Response(
                            {"error": True, "errors": "Enter Valid User"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
            if self.request.profile.role == "ADMIN":
                if params.get("teams"):
                    teams = json.loads(params.get("teams"))
                    for team in teams:
                        teams_ids = Teams.objects.filter(
                            id=team, org=request.org)
                        if teams_ids.exists():
                            doc.teams.add(team)
                        else:
                            doc.delete()
                            return Response(
                                {"error": True, "errors": "Enter Valid Team"},
                                status=status.HTTP_400_BAD_REQUEST,
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
        tags=["documents"], manual_parameters=swagger_params.organization_params
    )
    def get(self, request, pk, format=None):
        self.object = self.get_object(pk)
        if not self.object:
            return Response(
                {"error": True, "errors": "Document does not exist"},
                status=status.HTTP_403_FORBIDDEN,
            )
        if self.object.org != self.request.org:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN)
        if self.request.profile.role != "ADMIN" and not self.request.user.is_superuser:
            if not (
                (self.request.profile == self.object.created_by)
                or (self.request.profile in self.object.shared_to.all())
            ):
                return Response(
                    {
                        "error": True,
                        "errors": "You do not have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
        profile_list = Profile.objects.filter(org=self.request.org)
        if request.profile.role == "ADMIN" or request.user.is_superuser:
            profiles = profile_list.order_by("user__email")
        else:
            profiles = profile_list.filter(
                role="ADMIN").order_by("user__email")
        context = {}
        context.update(
            {
                "doc_obj": DocumentSerializer(self.object).data,
                "file_type_code": self.object.file_type()[1],
                "users": ProfileSerializer(profiles, many=True).data,
            }
        )
        return Response(context, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        tags=["documents"], manual_parameters=swagger_params.organization_params
    )
    def delete(self, request, pk, format=None):
        document = self.get_object(pk)
        if not document:
            return Response(
                {"error": True, "errors": "Documdnt does not exist"},
                status=status.HTTP_403_FORBIDDEN,
            )
        if document.org != self.request.org:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN
            )

        if self.request.profile.role != "ADMIN" and not self.request.user.is_superuser:
            if (
                self.request.profile != document.created_by
            ):  # or (self.request.profile not in document.shared_to.all()):
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
        params = request.query_params if len(
            request.data) == 0 else request.data
        if not self.object:
            return Response(
                {"error": True, "errors": "Document does not exist"},
                status=status.HTTP_403_FORBIDDEN,
            )
        if self.object.org != self.request.org:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN
            )
        if self.request.profile.role != "ADMIN" and not self.request.user.is_superuser:
            if not (
                (self.request.profile == self.object.created_by)
                or (self.request.profile in self.object.shared_to.all())
            ):
                return Response(
                    {
                        "error": True,
                        "errors": "You do not have Permission to perform this action",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
        serializer = DocumentCreateSerializer(
            data=params, instance=self.object, request_obj=request
        )
        if serializer.is_valid():
            doc = serializer.save(
                document_file=request.FILES.get("document_file"),
                status=params.get("status"),
                org=request.org
            )
            doc.shared_to.clear()
            if params.get("shared_to"):
                assinged_to_users_ids = json.loads(params.get("shared_to"))
                for user_id in assinged_to_users_ids:
                    user = Profile.objects.filter(
                        id=user_id, org=request.org)
                    if user.exists():
                        doc.shared_to.add(user_id)
                    else:
                        return Response(
                            {"error": True, "errors": "Enter Valid User"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

            if self.request.profile.role == "ADMIN":
                doc.teams.clear()
                if params.get("teams"):
                    teams = json.loads(params.get("teams"))
                    for team in teams:
                        teams_ids = Teams.objects.filter(
                            id=team, org=request.org)
                        if teams_ids.exists():
                            doc.teams.add(team)
                        else:
                            return Response(
                                {"error": True, "errors": "Enter Valid Team"},
                                status=status.HTTP_400_BAD_REQUEST,
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
        params = request.query_params if len(
            request.data) == 0 else request.data
        serializer = ForgotPasswordSerializer(data=params)
        if serializer.is_valid():
            user = get_object_or_404(User, email=params.get("email"))
            if not user.is_active:
                return Response(
                    {"error": True, "errors": "Please activate account to proceed."},
                    status=status.HTTP_406_NOT_ACCEPTABLE,
                )
            protocol = self.request.scheme
            send_email_to_reset_password.delay(
                user.email, protocol=protocol, domain=settings.DOMAIN_NAME
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
    def post(self, request, uid, token, format=None):
        params = request.query_params if len(
            request.data) == 0 else request.data
        try:
            uid = force_text(urlsafe_base64_decode(uid))
            user_obj = User.objects.get(pk=uid)
            if not user_obj.password:
                if not user_obj.is_active:
                    user_obj.is_active = True
                    user_obj.save()
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user_obj = None
        if user_obj is not None:
            password1 = params.get("new_password1")
            password2 = params.get("new_password2")
            if password1 != password2:
                return Response(
                    {"error": True, "errors": "The two password fields didn't match."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                user_obj.set_password(password1)
                user_obj.save()
                return Response(
                    {"error": False,
                        "message": "Password Updated Successfully. Please login"},
                    status=status.HTTP_200_OK
                )
        else:
            return Response(
                {"error": True, "errors": "Invalid Link"}
            )


class UserStatusView(APIView):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        tags=["Users"], manual_parameters=swagger_params.users_status_params
    )
    def post(self, request, pk, format=None):
        if self.request.profile.role != "ADMIN" and not self.request.user.is_superuser:
            return Response(
                {
                    "error": True,
                    "errors": "You do not have permission to perform this action",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        params = request.query_params if len(
            request.data) == 0 else request.data
        profiles = Profile.objects.filter(org=request.org)
        profile = profiles.get(id=pk)

        if params.get("status"):
            user_status = params.get("status")
            if user_status == "Active":
                profile.is_active = True
            elif user_status == "Inactive":
                profile.is_active = False
            else:
                return Response(
                    {"error": True, "errors": "Please enter Valid Status for user"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            profile.save()

        context = {}
        active_profiles = profiles.filter(is_active=True)
        inactive_profiles = profiles.filter(is_active=False)
        context["active_profiles"] = ProfileSerializer(
            active_profiles, many=True).data
        context["inactive_profiles"] = ProfileSerializer(
            inactive_profiles, many=True).data
        return Response(context)


class DomainList(APIView):
    model = APISettings
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        tags=["Settings"], manual_parameters=swagger_params.organization_params
    )
    def get(self, request, *args, **kwargs):
        api_settings = APISettings.objects.filter(org=request.org)
        users = Profile.objects.filter(
            is_active=True, org=request.org).order_by("user__email")
        return Response(
            {
                "error": False,
                "api_settings": APISettingsListSerializer(api_settings, many=True).data,
                "users": ProfileSerializer(users, many=True).data,
            },
            status=status.HTTP_200_OK,
        )

    @swagger_auto_schema(
        tags=["Settings"], manual_parameters=swagger_params.api_setting_create_params
    )
    def post(self, request, *args, **kwargs):
        params = (
            self.request.query_params
            if len(self.request.data) == 0
            else self.request.data
        )
        assign_to_list = []
        if params.get("lead_assigned_to"):
            assign_to_list = json.loads(params.get("lead_assigned_to"))
        serializer = APISettingsSerializer(data=params)
        if serializer.is_valid():
            settings_obj = serializer.save(
                created_by=request.profile, org=request.org)
            if params.get("tags"):
                tags = json.loads(params.get("tags"))
                for tag in tags:
                    tag_obj = Tags.objects.filter(name=tag).first()
                    if not tag_obj:
                        tag_obj = Tags.objects.create(name=tag)
                    settings_obj.tags.add(tag_obj)
            if assign_to_list:
                settings_obj.lead_assigned_to.add(*assign_to_list)
            return Response(
                {"error": False, "message": "API key added sucessfully"},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class DomainDetailView(APIView):
    model = APISettings
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        return self.model.objects.get(pk=pk)

    @swagger_auto_schema(
        tags=["Settings"], manual_parameters=swagger_params.organization_params
    )
    def get(self, request, pk, format=None):
        api_setting = self.get_object(pk)
        return Response(
            {"error": False, "domain": APISettingsListSerializer(
                api_setting).data},
            status=status.HTTP_200_OK,
        )

    @swagger_auto_schema(
        tags=["Settings"], manual_parameters=swagger_params.api_setting_create_params
    )
    def put(self, request, pk, **kwargs):
        api_setting = self.get_object(pk)
        params = (
            self.request.query_params
            if len(self.request.data) == 0
            else self.request.data
        )
        assign_to_list = []
        if params.get("lead_assigned_to"):
            assign_to_list = json.loads(params.get("lead_assigned_to"))
        serializer = APISettingsSerializer(data=params, instance=api_setting)
        if serializer.is_valid():
            api_setting = serializer.save()
            api_setting.tags.clear()
            api_setting.lead_assigned_to.clear()
            if params.get("tags"):
                tags = json.loads(params.get("tags"))
                for tag in tags:
                    tag_obj = Tags.objects.filter(name=tag).first()
                    if not tag_obj:
                        tag_obj = Tags.objects.create(name=tag)
                    api_setting.tags.add(tag_obj)
            if assign_to_list:
                api_setting.lead_assigned_to.add(*assign_to_list)
            return Response(
                {"error": False, "message": "API setting Updated sucessfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @swagger_auto_schema(
        tags=["Settings"], manual_parameters=swagger_params.organization_params
    )
    def delete(self, request, pk, **kwargs):
        api_setting = self.get_object(pk)
        if api_setting:
            api_setting.delete()
        return Response(
            {"error": False, "message": "API setting deleted sucessfully"},
            status=status.HTTP_200_OK,
        )


class ActivateUserView(APIView):
    @swagger_auto_schema(
        tags=["Auth"],
    )
    def post(self, request, uid, token, activation_key, format=None):
        profile = get_object_or_404(Profile, activation_key=activation_key)
        if profile.user:
            if timezone.now() > profile.key_expires:
                protocol = request.scheme
                resend_activation_link_to_user.delay(
                    profile.user.email,
                    domain=settings.DOMAIN_NAME,
                    protocol=protocol,
                )
                return Response(
                    {
                        "error": False,
                        "message": "Link expired. Please use the Activation link sent now to your mail.",
                    },
                    status=status.HTTP_406_NOT_ACCEPTABLE,
                )
            else:
                try:
                    uid = force_text(urlsafe_base64_decode(uid))
                    user = User.objects.get(pk=uid)
                except (TypeError, ValueError, OverflowError, User.DoesNotExist):
                    user = None
                if user is not None and account_activation_token.check_token(
                    user, token
                ):
                    user.is_active = True
                    user.save()
                    return Response(
                        {
                            "error": False,
                            "message": "Thank you for your email confirmation. Now you can login to your account.",
                        },
                        status=status.HTTP_200_OK,
                    )
                else:
                    return Response(
                        {"error": True, "errors": "Activation link is invalid!"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )


class ResendActivationLinkView(APIView):
    @swagger_auto_schema(
        tags=["Auth"], manual_parameters=swagger_params.forgot_password_params
    )
    def post(self, request, format=None):
        params = request.query_params if len(
            request.data) == 0 else request.data
        user = get_object_or_404(User, email=params.get("email"))
        if user.is_active:
            return Response(
                {"error": False, "message": "Account is active. Please login"},
                status=status.HTTP_200_OK,
            )
        protocol = request.scheme
        resend_activation_link_to_user.delay(
            user.email,
            domain=settings.DOMAIN_NAME,
            protocol=protocol,
        )
        data = {
            "error": False,
            "message": "Please use the Activation link sent to your mail to activate account.",
        }
        return Response(data, status=status.HTTP_200_OK)


class OrganizationListView(APIView, LimitOffsetPagination):

    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        tags=["Auth"]
    )
    def get(self, request):
        profiles = Profile.objects.filter(user=request.user, is_active=True)
        companies = Org.objects.filter(
            id__in=profiles.values_list('org', flat=True))
        return Response({'error': False,
                         'companies': OrganizationSerializer(
                             companies, many=True).data},
                        status=status.HTTP_200_OK)


# class UsersDelete(APIView):

#     authentication_classes = (JSONWebTokenAuthentication,)
#     permission_classes = (IsAuthenticated,)

#     @swagger_auto_schema(
#         tags=["Users"], manual_parameters=swagger_params.users_delete_params,
#         operation_description="To delete multiple users",
#     )
#     def post(self, request, *args, **kwargs):
#         if self.request.user.role == "ADMIN" or self.request.user.is_superuser:
#             params = request.query_params if len(request.data) == 0 else request.data
#             users_list = json.loads(params.get("users_list"))
#             users = User.objects.filter(
#                 id__in = users_list
#             )
#             users.delete()
#             return Response(
#                 {
#                     "error": False,
#                     "message": "Users deleted successfully",
#                 },
#                 status=status.HTTP_200_OK,
#             )
#         else:
#             return Response(
#                 {"error": True, "errors": "Permission Denied"},
#                 status=status.HTTP_403_FORBIDDEN,
#             )
