"""Tests for Tier 3 approval workflows.

Covers rule matching/specificity, the Case.clean() close-gate, the per-case
request flow, the inbox endpoint, and the four state transitions
(approve / reject / cancel + re-entry guards).
"""

from __future__ import annotations

from datetime import date

import pytest
from crum import impersonate
from django.core.exceptions import ValidationError

from cases.approvals import Approval, ApprovalRule, find_matching_rule
from cases.models import Case
from common.models import Activity


def _make_case(
    org,
    creator,
    *,
    name="Sample case",
    status_value="New",
    priority="Normal",
    case_type=None,
):
    with impersonate(creator):
        return Case.objects.create(
            name=name,
            status=status_value,
            priority=priority,
            case_type=case_type,
            org=org,
        )


def _make_rule(
    org,
    *,
    name="Default approval",
    is_active=True,
    match_priority=None,
    match_case_type=None,
    approver_role="ADMIN",
    approvers=None,
):
    rule = ApprovalRule.objects.create(
        org=org,
        name=name,
        is_active=is_active,
        match_priority=match_priority,
        match_case_type=match_case_type,
        approver_role=approver_role,
    )
    if approvers:
        rule.approvers.set(approvers)
    return rule


@pytest.mark.django_db
class TestRuleMatching:
    def test_inactive_rule_does_not_match(self, admin_user, org_a):
        case = _make_case(org_a, admin_user, priority="Urgent")
        _make_rule(org_a, is_active=False, match_priority="Urgent")
        assert find_matching_rule(case) is None

    def test_priority_filter(self, admin_user, org_a):
        urgent = _make_case(org_a, admin_user, name="U", priority="Urgent")
        normal = _make_case(org_a, admin_user, name="N", priority="Normal")
        rule = _make_rule(org_a, match_priority="Urgent")
        assert find_matching_rule(urgent) == rule
        assert find_matching_rule(normal) is None

    def test_specificity_tiebreak(self, admin_user, org_a):
        case = _make_case(
            org_a,
            admin_user,
            priority="Urgent",
            case_type="Incident",
        )
        broad = _make_rule(org_a, name="broad", match_priority="Urgent")
        specific = _make_rule(
            org_a,
            name="specific",
            match_priority="Urgent",
            match_case_type="Incident",
        )
        chosen = find_matching_rule(case)
        assert chosen == specific, (
            f"More-specific rule should win, got: {chosen.name if chosen else None}"
        )
        # Unused but covers the broader rule still being a candidate.
        assert broad.matches(case) is True

    def test_cross_org_does_not_match(self, admin_user, org_a, org_b):
        case = _make_case(org_a, admin_user, priority="Urgent")
        _make_rule(org_b, match_priority="Urgent")
        assert find_matching_rule(case) is None


@pytest.mark.django_db
class TestCloseGate:
    def test_close_blocked_when_rule_matches(self, admin_user, org_a):
        case = _make_case(org_a, admin_user, priority="Urgent")
        _make_rule(org_a, match_priority="Urgent")
        case.status = "Closed"
        case.closed_on = date.today()
        with pytest.raises(ValidationError) as exc:
            case.clean()
        assert "approval" in str(exc.value).lower()

    def test_close_allowed_with_approved_request(
        self, admin_user, admin_profile, org_a
    ):
        case = _make_case(org_a, admin_user, priority="Urgent")
        rule = _make_rule(org_a, match_priority="Urgent")
        Approval.objects.create(
            org=org_a,
            case=case,
            rule=rule,
            requested_by=admin_profile,
            state="approved",
        )
        case.status = "Closed"
        case.closed_on = date.today()
        case.clean()  # should not raise

    def test_close_unaffected_when_no_rule(self, admin_user, org_a):
        case = _make_case(org_a, admin_user, priority="Urgent")
        case.status = "Closed"
        case.closed_on = date.today()
        case.clean()  # should not raise

    def test_pending_approval_does_not_satisfy_gate(
        self, admin_user, admin_profile, org_a
    ):
        case = _make_case(org_a, admin_user, priority="Urgent")
        rule = _make_rule(org_a, match_priority="Urgent")
        Approval.objects.create(
            org=org_a,
            case=case,
            rule=rule,
            requested_by=admin_profile,
            state="pending",
        )
        case.status = "Closed"
        case.closed_on = date.today()
        with pytest.raises(ValidationError):
            case.clean()


