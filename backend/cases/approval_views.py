"""
Approval workflow endpoints (Tier 3 approvals).

Two flavors of endpoint live here:

* Admin-configured rules (CRUD): ``GET/POST /api/cases/approval-rules/``,
  ``GET/PUT/DELETE /api/cases/approval-rules/<pk>/``.
* Per-case requests + decisions: ``POST /api/cases/<pk>/request-approval/``,
  ``GET /api/cases/approvals/`` inbox, ``POST /api/cases/approvals/<pk>/{approve,reject,cancel}/``.

Each transition writes a ``common.Activity`` row using the verbs registered in
``common/models.Activity.ACTION_CHOICES`` (``APPROVAL_REQUESTED``,
``APPROVED``, ``REJECTED``, ``APPROVAL_CANCELLED``). Two approvers cannot
double-approve the same row — every transition takes a row lock first.
"""

from __future__ import annotations

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from cases.approvals import Approval, ApprovalRule, find_matching_rule
from cases.models import Case
from cases.serializer import (
    ApprovalRequestSerializer,
    ApprovalRuleSerializer,
    ApprovalSerializer,
)
from common.models import Activity, Profile
from common.permissions import HasOrgContext


def _is_admin(profile) -> bool:
    return profile.role == "ADMIN" or getattr(profile, "is_admin", False)


def _admin_required():
    return Response(
        {"error": True, "errors": "Admin access required"},
        status=status.HTTP_403_FORBIDDEN,
    )


def _record(case, action, metadata, actor):
    Activity.objects.create(
        user=actor,
        action=action,
        entity_type="Case",
        entity_id=case.pk,
        entity_name=str(case)[:255],
        metadata=metadata,
        org_id=case.org_id,
    )


# ---------------------------------------------------------------------------
# Rule CRUD


