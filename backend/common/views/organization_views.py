import secrets

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer

from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from common import serializer, swagger_params
from common.models import Org, Profile
from common.serializer import (
    CreateProfileSerializer,
    OrganizationSerializer,
    OrgProfileCreateSerializer,
    ProfileSerializer,
    ShowOrganizationListSerializer,
)


class OrgProfileCreateView(APIView):
    permission_classes = (IsAuthenticated,)

    model1 = Org
    model2 = Profile
    serializer_class = OrgProfileCreateSerializer
    profile_serializer = CreateProfileSerializer

    @extend_schema(
        operation_id="org_create",
        description="Organization and profile Creation api",
        request=OrgProfileCreateSerializer,
    )
    def post(self, request, format=None):
        data = request.data
        data["api_key"] = secrets.token_hex(16)
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            org_obj = serializer.save()

            # now creating the profile
            profile_obj = self.model2.objects.create(user=request.user, org=org_obj)
            # now the current user is the admin of the newly created organisation
            profile_obj.is_organization_admin = True
            profile_obj.role = "ADMIN"
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
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    @extend_schema(
        operation_id="org_list",
        description="Just Pass the token, will return ORG list, associated with user",
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
        operation_id="org_update",
        description="Update organization details",
        request=OrganizationSerializer,
        responses={200: OrganizationSerializer},
    )
    def put(self, request, pk, format=None):
        # Check if user has admin access to this organization
        if not request.profile:
            return Response(
                {"error": True, "errors": "Organization context required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify the organization matches the current context
        if str(request.profile.org.id) != str(pk):
            return Response(
                {"error": True, "errors": "Cannot update a different organization"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Check if user is admin
        if (
            request.profile.role != "ADMIN"
            and not request.profile.is_organization_admin
        ):
            return Response(
                {
                    "error": True,
                    "errors": "Only organization admins can update organization details",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            org = Org.objects.get(id=pk)
        except Org.DoesNotExist:
            return Response(
                {"error": True, "errors": "Organization not found"},
                status=status.HTTP_404_NOT_FOUND,
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
                "org": OrganizationSerializer(org).data,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        operation_id="org_destroy",
        description="Partial update organization details",
        request=OrganizationSerializer,
        responses={200: OrganizationSerializer},
    )
    def patch(self, request, pk, format=None):
        """Handle partial updates to an organization."""
        # Check if user has admin access to this organization
        if not request.profile:
            return Response(
                {"error": True, "errors": "Organization context required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify the organization matches the current context
        if str(request.profile.org.id) != str(pk):
            return Response(
                {"error": True, "errors": "Cannot update a different organization"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Check if user is admin
        if (
            request.profile.role != "ADMIN"
            and not request.profile.is_organization_admin
        ):
            return Response(
                {
                    "error": True,
                    "errors": "Only organization admins can update organization details",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            org = Org.objects.get(id=pk)
        except Org.DoesNotExist:
            return Response(
                {"error": True, "errors": "Organization not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Partial update fields
        data = request.data
        if "name" in data:
            org.name = data["name"]

        org.save()

        return Response(
            {
                "error": False,
                "message": "Organization updated successfully",
                "org": OrganizationSerializer(org).data,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        operation_id="org_retrieve",
        description="Get organization details",
        responses={200: OrganizationSerializer},
    )
    def get(self, request, pk, format=None):
        # Check if user has access to this organization
        if not request.profile:
            return Response(
                {"error": True, "errors": "Organization context required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify the organization matches the current context
        if str(request.profile.org.id) != str(pk):
            return Response(
                {"error": True, "errors": "Cannot access a different organization"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            org = Org.objects.get(id=pk)
        except Org.DoesNotExist:
            return Response(
                {"error": True, "errors": "Organization not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {"error": False, "org": OrganizationSerializer(org).data},
            status=status.HTTP_200_OK,
        )


class ProfileView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["profile"],
        parameters=swagger_params.organization_params,
        responses={
            200: inline_serializer(
                name="ProfileViewResponse", fields={"user_obj": ProfileSerializer()}
            )
        },
    )
    def get(self, request, format=None):
        # profile=Profile.objects.get(user=request.user)
        context = {}
        context["user_obj"] = ProfileSerializer(self.request.profile).data
        return Response(context, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["profile"],
        parameters=swagger_params.organization_params,
        request=inline_serializer(
            name="ProfilePatchRequest",
            fields={"phone": serializers.CharField(required=False)},
        ),
        responses={
            200: inline_serializer(
                name="ProfilePatchUpdateResponse",
                fields={
                    "message": serializers.CharField(),
                    "user_obj": ProfileSerializer(),
                },
            )
        },
    )
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
            {
                "message": "Profile updated successfully",
                "user_obj": ProfileSerializer(profile).data,
            },
            status=status.HTTP_200_OK,
        )


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
            OpenApiParameter(
                "org",
                OpenApiTypes.UUID,
                OpenApiParameter.HEADER,
                required=True,
                description="Organization ID",
            )
        ],
        responses={200: serializer.ProfileDetailSerializer},
    )
    def get(self, request):
        # request.profile is set by middleware based on org header
        if not hasattr(request, "profile") or request.profile is None:
            return Response(
                {"error": "Organization header required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile_serializer = serializer.ProfileDetailSerializer(request.profile)
        return Response(profile_serializer.data, status=status.HTTP_200_OK)