@pytest.mark.django_db
class TestRequestApprovalEndpoint:
    def test_auto_resolves_rule(self, admin_client, admin_user, org_a):
        case = _make_case(org_a, admin_user, priority="Urgent")
        _make_rule(org_a, match_priority="Urgent")
        res = admin_client.post(
            f"/api/cases/{case.id}/request-approval/",
            data={"note": "please review"},
            format="json",
        )
        assert res.status_code == 201, res.content
        assert res.data["state"] == "pending"
        assert res.data["case_summary"]["id"] == str(case.id)

        activity = Activity.objects.filter(
            entity_id=case.id, action="APPROVAL_REQUESTED"
        ).first()
        assert activity is not None
        assert activity.metadata["approval_id"] == res.data["id"]

    def test_rejects_when_no_rule_matches(self, admin_client, admin_user, org_a):
        case = _make_case(org_a, admin_user, priority="Normal")
        res = admin_client.post(
            f"/api/cases/{case.id}/request-approval/", data={}, format="json"
        )
        assert res.status_code == 400
        assert "no active" in str(res.data).lower()

    def test_double_request_returns_409(
        self, admin_client, admin_user, admin_profile, org_a
    ):
        case = _make_case(org_a, admin_user, priority="Urgent")
        rule = _make_rule(org_a, match_priority="Urgent")
        Approval.objects.create(
            org=org_a,
            case=case,
            rule=rule,
            requested_by=admin_profile,
            state="pending",
        )
        res = admin_client.post(
            f"/api/cases/{case.id}/request-approval/", data={}, format="json"
        )
        assert res.status_code == 409
        assert "approval_id" in res.data


@pytest.mark.django_db
class TestStateTransitions:
    def _setup(self, org, admin_profile, admin_user, *, approvers=None):
        case = _make_case(org, admin_user, priority="Urgent")
        rule = _make_rule(org, match_priority="Urgent", approvers=approvers)
        approval = Approval.objects.create(
            org=org,
            case=case,
            rule=rule,
            requested_by=admin_profile,
            state="pending",
        )
        return case, rule, approval

    def test_approve_records_activity(
        self, admin_client, admin_user, admin_profile, org_a
    ):
        case, rule, approval = self._setup(org_a, admin_profile, admin_user)
        res = admin_client.post(
            f"/api/cases/approvals/{approval.id}/approve/",
            data={"note": "ok"},
            format="json",
        )
        assert res.status_code == 200
        assert res.data["state"] == "approved"
        approval.refresh_from_db()
        assert approval.approver_id == admin_profile.id
        assert approval.decided_at is not None
        assert Activity.objects.filter(
            entity_id=case.id, action="APPROVED"
        ).exists()

    def test_reject_requires_reason(
        self, admin_client, admin_user, admin_profile, org_a
    ):
        case, rule, approval = self._setup(org_a, admin_profile, admin_user)
        bare = admin_client.post(
            f"/api/cases/approvals/{approval.id}/reject/", data={}, format="json"
        )
        assert bare.status_code == 400

        ok = admin_client.post(
            f"/api/cases/approvals/{approval.id}/reject/",
            data={"reason": "needs more triage"},
            format="json",
        )
        assert ok.status_code == 200
        approval.refresh_from_db()
        assert approval.state == "rejected"
        assert approval.reason == "needs more triage"
        assert Activity.objects.filter(
            entity_id=case.id, action="REJECTED"
        ).exists()

    def test_cancel_requires_requester_or_admin(
        self,
        admin_client,
        admin_user,
        admin_profile,
        user_client,
        regular_user,
        user_profile,
        org_a,
    ):
        # Approval requested by `user_profile`, attempted cancel by ADMIN succeeds.
        case = _make_case(org_a, regular_user, priority="Urgent")
        rule = _make_rule(org_a, match_priority="Urgent")
        approval = Approval.objects.create(
            org=org_a,
            case=case,
            rule=rule,
            requested_by=user_profile,
            state="pending",
        )

        # Admin cancels (allowed).
        res = admin_client.post(
            f"/api/cases/approvals/{approval.id}/cancel/", data={}, format="json"
        )
        assert res.status_code == 200, res.content
        approval.refresh_from_db()
        assert approval.state == "cancelled"
        assert Activity.objects.filter(
            entity_id=case.id, action="APPROVAL_CANCELLED"
        ).exists()

    def test_user_cannot_cancel_others_request(
        self,
        admin_client,
        admin_user,
        admin_profile,
        user_client,
        regular_user,
        user_profile,
        org_a,
    ):
        case = _make_case(org_a, admin_user, priority="Urgent")
        rule = _make_rule(org_a, match_priority="Urgent")
        approval = Approval.objects.create(
            org=org_a,
            case=case,
            rule=rule,
            requested_by=admin_profile,  # admin requested it
            state="pending",
        )
        res = user_client.post(
            f"/api/cases/approvals/{approval.id}/cancel/", data={}, format="json"
        )
        assert res.status_code == 403

    def test_non_approver_cannot_approve(
        self,
        user_client,
        regular_user,
        user_profile,
        admin_user,
        admin_profile,
        org_a,
    ):
        case = _make_case(org_a, admin_user, priority="Urgent")
        # Rule restricts to ADMIN role only.
        rule = _make_rule(org_a, match_priority="Urgent", approver_role="ADMIN")
        approval = Approval.objects.create(
            org=org_a,
            case=case,
            rule=rule,
            requested_by=admin_profile,
            state="pending",
        )
        res = user_client.post(
            f"/api/cases/approvals/{approval.id}/approve/", data={}, format="json"
        )
        assert res.status_code == 403

    def test_double_approve_rejected(
        self, admin_client, admin_user, admin_profile, org_a
    ):
        _, _, approval = self._setup(org_a, admin_profile, admin_user)
        a = admin_client.post(
            f"/api/cases/approvals/{approval.id}/approve/",
            data={},
            format="json",
        )
        assert a.status_code == 200
        b = admin_client.post(
            f"/api/cases/approvals/{approval.id}/approve/",
            data={},
            format="json",
        )
        assert b.status_code == 400
        assert "already" in str(b.data).lower()


