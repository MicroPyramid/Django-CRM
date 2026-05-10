"""Escalation tests: model, admin API, and the scan_for_breached_cases task.

See docs/cases/tier1/escalation.md.
"""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from cases.models import Case, EscalationPolicy
from cases.tasks import ESCALATION_COUNT_CAP, scan_for_breached_cases
from common.models import Activity, Profile, Teams, User

POLICIES_URL = "/api/cases/escalation-policies/"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_target_profile(org, email="agent@test.com"):
    user = User.objects.create_user(email=email, password="x")
    return Profile.objects.create(user=user, org=org, role="USER", is_active=True)


def _make_policy(org, target, **overrides):
    defaults = {
        "priority": "Urgent",
        "first_response_action": "notify",
        "resolution_action": "notify",
        "first_response_target": target,
        "resolution_target": target,
        "is_active": True,
    }
    defaults.update(overrides)
    return EscalationPolicy.objects.create(org=org, **defaults)


def _create_breached_case(admin_user, org, priority="Urgent", hours_old=5):
    """Create a Case and rewind its created_at so SLAs are breached."""
    case = Case.objects.create(
        name=f"Breached {priority}",
        status="New",
        priority=priority,
        created_by=admin_user,
        org=org,
    )
    Case.objects.filter(pk=case.pk).update(
        created_at=timezone.now() - timedelta(hours=hours_old)
    )
    case.refresh_from_db()
    return case


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestEscalationPolicyModel:
    def test_create_one_per_priority(self, org_a):
        target = _make_target_profile(org_a)
        _make_policy(org_a, target, priority="Urgent")
        # Different priority is fine
        _make_policy(org_a, target, priority="High")
        with pytest.raises(Exception):
            _make_policy(org_a, target, priority="Urgent")  # duplicates collide

    def test_orgs_independent(self, org_a, org_b):
        target_a = _make_target_profile(org_a, "a@x.com")
        target_b = _make_target_profile(org_b, "b@x.com")
        _make_policy(org_a, target_a, priority="Urgent")
        _make_policy(org_b, target_b, priority="Urgent")
        assert EscalationPolicy.objects.filter(org=org_a).count() == 1
        assert EscalationPolicy.objects.filter(org=org_b).count() == 1


# ---------------------------------------------------------------------------
# Admin API
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestEscalationPolicyAPI:
    def test_admin_can_list(self, admin_client, org_a):
        target = _make_target_profile(org_a)
        _make_policy(org_a, target, priority="Urgent")
        response = admin_client.get(POLICIES_URL)
        assert response.status_code == 200
        assert len(response.json()["policies"]) == 1

    def test_user_can_list_but_not_create(self, user_client, admin_client, org_a):
        target = _make_target_profile(org_a)
        # Non-admin GET allowed
        assert user_client.get(POLICIES_URL).status_code == 200
        # Non-admin POST forbidden
        post = user_client.post(
            POLICIES_URL,
            {
                "priority": "Urgent",
                "first_response_action": "notify",
                "resolution_action": "notify",
                "first_response_target_id": str(target.id),
                "resolution_target_id": str(target.id),
            },
            format="json",
        )
        assert post.status_code == 403

    def test_admin_can_create(self, admin_client, org_a):
        target = _make_target_profile(org_a)
        response = admin_client.post(
            POLICIES_URL,
            {
                "priority": "Urgent",
                "first_response_action": "notify_and_reassign",
                "resolution_action": "notify",
                "first_response_target_id": str(target.id),
                "resolution_target_id": str(target.id),
            },
            format="json",
        )
        assert response.status_code == 201, response.content
        policy = EscalationPolicy.objects.get(org=org_a, priority="Urgent")
        assert policy.first_response_action == "notify_and_reassign"

    def test_create_duplicate_priority_rejected(self, admin_client, org_a):
        target = _make_target_profile(org_a)
        _make_policy(org_a, target, priority="Urgent")
        response = admin_client.post(
            POLICIES_URL,
            {
                "priority": "Urgent",
                "first_response_action": "notify",
                "resolution_action": "notify",
                "first_response_target_id": str(target.id),
                "resolution_target_id": str(target.id),
            },
            format="json",
        )
        assert response.status_code == 400

    def test_admin_can_update_action_but_priority_frozen(self, admin_client, org_a):
        target = _make_target_profile(org_a)
        policy = _make_policy(org_a, target, priority="Urgent", first_response_action="notify")
        response = admin_client.put(
            f"{POLICIES_URL}{policy.id}/",
            {"first_response_action": "reassign", "priority": "High"},
            format="json",
        )
        assert response.status_code == 200, response.content
        policy.refresh_from_db()
        assert policy.first_response_action == "reassign"
        assert policy.priority == "Urgent"  # change silently dropped

    def test_admin_can_delete(self, admin_client, org_a):
        target = _make_target_profile(org_a)
        policy = _make_policy(org_a, target, priority="Urgent")
        response = admin_client.delete(f"{POLICIES_URL}{policy.id}/")
        assert response.status_code == 200
        assert not EscalationPolicy.objects.filter(pk=policy.pk).exists()

    def test_cross_org_isolation(self, admin_client, org_a, org_b):
        target_b = _make_target_profile(org_b, "b@x.com")
        _make_policy(org_b, target_b, priority="Urgent")
        # admin_client has org_a — should see no policies
        assert admin_client.get(POLICIES_URL).json()["policies"] == []


