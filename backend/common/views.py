import json
import secrets
from multiprocessing import context
from re import template

import requests
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.db.models import Q
from django.http.response import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import gettext as _
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (OpenApiExample, OpenApiParameter,
                                   extend_schema)
#from common.external_auth import CustomDualAuthentication
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.utils import json
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import Account
from accounts.serializer import AccountSerializer
from cases.models import Case
from cases.serializer import CaseSerializer
##from common.custom_auth import JSONWebTokenAuthentication
from common import serializer, swagger_params
from common.models import (Activity, APISettings, Document, Org, Profile, Tags,
                           Teams, User)
from common.serializer import *
from common.serializer import OrgAwareRefreshToken
# from common.serializer import (
#     CreateUserSerializer,
#     PasswordChangeSerializer,
#     RegisterOrganizationSerializer,
# )
from common.tasks import (remove_users, resend_activation_link_to_user,
                          send_email_to_new_user, send_email_to_reset_password,
                          send_email_user_delete, update_team_users)
from common.token_generator import account_activation_token
# from rest_framework_jwt.serializers import jwt_encode_handler
from common.utils import COUNTRIES, ROLES, jwt_payload_handler
from contacts.models import Contact
from contacts.serializer import ContactSerializer
from leads.models import Lead
from leads.serializer import LeadSerializer
from opportunity.models import Opportunity
from opportunity.serializer import OpportunitySerializer


class GetTeamsAndUsersView(APIView):

    permission_classes = (IsAuthenticated,)

    @extend_schema(tags=["users"], parameters=swagger_params.organization_params)
    def get(self, request, *args, **kwargs):
        data = {}
        teams = Teams.objects.filter(org=request.profile.org).order_by("-id")
        teams_data = TeamsSerializer(teams, many=True).data
        profiles = Profile.objects.filter(is_active=True, org=request.profile.org).order_by(
            "user__email"
        )
        profiles_data = ProfileSerializer(profiles, many=True).data
        data["teams"] = teams_data
        data["profiles"] = profiles_data
        return Response(data)