class ApprovalRuleListCreateView(APIView):
    permission_classes = (IsAuthenticated, HasOrgContext)

    def get(self, request):
        org = request.profile.org
        qs = ApprovalRule.objects.filter(org=org).prefetch_related(
            "approvers__user", "match_team"
        )
        return Response(
            {"rules": ApprovalRuleSerializer(qs, many=True).data},
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        if not _is_admin(request.profile):
            return _admin_required()
        org = request.profile.org
        serializer = ApprovalRuleSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": True, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Filter approver / match_team selection to the requester's org so
        # an admin in org A cannot point at a profile in org B.
        approvers = serializer.validated_data.get("approvers") or []
        for p in approvers:
            if p.org_id != org.id:
                return Response(
                    {"error": True, "errors": "Approver is outside this org."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        match_team = serializer.validated_data.get("match_team")
        if match_team is not None and match_team.org_id != org.id:
            return Response(
                {"error": True, "errors": "Team is outside this org."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        rule = serializer.save(org=org)
        return Response(
            ApprovalRuleSerializer(rule).data, status=status.HTTP_201_CREATED
        )


class ApprovalRuleDetailView(APIView):
    permission_classes = (IsAuthenticated, HasOrgContext)

    def _get(self, pk, org):
        return ApprovalRule.objects.filter(pk=pk, org=org).first()

    def get(self, request, pk):
        rule = self._get(pk, request.profile.org)
        if rule is None:
            return Response(
                {"error": True, "errors": "Rule not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(ApprovalRuleSerializer(rule).data)

    def put(self, request, pk):
        if not _is_admin(request.profile):
            return _admin_required()
        rule = self._get(pk, request.profile.org)
        if rule is None:
            return Response(
                {"error": True, "errors": "Rule not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = ApprovalRuleSerializer(rule, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(
                {"error": True, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        rule = serializer.save()
        return Response(ApprovalRuleSerializer(rule).data)

    def delete(self, request, pk):
        if not _is_admin(request.profile):
            return _admin_required()
        rule = self._get(pk, request.profile.org)
        if rule is None:
            return Response(
                {"error": True, "errors": "Rule not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        # Hard delete is fine — Approval.rule is on_delete=PROTECT, so any
        # historical request keeps the rule alive automatically.
        if rule.requests.exists():
            # Soft-disable instead of hard-delete when there is history.
            rule.is_active = False
            rule.save(update_fields=["is_active", "updated_at"])
            return Response(
                {"id": str(rule.id), "is_active": False},
                status=status.HTTP_200_OK,
            )
        rule.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Per-case requests + decisions


class CaseRequestApprovalView(APIView):
    """``POST /api/cases/<pk>/request-approval/`` — agent fires a new request."""

    permission_classes = (IsAuthenticated, HasOrgContext)

    @transaction.atomic
    def post(self, request, pk):
        org = request.profile.org
        case = get_object_or_404(Case, id=pk, org=org)
        body = ApprovalRequestSerializer(data=request.data)
        if not body.is_valid():
            return Response(
                {"error": True, "errors": body.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        rule_id = body.validated_data.get("rule_id")
        note = body.validated_data.get("note") or ""

        if rule_id:
            rule = ApprovalRule.objects.filter(
                id=rule_id, org=org, is_active=True
            ).first()
            if rule is None:
                return Response(
                    {"error": True, "errors": "Rule not found or inactive."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not rule.matches(case):
                return Response(
                    {"error": True, "errors": "Rule does not match this case."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            rule = find_matching_rule(case, trigger_event="pre_close")
            if rule is None:
                return Response(
                    {
                        "error": True,
                        "errors": "No active approval rule matches this case.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Reject when a still-open request exists for the same case+rule.
        existing = (
            Approval.objects.select_for_update()
            .filter(case=case, rule=rule, state="pending")
            .first()
        )
        if existing is not None:
            return Response(
                {
                    "error": True,
                    "errors": "An approval is already pending for this case.",
                    "approval_id": str(existing.id),
                },
                status=status.HTTP_409_CONFLICT,
            )

        approval = Approval.objects.create(
            org=org,
            case=case,
            rule=rule,
            requested_by=request.profile,
            note=note,
        )
        _record(
            case,
            "APPROVAL_REQUESTED",
            {
                "approval_id": str(approval.id),
                "rule_id": str(rule.id),
                "rule_name": rule.name,
            },
            actor=request.profile,
        )
        return Response(
            ApprovalSerializer(approval).data, status=status.HTTP_201_CREATED
        )


class ApprovalInboxView(APIView):
    """``GET /api/cases/approvals/`` — list approvals.

    Query params:
      * ``state`` (default ``pending``) — filter by state, or ``all`` to drop the filter.
      * ``mine`` (``true``/``false``) — when true, restrict to approvals the
        caller can act on (in rule.approvers OR matches rule.approver_role).
    """

    permission_classes = (IsAuthenticated, HasOrgContext)

    def get(self, request):
        org = request.profile.org
        qs = (
            Approval.objects.filter(org=org)
            .select_related(
                "case",
                "rule",
                "requested_by__user",
                "approver__user",
            )
            .order_by("-created_at")
        )

        state = (request.query_params.get("state") or "pending").lower()
        if state and state != "all":
            qs = qs.filter(state=state)

        case_id = request.query_params.get("case")
        if case_id:
            qs = qs.filter(case_id=case_id)

        mine = (request.query_params.get("mine") or "").lower() in (
            "true",
            "1",
            "yes",
        )
        if mine:
            # Only this branch reads `rule.approvers`, so the prefetch is
            # scoped here instead of paid on every list call.
            profile = request.profile
            rows = list(qs.prefetch_related("rule__approvers"))
            qs = [a for a in rows if a.can_be_acted_on_by(profile)]
            return Response(
                {"approvals": ApprovalSerializer(qs, many=True).data},
                status=status.HTTP_200_OK,
            )

        return Response(
            {"approvals": ApprovalSerializer(qs, many=True).data},
            status=status.HTTP_200_OK,
        )


def _load_pending(pk, org):
    """Locked fetch for state transitions; returns None if missing/wrong-org."""
    return (
        Approval.objects.select_for_update()
        .filter(id=pk, org=org)
        .select_related("case", "rule", "requested_by")
        .first()
    )


class ApprovalApproveView(APIView):
    permission_classes = (IsAuthenticated, HasOrgContext)

    @transaction.atomic
    def post(self, request, pk):
        org = request.profile.org
        approval = _load_pending(pk, org)
        if approval is None:
            return Response(
                {"error": True, "errors": "Approval not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        if approval.state != "pending":
            return Response(
                {
                    "error": True,
                    "errors": f"Approval already {approval.state}.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not approval.can_be_acted_on_by(request.profile):
            return Response(
                {"error": True, "errors": "You are not an approver for this rule."},
                status=status.HTTP_403_FORBIDDEN,
            )
        approval.state = "approved"
        approval.approver = request.profile
        approval.note = (request.data.get("note") or approval.note)[:4096]
        approval.decided_at = timezone.now()
        approval.save(
            update_fields=["state", "approver", "note", "decided_at", "updated_at"]
        )
        _record(
            approval.case,
            "APPROVED",
            {
                "approval_id": str(approval.id),
                "rule_id": str(approval.rule_id),
            },
            actor=request.profile,
        )
        return Response(
            ApprovalSerializer(approval).data, status=status.HTTP_200_OK
        )


class ApprovalRejectView(APIView):
    permission_classes = (IsAuthenticated, HasOrgContext)

    @transaction.atomic
    def post(self, request, pk):
        org = request.profile.org
        reason = (request.data.get("reason") or "").strip()
        if not reason:
            return Response(
                {"error": True, "errors": "Rejection reason is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        approval = _load_pending(pk, org)
        if approval is None:
            return Response(
                {"error": True, "errors": "Approval not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        if approval.state != "pending":
            return Response(
                {
                    "error": True,
                    "errors": f"Approval already {approval.state}.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not approval.can_be_acted_on_by(request.profile):
            return Response(
                {"error": True, "errors": "You are not an approver for this rule."},
                status=status.HTTP_403_FORBIDDEN,
            )
        approval.state = "rejected"
        approval.approver = request.profile
        approval.reason = reason[:4096]
        approval.decided_at = timezone.now()
        approval.save(
            update_fields=[
                "state",
                "approver",
                "reason",
                "decided_at",
                "updated_at",
            ]
        )
        _record(
            approval.case,
            "REJECTED",
            {
                "approval_id": str(approval.id),
                "rule_id": str(approval.rule_id),
                "reason": approval.reason[:1000],
            },
            actor=request.profile,
        )
        return Response(
            ApprovalSerializer(approval).data, status=status.HTTP_200_OK
        )


class ApprovalCancelView(APIView):
    permission_classes = (IsAuthenticated, HasOrgContext)

    @transaction.atomic
    def post(self, request, pk):
        org = request.profile.org
        approval = _load_pending(pk, org)
        if approval is None:
            return Response(
                {"error": True, "errors": "Approval not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        if approval.state != "pending":
            return Response(
                {
                    "error": True,
                    "errors": f"Approval already {approval.state}.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Only the requester (or an admin) can cancel.
        if (
            approval.requested_by_id != request.profile.id
            and not _is_admin(request.profile)
        ):
            return Response(
                {"error": True, "errors": "Only the requester can cancel."},
                status=status.HTTP_403_FORBIDDEN,
            )
        approval.state = "cancelled"
        approval.decided_at = timezone.now()
        approval.save(update_fields=["state", "decided_at", "updated_at"])
        _record(
            approval.case,
            "APPROVAL_CANCELLED",
            {
                "approval_id": str(approval.id),
                "rule_id": str(approval.rule_id),
            },
            actor=request.profile,
        )
        return Response(
            ApprovalSerializer(approval).data, status=status.HTTP_200_OK
        )