# ---------------------------------------------------------------------------
# Scanner task
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestScanForBreachedCases:
    @patch("cases.tasks.send_email_to_assigned_user")
    def test_no_policy_does_not_fire(self, mock_email, admin_user, org_a):
        _create_breached_case(admin_user, org_a)
        assert scan_for_breached_cases() == 0
        assert Activity.objects.filter(action="ESCALATED").count() == 0
        mock_email.delay.assert_not_called()

    @patch("cases.tasks.send_email_to_assigned_user")
    def test_notify_action_fires_once(self, mock_email, admin_user, org_a):
        target = _make_target_profile(org_a)
        _make_policy(
            org_a,
            target,
            priority="Urgent",
            first_response_action="notify",
            resolution_action="notify",
        )
        case = _create_breached_case(admin_user, org_a)

        assert scan_for_breached_cases() == 1
        case.refresh_from_db()
        assert case.escalation_count == 1
        assert case.last_escalation_fired_at is not None

        activity = Activity.objects.get(action="ESCALATED", entity_id=case.pk)
        breach_types = {b["breach_type"] for b in activity.metadata["breaches"]}
        # Both SLAs breached at 5h vs 1/4h limits
        assert breach_types == {"first_response", "resolution"}
        assert mock_email.delay.called

    @patch("cases.tasks.send_email_to_assigned_user")
    def test_reassign_action_replaces_assignee(self, mock_email, admin_user, org_a):
        target = _make_target_profile(org_a)
        other = _make_target_profile(org_a, "other@test.com")
        _make_policy(
            org_a,
            target,
            priority="Urgent",
            first_response_action="reassign",
            resolution_action="reassign",
        )
        case = _create_breached_case(admin_user, org_a)
        case.assigned_to.set([other])

        scan_for_breached_cases()
        case.refresh_from_db()
        assert list(case.assigned_to.all()) == [target]

    @patch("cases.tasks.send_email_to_assigned_user")
    def test_cooldown_prevents_double_fire(self, mock_email, admin_user, org_a):
        target = _make_target_profile(org_a)
        _make_policy(org_a, target, priority="Urgent")
        _create_breached_case(admin_user, org_a)

        scan_for_breached_cases()
        # Second pass within cooldown — no new activity
        assert scan_for_breached_cases() == 0
        assert Activity.objects.filter(action="ESCALATED").count() == 1

    @patch("cases.tasks.send_email_to_assigned_user")
    def test_cap_prevents_runaway_escalation(self, mock_email, admin_user, org_a):
        target = _make_target_profile(org_a)
        _make_policy(org_a, target, priority="Urgent")
        case = _create_breached_case(admin_user, org_a)
        # Pretend it's already at the cap
        Case.objects.filter(pk=case.pk).update(escalation_count=ESCALATION_COUNT_CAP)
        assert scan_for_breached_cases() == 0
        assert Activity.objects.filter(action="ESCALATED").count() == 0

    @patch("cases.tasks.send_email_to_assigned_user")
    def test_terminal_cases_skipped(self, mock_email, admin_user, org_a):
        target = _make_target_profile(org_a)
        _make_policy(org_a, target, priority="Urgent")
        case = _create_breached_case(admin_user, org_a)
        Case.objects.filter(pk=case.pk).update(status="Closed")
        assert scan_for_breached_cases() == 0

    @patch("cases.tasks.send_email_to_assigned_user")
    def test_inactive_policy_skipped(self, mock_email, admin_user, org_a):
        target = _make_target_profile(org_a)
        _make_policy(org_a, target, priority="Urgent", is_active=False)
        _create_breached_case(admin_user, org_a)
        assert scan_for_breached_cases() == 0

    @patch("cases.tasks.send_email_to_assigned_user")
    def test_team_members_added_to_notify_recipients(self, mock_email, admin_user, org_a):
        target = _make_target_profile(org_a, "lead@test.com")
        member = _make_target_profile(org_a, "member@test.com")
        team = Teams.objects.create(name="Tier-2", description="", org=org_a)
        team.users.add(member)
        _make_policy(
            org_a,
            target,
            priority="Urgent",
            first_response_action="notify",
            resolution_action="notify",
            notify_team=team,
        )
        _create_breached_case(admin_user, org_a)
        scan_for_breached_cases()
        # Look at any of the .delay calls — recipients should include both ids
        called_recipients = []
        for call in mock_email.delay.call_args_list:
            called_recipients.extend(call.args[0])
        assert str(target.id) in called_recipients
        assert str(member.id) in called_recipients

    @patch("cases.tasks.send_email_to_assigned_user")
    def test_only_first_response_breached(self, mock_email, admin_user, org_a):
        target = _make_target_profile(org_a)
        _make_policy(org_a, target, priority="Urgent")
        # 2h-old Urgent case: first-response (1h SLA) breached, resolution (4h SLA) NOT
        case = _create_breached_case(admin_user, org_a, hours_old=2)
        assert scan_for_breached_cases() == 1
        activity = Activity.objects.get(action="ESCALATED", entity_id=case.pk)
        breach_types = {b["breach_type"] for b in activity.metadata["breaches"]}
        assert breach_types == {"first_response"}

    @patch("cases.tasks.send_email_to_assigned_user")
    def test_first_response_recorded_skips_after_response(self, mock_email, admin_user, org_a):
        target = _make_target_profile(org_a)
        _make_policy(org_a, target, priority="Urgent")
        case = _create_breached_case(admin_user, org_a)
        Case.objects.filter(pk=case.pk).update(first_response_at=timezone.now())
        case.refresh_from_db()
        scan_for_breached_cases()
        # Resolution still breached (5h vs 4h Urgent SLA), so we still escalate
        # but only the resolution branch.
        activity = Activity.objects.get(action="ESCALATED", entity_id=case.pk)
        breach_types = {b["breach_type"] for b in activity.metadata["breaches"]}
        assert breach_types == {"resolution"}