class UsersListView(APIView, LimitOffsetPagination):

    permission_classes = (IsAuthenticated,)
    @extend_schema(parameters=swagger_params.organization_params,request=UserCreateSwaggerSerializer)
    def post(self, request, format=None):
        print(request.profile.role, request.user.is_superuser)
        if self.request.profile.role != "ADMIN" and not self.request.user.is_superuser:
            return Response(
                {"error": True, "errors": "Permission Denied"},
                status=status.HTTP_403_FORBIDDEN,
            )
        else:
            params = request.data
            if params:
                user_serializer = CreateUserSerializer(data=params, org=request.profile.org)
                address_serializer = BillingAddressSerializer(data=params)
                profile_serializer = CreateProfileSerializer(data=params)
                data = {}
                if not user_serializer.is_valid():
                    data["user_errors"] = dict(user_serializer.errors)
                if not profile_serializer.is_valid():
                    data["profile_errors"] = profile_serializer.errors
                if not address_serializer.is_valid():
                    data["address_errors"] = (address_serializer.errors,)
                if data:
                    return Response(
                        {"error": True, "errors": data},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if address_serializer.is_valid():
                    address_obj = address_serializer.save()
                    user = user_serializer.save(
                        is_active=True,
                    )
                    user.email = user.email
                    user.save()
                    # if params.get("password"):
                    #     user.set_password(params.get("password"))
                    #     user.save()
                    profile = Profile.objects.create(
                        user=user,
                        date_of_joining=timezone.now(),
                        role=params.get("role"),
                        address=address_obj,
                        org=request.profile.org,
                    )

                    # send_email_to_new_user.delay(
                    #     profile.id,
                    #     request.profile.org.id,
                    # )
                    return Response(
                        {"error": False, "message": "User Created Successfully"},
                        status=status.HTTP_201_CREATED,
                    )


    @extend_schema(parameters=swagger_params.user_list_params)
    def get(self, request, format=None):
        # Check if profile exists and user has permission
        if not self.request.profile:
            return Response(
                {"error": True, "errors": "Organization context required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if self.request.profile.role != "ADMIN" and not self.request.user.is_superuser:
            return Response(
                {"error": True, "errors": "Permission Denied"},
                status=status.HTTP_403_FORBIDDEN,
            )
        queryset = Profile.objects.filter(org=request.profile.org).order_by("-id")
        params = request.query_params
        if params:
            if params.get("email"):
                queryset = queryset.filter(user__email__icontains=params.get("email"))
            if params.get("role"):
                queryset = queryset.filter(role=params.get("role"))
            if params.get("status"):
                queryset = queryset.filter(is_active=params.get("status"))

        context = {}
        queryset_active_users = queryset.filter(is_active=True)
        results_active_users = self.paginate_queryset(
            queryset_active_users.distinct(), self.request, view=self
        )
        active_users = ProfileSerializer(results_active_users, many=True).data
        if results_active_users:
            offset = queryset_active_users.filter(
                id__gte=results_active_users[-1].id
            ).count()
            if offset == queryset_active_users.count():
                offset = None
        else:
            offset = 0
        context["active_users"] = {
            "active_users_count": self.count,
            "active_users": active_users,
            "offset": offset,
        }

        queryset_inactive_users = queryset.filter(is_active=False)
        results_inactive_users = self.paginate_queryset(
            queryset_inactive_users.distinct(), self.request, view=self
        )
        inactive_users = ProfileSerializer(results_inactive_users, many=True).data
        if results_inactive_users:
            offset = queryset_inactive_users.filter(
                id__gte=results_inactive_users[-1].id
            ).count()
            if offset == queryset_inactive_users.count():
                offset = None
        else:
            offset = 0
        context["inactive_users"] = {
            "inactive_users_count": self.count,
            "inactive_users": inactive_users,
            "offset": offset,
        }

        context["admin_email"] = settings.ADMIN_EMAIL
        context["roles"] = ROLES
        context["status"] = [("True", "Active"), ("False", "In Active")]
        return Response(context)


class UserDetailView(APIView):
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        profile = get_object_or_404(Profile, pk=pk)
        return profile

    @extend_schema(tags=["users"], parameters=swagger_params.organization_params)
    def get(self, request, pk, format=None):
        profile_obj = self.get_object(pk)
        if (
            self.request.profile.role != "ADMIN"
            and not self.request.profile.is_admin
            and self.request.profile.id != profile_obj.id
        ):
            return Response(
                {"error": True, "errors": "Permission Denied"},
                status=status.HTTP_403_FORBIDDEN,
            )
        if profile_obj.org != request.profile.org:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN,
            )
        assigned_data = Profile.objects.filter(org=request.profile.org, is_active=True).values(
            "id", "user__email"
        )
        context = {}
        context["profile_obj"] = ProfileSerializer(profile_obj).data
        opportunity_list = Opportunity.objects.filter(assigned_to=profile_obj)
        context["opportunity_list"] = OpportunitySerializer(
            opportunity_list, many=True
        ).data
        contacts = Contact.objects.filter(assigned_to=profile_obj)
        context["contacts"] = ContactSerializer(contacts, many=True).data
        cases = Case.objects.filter(assigned_to=profile_obj)
        context["cases"] = CaseSerializer(cases, many=True).data
        context["assigned_data"] = assigned_data
        comments = profile_obj.user_comments.all()
        context["comments"] = CommentSerializer(comments, many=True).data
        context["countries"] = COUNTRIES
        return Response(
            {"error": False, "data": context},
            status=status.HTTP_200_OK,
        )

    @extend_schema(tags=["users"],parameters=swagger_params.organization_params, request=UserCreateSwaggerSerializer)
    def put(self, request, pk, format=None):
        params = request.data
        profile = self.get_object(pk)
        address_obj = profile.address
        if (
            self.request.profile.role != "ADMIN"
            and not self.request.user.is_superuser
            and self.request.profile.id != profile.id
        ):
            return Response(
                {"error": True, "errors": "Permission Denied"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if profile.org != request.profile.org:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = CreateUserSerializer(
            data=params, instance=profile.user, org=request.profile.org
        )
        address_serializer = BillingAddressSerializer(data=params, instance=address_obj)
        profile_serializer = CreateProfileSerializer(data=params, instance=profile)
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
        if address_serializer.is_valid():
            address_obj = address_serializer.save()
            user = serializer.save()
            user.email = user.email
            user.save()
        if profile_serializer.is_valid():
            profile = profile_serializer.save()
            return Response(
                {"error": False, "message": "User Updated Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @extend_schema(
        tags=["users"],parameters=swagger_params.organization_params
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
        )
        self.object.delete()
        return Response({"status": "success"}, status=status.HTTP_200_OK)


# check_header not working
class ApiHomeView(APIView):

    permission_classes = (IsAuthenticated,)

    @extend_schema(parameters=swagger_params.organization_params)
    def get(self, request, format=None):
        accounts = Account.objects.filter(is_active=True, org=request.profile.org)
        contacts = Contact.objects.filter(org=request.profile.org)
        leads = Lead.objects.filter(org=request.profile.org).exclude(
            Q(status="converted") | Q(status="closed")
        )
        opportunities = Opportunity.objects.filter(org=request.profile.org)

        if self.request.profile.role != "ADMIN" and not self.request.user.is_superuser:
            accounts = accounts.filter(
                Q(assigned_to=self.request.profile) | Q(created_by=self.request.profile.user)
            )
            contacts = contacts.filter(
                Q(assigned_to__id__in=self.request.profile)
                | Q(created_by=self.request.profile.user)
            )
            leads = leads.filter(
                Q(assigned_to__id__in=self.request.profile)
                | Q(created_by=self.request.profile.user)
            ).exclude(status="closed")
            opportunities = opportunities.filter(
                Q(assigned_to__id__in=self.request.profile)
                | Q(created_by=self.request.profile.user)
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


class OrgProfileCreateView(APIView):
    #authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated,)

    model1 = Org
    model2 = Profile
    serializer_class = OrgProfileCreateSerializer
    profile_serializer = CreateProfileSerializer

    @extend_schema(
        description="Organization and profile Creation api",
        request=OrgProfileCreateSerializer
    )
    def post(self, request, format=None):
        data = request.data
        data['api_key'] = secrets.token_hex(16)
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            org_obj = serializer.save()

            # now creating the profile
            profile_obj = self.model2.objects.create(user=request.user, org=org_obj)
            # now the current user is the admin of the newly created organisation
            profile_obj.is_organization_admin = True
            profile_obj.role = 'ADMIN'
            profile_obj.save()

            return Response(
                {
                    "error": False,
                    "message": "New Org is Created.",
                    "org": self.serializer_class(org_obj).data,
                    "status": status.HTTP_201_CREATED,
                }
            )
        else:
            return Response(
                {
                    "error": True,
                    "errors": serializer.errors,
                    "status": status.HTTP_400_BAD_REQUEST,
                }
            )

    @extend_schema(
        description="Just Pass the token, will return ORG list, associated with user"
    )
    def get(self, request, format=None):
        """
        here we are passing profile list of the user, where org details also included
        """
        profile_list = Profile.objects.filter(user=request.user)
        serializer = ShowOrganizationListSerializer(profile_list, many=True)
        return Response(
            {
                "error": False,
                "status": status.HTTP_200_OK,
                "profile_org_list": serializer.data,
            }
        )


class OrgUpdateView(APIView):
    """
    Update organization details
    Only organization admins can update
    """
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        description="Update organization details",
        request=OrganizationSerializer,
        responses={200: OrganizationSerializer}
    )
    def put(self, request, pk, format=None):
        # Check if user has admin access to this organization
        if not request.profile:
            return Response(
                {"error": True, "errors": "Organization context required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify the organization matches the current context
        if str(request.profile.org.id) != str(pk):
            return Response(
                {"error": True, "errors": "Cannot update a different organization"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if user is admin
        if request.profile.role != "ADMIN" and not request.profile.is_organization_admin:
            return Response(
                {"error": True, "errors": "Only organization admins can update organization details"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            org = Org.objects.get(id=pk)
        except Org.DoesNotExist:
            return Response(
                {"error": True, "errors": "Organization not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Update fields
        data = request.data
        if "name" in data:
            org.name = data["name"]

        org.save()

        return Response(
            {
                "error": False,
                "message": "Organization updated successfully",
                "org": OrganizationSerializer(org).data
            },
            status=status.HTTP_200_OK
        )

    @extend_schema(
        description="Get organization details",
        responses={200: OrganizationSerializer}
    )
    def get(self, request, pk, format=None):
        # Check if user has access to this organization
        if not request.profile:
            return Response(
                {"error": True, "errors": "Organization context required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify the organization matches the current context
        if str(request.profile.org.id) != str(pk):
            return Response(
                {"error": True, "errors": "Cannot access a different organization"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            org = Org.objects.get(id=pk)
        except Org.DoesNotExist:
            return Response(
                {"error": True, "errors": "Organization not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            {
                "error": False,
                "org": OrganizationSerializer(org).data
            },
            status=status.HTTP_200_OK
        )


class ProfileView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(parameters=swagger_params.organization_params)
    def get(self, request, format=None):
        # profile=Profile.objects.get(user=request.user)
        context = {}
        context["user_obj"] = ProfileSerializer(self.request.profile).data
        return Response(context, status=status.HTTP_200_OK)

    @extend_schema(parameters=swagger_params.organization_params)
    def patch(self, request, format=None):
        profile = request.profile
        data = request.data

        # Update phone on Profile if provided
        if "phone" in data:
            profile.phone = data.get("phone")
            profile.save()

        # Note: name field is not available on User model
        # If name updates are needed, the User model would need to be extended

        return Response(
            {"message": "Profile updated successfully", "user_obj": ProfileSerializer(profile).data},
            status=status.HTTP_200_OK
        )

class DocumentListView(APIView, LimitOffsetPagination):
    #authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated,)
    model = Document

    def get_context_data(self, **kwargs):
        params = self.request.query_params
        queryset = self.model.objects.filter(org=self.request.profile.org).order_by("-id")
        if self.request.user.is_superuser or self.request.profile.role == "ADMIN":
            queryset = queryset
        else:
            if self.request.profile.documents():
                doc_ids = self.request.profile.documents().values_list("id", flat=True)
                shared_ids = queryset.filter(
                    Q(status="active") & Q(shared_to__id__in=[self.request.profile.id])
                ).values_list("id", flat=True)
                queryset = queryset.filter(Q(id__in=doc_ids) | Q(id__in=shared_ids))
            else:
                queryset = queryset.filter(
                    Q(status="active") & Q(shared_to__id__in=[self.request.profile.id])
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
        profile_list = Profile.objects.filter(is_active=True, org=self.request.profile.org)
        if self.request.profile.role == "ADMIN" or self.request.profile.is_admin:
            profiles = profile_list.order_by("user__email")
        else:
            profiles = profile_list.filter(role="ADMIN").order_by("user__email")
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
        documents_active = DocumentSerializer(results_documents_active, many=True).data
        if results_documents_active:
            offset = queryset_documents_active.filter(
                id__gte=results_documents_active[-1].id
            ).count()
            if offset == queryset_documents_active.count():
                offset = None
        else:
            offset = 0
        context["documents_active"] = {
            "documents_active_count": self.count,
            "documents_active": documents_active,
            "offset": offset,
        }

        queryset_documents_inactive = queryset.filter(status="inactive")
        results_documents_inactive = self.paginate_queryset(
            queryset_documents_inactive.distinct(), self.request, view=self
        )
        documents_inactive = DocumentSerializer(
            results_documents_inactive, many=True
        ).data
        if results_documents_inactive:
            offset = queryset_documents_inactive.filter(
                id__gte=results_documents_active[-1].id
            ).count()
            if offset == queryset_documents_inactive.count():
                offset = None
        else:
            offset = 0
        context["documents_inactive"] = {
            "documents_inactive_count": self.count,
            "documents_inactive": documents_inactive,
            "offset": offset,
        }

        context["users"] = ProfileSerializer(profiles, many=True).data
        context["status_choices"] = Document.DOCUMENT_STATUS_CHOICE
        return context

    @extend_schema(
        tags=["documents"], parameters=swagger_params.document_get_params
    )
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return Response(context)

    @extend_schema(
        tags=["documents"], parameters=swagger_params.organization_params,request=DocumentCreateSwaggerSerializer
    )
    def post(self, request, *args, **kwargs):
        params = request.data
        serializer = DocumentCreateSerializer(data=params, request_obj=request)
        if serializer.is_valid():
            doc = serializer.save(
                created_by=request.profile.user,
                org=request.profile.org,
                document_file=request.FILES.get("document_file"),
            )
            if params.get("shared_to"):
                assinged_to_list = params.get("shared_to")
                profiles = Profile.objects.filter(
                    id__in=assinged_to_list, org=request.profile.org, is_active=True
                )
                if profiles:
                    doc.shared_to.add(*profiles)
            if params.get("teams"):
                teams_list = params.get("teams")
                teams = Teams.objects.filter(id__in=teams_list, org=request.profile.org)
                if teams:
                    doc.teams.add(*teams)

            return Response(
                {"error": False, "message": "Document Created Successfully"},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class DocumentDetailView(APIView):
    #authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        return Document.objects.filter(id=pk).first()

    @extend_schema(
        tags=["documents"], parameters=swagger_params.organization_params
    )
    def get(self, request, pk, format=None):
        self.object = self.get_object(pk)
        if not self.object:
            return Response(
                {"error": True, "errors": "Document does not exist"},
                status=status.HTTP_403_FORBIDDEN,
            )
        if self.object.org != self.request.profile.org:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN,
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
        profile_list = Profile.objects.filter(org=self.request.profile.org)
        if request.profile.role == "ADMIN" or request.user.is_superuser:
            profiles = profile_list.order_by("user__email")
        else:
            profiles = profile_list.filter(role="ADMIN").order_by("user__email")
        context = {}
        context.update(
            {
                "doc_obj": DocumentSerializer(self.object).data,
                "file_type_code": self.object.file_type()[1],
                "users": ProfileSerializer(profiles, many=True).data,
            }
        )
        return Response(context, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["documents"], parameters=swagger_params.organization_params
    )
    def delete(self, request, pk, format=None):
        document = self.get_object(pk)
        if not document:
            return Response(
                {"error": True, "errors": "Documdnt does not exist"},
                status=status.HTTP_403_FORBIDDEN,
            )
        if document.org != self.request.profile.org:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN,
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

    
    @extend_schema(
        tags=["documents"], parameters=swagger_params.organization_params,request=DocumentEditSwaggerSerializer
    )
    def put(self, request, pk, format=None):
        self.object = self.get_object(pk)
        params = request.data
        if not self.object:
            return Response(
                {"error": True, "errors": "Document does not exist"},
                status=status.HTTP_403_FORBIDDEN,
            )
        if self.object.org != self.request.profile.org:
            return Response(
                {"error": True, "errors": "User company doesnot match with header...."},
                status=status.HTTP_403_FORBIDDEN,
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
                org=request.profile.org,
            )
            doc.shared_to.clear()
            if params.get("shared_to"):
                assinged_to_list = params.get("shared_to")
                profiles = Profile.objects.filter(
                    id__in=assinged_to_list, org=request.profile.org, is_active=True
                )
                if profiles:
                    doc.shared_to.add(*profiles)

            doc.teams.clear()
            if params.get("teams"):
                teams_list = params.get("teams")
                teams = Teams.objects.filter(id__in=teams_list, org=request.profile.org)
                if teams:
                    doc.teams.add(*teams)
            return Response(
                {"error": False, "message": "Document Updated Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class UserStatusView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        description="User Status View",parameters=swagger_params.organization_params, request=UserUpdateStatusSwaggerSerializer
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
        params = request.data
        profiles = Profile.objects.filter(org=request.profile.org)
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
        context["active_profiles"] = ProfileSerializer(active_profiles, many=True).data
        context["inactive_profiles"] = ProfileSerializer(
            inactive_profiles, many=True
        ).data
        return Response(context)


class DomainList(APIView):
    model = APISettings
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["Settings"],parameters=swagger_params.organization_params
    )
    def get(self, request, *args, **kwargs):
        api_settings = APISettings.objects.filter(org=request.profile.org)
        users = Profile.objects.filter(is_active=True, org=request.profile.org).order_by(
            "user__email"
        )
        return Response(
            {
                "error": False,
                "api_settings": APISettingsListSerializer(api_settings, many=True).data,
                "users": ProfileSerializer(users, many=True).data,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["Settings"],parameters=swagger_params.organization_params, request=APISettingsSwaggerSerializer
    )
    def post(self, request, *args, **kwargs):
        params = request.data
        assign_to_list = []
        if params.get("lead_assigned_to"):
            assign_to_list = params.get("lead_assigned_to")
        serializer = APISettingsSerializer(data=params)
        if serializer.is_valid():
            settings_obj = serializer.save(created_by=request.profile.user, org=request.profile.org)
            if params.get("tags"):
                tags = params.get("tags")
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
    #authentication_classes = (CustomDualAuthentication,)
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["Settings"],parameters=swagger_params.organization_params
    )
    def get(self, request, pk, format=None):
        api_setting = self.get_object(pk)
        return Response(
            {"error": False, "domain": APISettingsListSerializer(api_setting).data},
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["Settings"],parameters=swagger_params.organization_params, request=APISettingsSwaggerSerializer
    )
    def put(self, request, pk, **kwargs):
        api_setting = self.get_object(pk)
        params = request.data
        assign_to_list = []
        if params.get("lead_assigned_to"):
            assign_to_list = params.get("lead_assigned_to")
        serializer = APISettingsSerializer(data=params, instance=api_setting)
        if serializer.is_valid():
            api_setting = serializer.save()
            api_setting.tags.clear()
            api_setting.lead_assigned_to.clear()
            if params.get("tags"):
                tags = params.get("tags")
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

    @extend_schema(
        tags=["Settings"],parameters=swagger_params.organization_params
    )
    def delete(self, request, pk, **kwargs):
        api_setting = self.get_object(pk)
        if api_setting:
            api_setting.delete()
        return Response(
            {"error": False, "message": "API setting deleted sucessfully"},
            status=status.HTTP_200_OK,
        )

class GoogleLoginView(APIView):
    """
    Check for authentication with google
    post:
        Returns token of logged In user
    """


    @extend_schema(
        description="Login through Google",  request=SocialLoginSerializer,
    )
    def post(self, request):
        from django.utils import timezone

        payload = {'access_token': request.data.get("token")}  # validate the token
        r = requests.get('https://www.googleapis.com/oauth2/v2/userinfo', params=payload)
        data = json.loads(r.text)
        print(data)
        if 'error' in data:
            content = {'message': 'wrong google token / this google token is already expired.'}
            return Response(content)
        # create user if not exist
        try:
            user = User.objects.get(email=data['email'])
        except User.DoesNotExist:
            user = User()
            user.email = data['email']
            user.profile_pic = data['picture']
            # provider random default password
            user.password = make_password(secrets.token_urlsafe(16))
            user.save()

        # Update last_login timestamp
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])

        token = RefreshToken.for_user(user)  # generate token without username & password
        response = {}
        response['username'] = user.email
        response['access_token'] = str(token.access_token)
        response['refresh_token'] = str(token)
        response['user_id'] = user.id
        return Response(response)


# JWT Authentication Views for SvelteKit Integration

class LoginView(APIView):
    """
    Login with email and password, returns JWT tokens
    """
    permission_classes = []
    authentication_classes = []

    @extend_schema(
        description="Login with email and password",
        request=serializer.LoginSerializer,
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'access_token': {'type': 'string'},
                    'refresh_token': {'type': 'string'},
                    'user': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'string'},
                            'email': {'type': 'string'},
                            'organizations': {'type': 'array'}
                        }
                    }
                }
            }
        }
    )
    def post(self, request):
        from django.utils import timezone

        from common.audit_log import audit_log

        serializer_obj = serializer.LoginSerializer(data=request.data)
        if serializer_obj.is_valid():
            user = serializer_obj.validated_data['user']

            # Update last_login timestamp
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])

            # Get user's organizations
            profiles = Profile.objects.filter(user=user, is_active=True)

            # Get the default org (first org or from request)
            org_id = request.data.get('org_id')
            default_org = None

            if org_id:
                # Use specified org if user has access
                try:
                    profile = profiles.get(org_id=org_id)
                    default_org = profile.org
                except Profile.DoesNotExist:
                    audit_log.login_failure(
                        user.email,
                        f"No access to org {org_id}",
                        request
                    )
                    return Response(
                        {'error': 'User does not have access to specified organization'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            elif profiles.exists():
                # Use first available org
                default_org = profiles.first().org

            # Generate JWT tokens with org context
            if default_org:
                token = OrgAwareRefreshToken.for_user_and_org(user, default_org)
            else:
                # User has no orgs - generate token without org context
                token = RefreshToken.for_user(user)

            # Audit log successful login
            audit_log.login_success(user, default_org, request)

            # Get user details with organizations
            user_serializer = serializer.UserDetailSerializer(user)

            response_data = {
                'access_token': str(token.access_token),
                'refresh_token': str(token),
                'user': user_serializer.data
            }

            # Include current org info if available
            if default_org:
                response_data['current_org'] = {
                    'id': str(default_org.id),
                    'name': default_org.name
                }

            return Response(response_data, status=status.HTTP_200_OK)

        # Log failed login
        email = request.data.get('email', 'unknown')
        audit_log.login_failure(email, str(serializer_obj.errors), request)
        return Response(serializer_obj.errors, status=status.HTTP_400_BAD_REQUEST)


class RegisterView(APIView):
    """
    Register a new user account
    """
    permission_classes = []
    authentication_classes = []

    @extend_schema(
        description="Register a new user account",
        request=serializer.RegisterSerializer,
        responses={
            201: {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'user_id': {'type': 'string'},
                    'email': {'type': 'string'}
                }
            }
        }
    )
    def post(self, request):
        serializer_obj = serializer.RegisterSerializer(data=request.data)
        if serializer_obj.is_valid():
            user = serializer_obj.save()

            # TODO: Send activation email
            # send_email_to_new_user.delay(user.email, user.id)

            return Response({
                'message': 'User registered successfully. Please check your email for activation link.',
                'user_id': str(user.id),
                'email': user.email
            }, status=status.HTTP_201_CREATED)

        return Response(serializer_obj.errors, status=status.HTTP_400_BAD_REQUEST)


class MeView(APIView):
    """
    Get current authenticated user details
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        description="Get current authenticated user with organizations",
        responses={200: serializer.UserDetailSerializer}
    )
    def get(self, request):
        user_serializer = serializer.UserDetailSerializer(request.user)
        return Response(user_serializer.data, status=status.HTTP_200_OK)


class OrgAwareTokenRefreshView(APIView):
    """
    Custom token refresh that validates org membership.

    When refreshing a token, this view:
    1. Validates the refresh token
    2. Checks that user still has access to the org in the token
    3. Issues new tokens with the same org context

    If membership was revoked, returns 403 and user must login again.
    """
    permission_classes = []
    authentication_classes = []

    @extend_schema(
        description="Refresh access token with org membership validation",
        request={
            'type': 'object',
            'properties': {
                'refresh': {'type': 'string', 'description': 'Refresh token'}
            },
            'required': ['refresh']
        },
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'access': {'type': 'string'},
                    'refresh': {'type': 'string'}
                }
            }
        }
    )
    def post(self, request):
        from rest_framework_simplejwt.exceptions import TokenError
        from rest_framework_simplejwt.tokens import \
            RefreshToken as BaseRefreshToken

        from common.audit_log import audit_log

        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response(
                {'error': 'Refresh token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Decode and validate refresh token
            token = BaseRefreshToken(refresh_token)
            user_id = token['user_id']
            org_id = token.get('org_id')

            # Get user
            user = User.objects.get(id=user_id)

            if not user.is_active:
                return Response(
                    {'error': 'User account is disabled'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # If token has org context, validate membership
            if org_id:
                try:
                    profile = Profile.objects.get(
                        user=user,
                        org_id=org_id,
                        is_active=True
                    )
                    org = profile.org
                except Profile.DoesNotExist:
                    # Membership revoked - user must login again
                    audit_log.token_revoked(
                        user, None,
                        f"Membership revoked for org {org_id}",
                        request
                    )
                    return Response(
                        {'error': 'Organization membership revoked. Please login again.'},
                        status=status.HTTP_403_FORBIDDEN
                    )

                # Generate new tokens with same org context
                new_token = OrgAwareRefreshToken.for_user_and_org(user, org)
                audit_log.token_refresh(user, org, request)
            else:
                # No org context - standard refresh
                new_token = BaseRefreshToken.for_user(user)
                audit_log.token_refresh(user, None, request)

            return Response({
                'access': str(new_token.access_token),
                'refresh': str(new_token)
            }, status=status.HTTP_200_OK)

        except TokenError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_401_UNAUTHORIZED
            )


class OrgSwitchView(APIView):
    """
    Switch to a different organization and get new JWT tokens.

    This endpoint validates that the user has access to the target
    organization and issues new tokens with the org_id claim.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        description="Switch to a different organization and get new JWT tokens",
        request={
            'type': 'object',
            'properties': {
                'org_id': {
                    'type': 'string',
                    'format': 'uuid',
                    'description': 'Target organization ID'
                }
            },
            'required': ['org_id']
        },
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'access_token': {'type': 'string'},
                    'refresh_token': {'type': 'string'},
                    'current_org': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'string'},
                            'name': {'type': 'string'}
                        }
                    }
                }
            }
        }
    )
    def post(self, request):
        from common.audit_log import audit_log

        org_id = request.data.get('org_id')

        if not org_id:
            return Response(
                {'error': 'org_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get current org for audit logging
        from_org = getattr(request, 'org', None)

        # Validate user has access to the target org
        try:
            profile = Profile.objects.get(
                user=request.user,
                org_id=org_id,
                is_active=True
            )
        except Profile.DoesNotExist:
            audit_log.permission_denied(
                request.user,
                from_org,
                'ORG_SWITCH',
                f'org:{org_id}',
                request
            )
            return Response(
                {'error': 'User does not have access to this organization'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Generate new tokens with the target org
        token = OrgAwareRefreshToken.for_user_and_org(request.user, profile.org)

        # Audit log the org switch
        audit_log.org_switch(request.user, from_org, profile.org, request)

        return Response({
            'access_token': str(token.access_token),
            'refresh_token': str(token),
            'current_org': {
                'id': str(profile.org.id),
                'name': profile.org.name
            },
            'profile': {
                'id': str(profile.id),
                'role': profile.role,
                'is_organization_admin': profile.is_organization_admin
            }
        }, status=status.HTTP_200_OK)


class ProfileDetailView(APIView):
    """
    Get profile details for a specific organization
    Requires org header
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        description="Get profile for current user in specified organization",
        parameters=[
            {
                'name': 'org',
                'in': 'header',
                'required': True,
                'schema': {'type': 'string', 'format': 'uuid'},
                'description': 'Organization ID'
            }
        ],
        responses={200: serializer.ProfileDetailSerializer}
    )
    def get(self, request):
        # request.profile is set by middleware based on org header
        if not hasattr(request, 'profile') or request.profile is None:
            return Response(
                {'error': 'Organization header required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        profile_serializer = serializer.ProfileDetailSerializer(request.profile)
        return Response(profile_serializer.data, status=status.HTTP_200_OK)


# Activity Views for Dashboard Recent Activities

class ActivityListView(APIView):
    """
    Get recent activities for the organization
    Returns the last 10 activities by default
    """
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["activities"],
        parameters=swagger_params.organization_params + [
            OpenApiParameter(
                name='limit',
                type=int,
                location=OpenApiParameter.QUERY,
                description='Number of activities to return (default: 10, max: 50)'
            ),
            OpenApiParameter(
                name='entity_type',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Filter by entity type (Account, Lead, Contact, etc.)'
            ),
        ],
        responses={200: serializer.ActivitySerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        if not request.profile:
            return Response(
                {"error": True, "errors": "Organization context required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get query params
        limit = min(int(request.query_params.get('limit', 10)), 50)
        entity_type = request.query_params.get('entity_type', None)

        # Query activities for this organization
        queryset = Activity.objects.filter(org=request.profile.org)

        # Filter by entity type if specified
        if entity_type:
            queryset = queryset.filter(entity_type=entity_type)

        # Get most recent activities
        activities = queryset.select_related('user', 'user__user')[:limit]

        # Serialize
        activities_data = serializer.ActivitySerializer(activities, many=True).data

        return Response({
            "error": False,
            "count": len(activities_data),
            "activities": activities_data
        }, status=status.HTTP_200_OK)


# =============================================================================
# Teams Views (merged from teams app)
# =============================================================================

class TeamsListView(APIView, LimitOffsetPagination):
    model = Teams
    permission_classes = (IsAuthenticated,)

    def get_context_data(self, **kwargs):
        params = self.request.query_params
        queryset = self.model.objects.filter(org=self.request.profile.org).order_by("-id")
        if params:
            if params.get("team_name"):
                queryset = queryset.filter(name__icontains=params.get("team_name"))
            if params.get("created_by"):
                queryset = queryset.filter(created_by=params.get("created_by"))
            if params.get("assigned_users"):
                queryset = queryset.filter(
                    users__id__in=params.get("assigned_users")
                )

        context = {}
        results_teams = self.paginate_queryset(
            queryset.distinct(), self.request, view=self
        )
        teams = TeamsSerializer(results_teams, many=True).data
        if results_teams:
            offset = queryset.filter(id__gte=results_teams[-1].id).count()
            if offset == queryset.count():
                offset = None
        else:
            offset = 0
        context["per_page"] = 10
        page_number = (int(self.offset / 10) + 1,)
        context["page_number"] = page_number
        context.update({"teams_count": self.count, "offset": offset})
        context["teams"] = teams
        return context

    @extend_schema(
        tags=["Teams"], parameters=swagger_params.teams_list_get_params
    )
    def get(self, *args, **kwargs):
        if self.request.profile.role != "ADMIN" and not self.request.profile.is_admin:
            return Response(
                {
                    "error": True,
                    "errors": "You don't have permission to perform this action.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        context = self.get_context_data(**kwargs)
        return Response(context)

    @extend_schema(
        tags=["Teams"], request=TeamswaggerCreateSerializer, parameters=swagger_params.organization_params
    )
    def post(self, request, *args, **kwargs):
        if self.request.profile.role != "ADMIN" and not self.request.profile.is_admin:
            return Response(
                {
                    "error": True,
                    "errors": "You don't have permission to perform this action.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        params = self.request.data
        serializer = TeamCreateSerializer(data=params, request_obj=request)
        if serializer.is_valid():
            team_obj = serializer.save(org=request.profile.org)

            if params.get("assign_users"):
                assinged_to_list = params.get("users")
                profiles = Profile.objects.filter(
                    id__in=assinged_to_list, org=request.profile.org
                )
                if profiles:
                    team_obj.users.add(*profiles)
            return Response(
                {"error": False, "message": "Team Created Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class TeamsDetailView(APIView):
    model = Teams
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        return self.model.objects.get(pk=pk, org=self.request.profile.org)

    @extend_schema(
        tags=["Teams"], parameters=swagger_params.organization_params
    )
    def get(self, request, pk, **kwargs):
        if self.request.profile.role != "ADMIN" and not self.request.profile.is_admin:
            return Response(
                {
                    "error": True,
                    "errors": "You don't have permission to perform this action.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        self.team_obj = self.get_object(pk)
        context = {}
        context["team"] = TeamsSerializer(self.team_obj).data
        return Response(context)

    @extend_schema(
        tags=["Teams"], request=TeamswaggerCreateSerializer, parameters=swagger_params.organization_params
    )
    def put(self, request, pk, *args, **kwargs):
        if self.request.profile.role != "ADMIN" and not self.request.profile.is_admin:
            return Response(
                {
                    "error": True,
                    "errors": "You don't have permission to perform this action.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        params = request.data
        self.team = self.get_object(pk)
        actual_users = self.team.get_users()
        removed_users = []
        serializer = TeamCreateSerializer(
            data=params, instance=self.team, request_obj=request
        )
        if serializer.is_valid():
            team_obj = serializer.save()

            team_obj.users.clear()
            if params.get("assign_users"):
                assinged_to_list = params.get("assign_users")
                profiles = Profile.objects.filter(
                    id__in=assinged_to_list, org=request.profile.org
                )
                if profiles:
                    team_obj.users.add(*profiles)
            update_team_users.delay(pk, str(request.profile.org.id))
            latest_users = team_obj.get_users()
            for user in actual_users:
                if user not in latest_users:
                    removed_users.append(user)
            remove_users.delay(removed_users, pk, str(request.profile.org.id))
            return Response(
                {"error": False, "message": "Team Updated Successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @extend_schema(
        tags=["Teams"], parameters=swagger_params.organization_params
    )
    def delete(self, request, pk, **kwargs):
        if self.request.profile.role != "ADMIN" and not self.request.profile.is_admin:
            return Response(
                {
                    "error": True,
                    "errors": "You don't have permission to perform this action.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        self.team_obj = self.get_object(pk)
        self.team_obj.delete()
        return Response(
            {"error": False, "message": "Team Deleted Successfully"},
            status=status.HTTP_200_OK,
        )