@pytest.mark.django_db
class TestInbox:
    def test_mine_filters_to_actionable_rows(
        self,
        admin_client,
        admin_user,
        admin_profile,
        user_client,
        regular_user,
        user_profile,
        org_a,
    ):
        case = _make_case(org_a, admin_user, priority="Urgent")
        rule_admin_only = _make_rule(
            org_a,
            name="admins-only",
            match_priority="Urgent",
            approver_role="ADMIN",
        )
        rule_user_explicit = _make_rule(
            org_a,
            name="explicit-user",
            match_case_type="Incident",
            # Use MANAGER so admin's role match doesn't sweep this row in too.
            approver_role="MANAGER",
            approvers=[user_profile],
        )

        # Both approvals exist.
        Approval.objects.create(
            org=org_a,
            case=case,
            rule=rule_admin_only,
            requested_by=admin_profile,
            state="pending",
        )
        case2 = _make_case(
            org_a, admin_user, name="C2", priority="Low", case_type="Incident"
        )
        Approval.objects.create(
            org=org_a,
            case=case2,
            rule=rule_user_explicit,
            requested_by=admin_profile,
            state="pending",
        )

        # Admin sees both via mine=true (admin role + admin-only rule).
        admin_view = admin_client.get(
            "/api/cases/approvals/?mine=true&state=pending"
        )
        assert admin_view.status_code == 200
        admin_ids = {a["id"] for a in admin_view.data["approvals"]}
        # Admin matches the ADMIN-role rule but isn't in the explicit-user pool.
        assert len(admin_ids) == 1

        # Regular user sees only the explicit pool entry.
        user_view = user_client.get(
            "/api/cases/approvals/?mine=true&state=pending"
        )
        assert user_view.status_code == 200
        user_ids = {a["id"] for a in user_view.data["approvals"]}
        assert len(user_ids) == 1


@pytest.mark.django_db
class TestRuleCRUD:
    def test_admin_creates_rule(self, admin_client, org_a):
        res = admin_client.post(
            "/api/cases/approval-rules/",
            data={
                "name": "Urgent close approval",
                "match_priority": "Urgent",
                "approver_role": "ADMIN",
            },
            format="json",
        )
        assert res.status_code == 201, res.content
        assert ApprovalRule.objects.filter(name="Urgent close approval").exists()

    def test_non_admin_cannot_create(self, user_client):
        res = user_client.post(
            "/api/cases/approval-rules/",
            data={"name": "x", "match_priority": "Urgent"},
            format="json",
        )
        assert res.status_code == 403

    def test_delete_with_history_soft_disables(
        self, admin_client, admin_user, admin_profile, org_a
    ):
        case = _make_case(org_a, admin_user, priority="Urgent")
        rule = _make_rule(org_a, match_priority="Urgent")
        Approval.objects.create(
            org=org_a,
            case=case,
            rule=rule,
            requested_by=admin_profile,
            state="approved",
        )
        res = admin_client.delete(f"/api/cases/approval-rules/{rule.id}/")
        # PROTECT FK + history present → endpoint soft-disables instead of 204.
        assert res.status_code == 200
        rule.refresh_from_db()
        assert rule.is_active is False
