"""Escalation policy admin endpoints.

See docs/cases/tier1/escalation.md.
"""

from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from cases.models import EscalationPolicy
from cases.serializer import EscalationPolicySerializer
from common.permissions import HasOrgContext


def _is_admin(profile):
    return profile.role == "ADMIN" or getattr(profile, "is_admin", False)


def _admin_required():
    return Response(
        {"error": True, "errors": "Admin access required"},
        status=status.HTTP_403_FORBIDDEN,
    )


class EscalationPolicyListCreateView(APIView):
    """GET lists policies for the org; POST creates one (admin)."""

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(tags=["Escalation"], responses={200: EscalationPolicySerializer(many=True)})
    def get(self, request, *args, **kwargs):
        org = request.profile.org
        qs = EscalationPolicy.objects.filter(org=org).order_by("priority")
        return Response(
            {
                "policies": EscalationPolicySerializer(
                    qs, many=True, context={"request": request, "org": org}
                ).data
            }
        )

    @extend_schema(
        tags=["Escalation"],
        request=EscalationPolicySerializer,
        responses={201: EscalationPolicySerializer},
    )
    def post(self, request, *args, **kwargs):
        if not _is_admin(request.profile):
            return _admin_required()
        org = request.profile.org
        serializer = EscalationPolicySerializer(
            data=request.data, context={"request": request, "org": org}
        )
        if not serializer.is_valid():
            return Response(
                {"error": True, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save(org=org)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class EscalationPolicyDetailView(APIView):
    """GET / PUT / DELETE one policy. DELETE is hard-delete (policies are config)."""

    permission_classes = (IsAuthenticated, HasOrgContext)

    def _get_object(self, pk, org):
        return EscalationPolicy.objects.filter(pk=pk, org=org).first()

    @extend_schema(tags=["Escalation"], responses={200: EscalationPolicySerializer})
    def get(self, request, pk, *args, **kwargs):
        obj = self._get_object(pk, request.profile.org)
        if not obj:
            return Response(
                {"error": True, "errors": "Escalation policy not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            EscalationPolicySerializer(
                obj, context={"request": request, "org": request.profile.org}
            ).data
        )

    @extend_schema(
        tags=["Escalation"],
        request=EscalationPolicySerializer,
        responses={200: EscalationPolicySerializer},
    )
    def put(self, request, pk, *args, **kwargs):
        if not _is_admin(request.profile):
            return _admin_required()
        org = request.profile.org
        obj = self._get_object(pk, org)
        if not obj:
            return Response(
                {"error": True, "errors": "Escalation policy not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        # `priority` is the natural key — disallow changing it post-create
        # (would collide with the (org, priority) unique constraint anyway).
        data = {k: v for k, v in request.data.items() if k != "priority"}
        serializer = EscalationPolicySerializer(
            obj,
            data=data,
            partial=True,
            context={"request": request, "org": org},
        )
        if not serializer.is_valid():
            return Response(
                {"error": True, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save()
        return Response(serializer.data)

    @extend_schema(
        tags=["Escalation"],
        responses={
            200: inline_serializer(
                name="EscalationPolicyDeleteResponse",
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
                {"error": True, "errors": "Escalation policy not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        obj.delete()
        return Response(
            {"error": False, "message": "Escalation policy deleted"},
            status=status.HTTP_200_OK,
        )
