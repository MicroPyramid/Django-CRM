"""Generic custom-field definition CRUD endpoints.

Lives in `common` so all entity apps (Cases first, Leads/Contacts/etc. later)
can drive their per-entity schemas through one API.

See docs/cases/tier1/custom-fields.md.
"""

from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.models import CustomFieldDefinition
from common.permissions import HasOrgContext
from common.serializer import CustomFieldDefinitionSerializer


def _is_admin(profile):
    return profile.role == "ADMIN" or getattr(profile, "is_admin", False)


def _admin_required():
    return Response(
        {"error": True, "errors": "Admin access required"},
        status=status.HTTP_403_FORBIDDEN,
    )


class CustomFieldDefinitionListCreateView(APIView):
    """GET ?target_model=Case lists definitions; POST creates one (admin)."""

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(tags=["CustomFields"], responses={200: CustomFieldDefinitionSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        org = request.profile.org
        qs = CustomFieldDefinition.objects.filter(org=org)
        target_model = request.query_params.get("target_model")
        if target_model:
            qs = qs.filter(target_model=target_model)
        if request.query_params.get("active_only") == "true":
            qs = qs.filter(is_active=True)
        return Response(
            {"definitions": CustomFieldDefinitionSerializer(qs, many=True).data}
        )

    @extend_schema(
        tags=["CustomFields"],
        request=CustomFieldDefinitionSerializer,
        responses={201: CustomFieldDefinitionSerializer},
    )
    def post(self, request, *args, **kwargs):
        if not _is_admin(request.profile):
            return _admin_required()
        org = request.profile.org
        serializer = CustomFieldDefinitionSerializer(
            data=request.data, context={"org": org}
        )
        if not serializer.is_valid():
            return Response(
                {"error": True, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save(org=org)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CustomFieldDefinitionDetailView(APIView):
    """GET / PUT / DELETE one definition. DELETE soft-deletes (is_active=False)."""

    permission_classes = (IsAuthenticated, HasOrgContext)

    def _get_object(self, pk, org):
        return CustomFieldDefinition.objects.filter(pk=pk, org=org).first()

    @extend_schema(tags=["CustomFields"], responses={200: CustomFieldDefinitionSerializer})
    def get(self, request, pk, *args, **kwargs):
        obj = self._get_object(pk, request.profile.org)
        if not obj:
            return Response(
                {"error": True, "errors": "Custom field not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(CustomFieldDefinitionSerializer(obj).data)

    @extend_schema(
        tags=["CustomFields"],
        request=CustomFieldDefinitionSerializer,
        responses={200: CustomFieldDefinitionSerializer},
    )
    def put(self, request, pk, *args, **kwargs):
        if not _is_admin(request.profile):
            return _admin_required()
        obj = self._get_object(pk, request.profile.org)
        if not obj:
            return Response(
                {"error": True, "errors": "Custom field not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = CustomFieldDefinitionSerializer(
            obj,
            data=request.data,
            partial=True,
            context={"org": request.profile.org},
        )
        if not serializer.is_valid():
            return Response(
                {"error": True, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save()
        return Response(serializer.data)

    @extend_schema(
        tags=["CustomFields"],
        responses={
            200: inline_serializer(
                name="CustomFieldDeleteResponse",
                fields={
                    "error": serializers.BooleanField(),
                    "message": serializers.CharField(),
                },
            )
        },
    )
    def delete(self, request, pk, *args, **kwargs):
        if not _is_admin(request.profile):
            return _admin_required()
        obj = self._get_object(pk, request.profile.org)
        if not obj:
            return Response(
                {"error": True, "errors": "Custom field not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        # Soft delete — historical values on entities stay readable; the field
        # just stops appearing in admin UIs and stops accepting new writes.
        obj.is_active = False
        obj.save(update_fields=["is_active", "updated_at"])
        return Response(
            {"error": False, "message": "Custom field deactivated"},
            status=status.HTTP_200_OK,
        )
