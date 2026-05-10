"""Routing-rule admin endpoints + dry-run test endpoint.

See docs/cases/tier1/auto-routing.md.
"""

from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from cases.models import Case, RoutingRule
from cases.routing import evaluate
from cases.serializer import RoutingRuleSerializer
from common.permissions import HasOrgContext


def _is_admin(profile):
    return profile.role == "ADMIN" or getattr(profile, "is_admin", False)


def _admin_required():
    return Response(
        {"error": True, "errors": "Admin access required"},
        status=status.HTTP_403_FORBIDDEN,
    )


class RoutingRuleListCreateView(APIView):
    """GET lists rules ordered by priority_order; POST creates one (admin)."""

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(tags=["Routing"], responses={200: RoutingRuleSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        org = request.profile.org
        qs = (
            RoutingRule.objects.filter(org=org)
            .order_by("priority_order", "created_at")
            .prefetch_related("target_assignees")
        )
        return Response(
            {
                "rules": RoutingRuleSerializer(
                    qs, many=True, context={"request": request, "org": org}
                ).data
            }
        )

    @extend_schema(
        tags=["Routing"],
        request=RoutingRuleSerializer,
        responses={201: RoutingRuleSerializer},
    )
    def post(self, request, *args, **kwargs):
        if not _is_admin(request.profile):
            return _admin_required()
        org = request.profile.org
        serializer = RoutingRuleSerializer(
            data=request.data, context={"request": request, "org": org}
        )
        if not serializer.is_valid():
            return Response(
                {"error": True, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save(org=org)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class RoutingRuleDetailView(APIView):
    """GET / PUT / DELETE one routing rule."""

    permission_classes = (IsAuthenticated, HasOrgContext)

    def _get_object(self, pk, org):
        return RoutingRule.objects.filter(pk=pk, org=org).first()

    @extend_schema(tags=["Routing"], responses={200: RoutingRuleSerializer})
    def get(self, request, pk, *args, **kwargs):
        obj = self._get_object(pk, request.profile.org)
        if not obj:
            return Response(
                {"error": True, "errors": "Routing rule not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            RoutingRuleSerializer(
                obj, context={"request": request, "org": request.profile.org}
            ).data
        )

    @extend_schema(
        tags=["Routing"],
        request=RoutingRuleSerializer,
        responses={200: RoutingRuleSerializer},
    )
    def put(self, request, pk, *args, **kwargs):
        if not _is_admin(request.profile):
            return _admin_required()
        org = request.profile.org
        obj = self._get_object(pk, org)
        if not obj:
            return Response(
                {"error": True, "errors": "Routing rule not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = RoutingRuleSerializer(
            obj,
            data=request.data,
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
        tags=["Routing"],
        responses={
            200: inline_serializer(
                name="RoutingRuleDeleteResponse",
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
                {"error": True, "errors": "Routing rule not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        obj.delete()
        return Response(
            {"error": False, "message": "Routing rule deleted"},
            status=status.HTTP_200_OK,
        )


class RoutingRuleTestView(APIView):
    """Dry-run a routing rule against a sample Case (no state mutation)."""

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(
        tags=["Routing"],
        request=inline_serializer(
            name="RoutingRuleTestRequest",
            fields={"case_id": serializers.UUIDField()},
        ),
        responses={
            200: inline_serializer(
                name="RoutingRuleTestResponse",
                fields={
                    "matched": serializers.BooleanField(),
                    "rule_id": serializers.CharField(allow_null=True),
                    "rule_name": serializers.CharField(allow_blank=True),
                    "strategy": serializers.CharField(allow_blank=True),
                    "would_assign_profile_ids": serializers.ListField(
                        child=serializers.CharField()
                    ),
                    "would_assign_team_id": serializers.CharField(allow_null=True),
                    "reason": serializers.CharField(allow_blank=True),
                },
            )
        },
    )
    def post(self, request, *args, **kwargs):
        if not _is_admin(request.profile):
            return _admin_required()
        org = request.profile.org
        case_id = request.data.get("case_id")
        if not case_id:
            return Response(
                {"error": True, "errors": "case_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        case = Case.objects.filter(pk=case_id, org=org).first()
        if case is None:
            return Response(
                {"error": True, "errors": "Case not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        decision = evaluate(case, dry_run=True)
        return Response(
            {
                "matched": decision.matched_rule_id is not None,
                "rule_id": decision.matched_rule_id,
                "rule_name": decision.matched_rule_name,
                "strategy": decision.strategy,
                "would_assign_profile_ids": decision.assigned_profile_ids,
                "would_assign_team_id": decision.assigned_team_id,
                "reason": decision.reason,
            }
        )
