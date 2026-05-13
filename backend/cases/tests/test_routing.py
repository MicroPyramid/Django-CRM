"""Auto-routing tests: engine, signal-on-create, admin API, and dry-run endpoint.

See docs/cases/tier1/auto-routing.md.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from django.utils import timezone

from cases.inbound.parser import ParsedEmail
from cases.inbound.pipeline import ingest
from cases.models import (
    Case,
    InboundMailbox,
    RoutingRule,
    RoutingRuleState,
)
from cases.routing import RoutingDecision, _matches_all, evaluate
from common.models import Activity, Profile, Tags, Teams, User

RULES_URL = "/api/cases/routing-rules/"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _profile(org, email):
    user = User.objects.create_user(email=email, password="x")
    return Profile.objects.create(user=user, org=org, role="USER", is_active=True)


def _rule(org, name, **kwargs):
    assignees = kwargs.pop("target_assignees", [])
    rule = RoutingRule.objects.create(
        org=org,
        name=name,
        priority_order=kwargs.pop("priority_order", 100),
        is_active=kwargs.pop("is_active", True),
        conditions=kwargs.pop("conditions", []),
        strategy=kwargs.pop("strategy", "direct"),
        stop_processing=kwargs.pop("stop_processing", True),
        target_team=kwargs.pop("target_team", None),
    )
    if assignees:
        rule.target_assignees.set(assignees)
    return rule


def _case(org, **kwargs):
    defaults = {
        "name": "Auto-routed case",
        "status": "New",
        "priority": "Normal",
        "org": org,
    }
    defaults.update(kwargs)
    return Case.objects.create(**defaults)


# ---------------------------------------------------------------------------
# Condition matching (pure-function tests)
# ---------------------------------------------------------------------------


class TestConditionMatching:
    def test_eq_priority(self):
        data = {"priority": "Urgent", "case_type": None, "tags": [], "custom_fields": {}}
        assert _matches_all(data, [{"field": "priority", "op": "eq", "value": "Urgent"}])
        assert not _matches_all(
            data, [{"field": "priority", "op": "eq", "value": "Low"}]
        )

    def test_in_op(self):
        data = {"priority": "High", "tags": []}
        assert _matches_all(
            data, [{"field": "priority", "op": "in", "value": ["High", "Urgent"]}]
        )
        assert not _matches_all(
            data, [{"field": "priority", "op": "in", "value": ["Low"]}]
        )

    def test_tag_eq_membership(self):
        data = {"tags": ["billing", "vip"]}
        assert _matches_all(data, [{"field": "tags", "op": "eq", "value": "billing"}])
        assert not _matches_all(
            data, [{"field": "tags", "op": "eq", "value": "shipping"}]
        )

    def test_contains_op_string(self):
        data = {"case_type": "Billing question"}
        assert _matches_all(
            data, [{"field": "case_type", "op": "contains", "value": "Billing"}]
        )

    def test_regex_op(self):
        data = {"from_email_domain": "alpha.example.com"}
        assert _matches_all(
            data,
            [{"field": "from_email_domain", "op": "regex", "value": r"^alpha\."}],
        )

    def test_custom_field_lookup(self):
        data = {"custom_fields": {"severity": "S1"}}
        assert _matches_all(
            data,
            [{"field": "custom_fields.severity", "op": "eq", "value": "S1"}],
        )
        assert not _matches_all(
            data,
            [{"field": "custom_fields.severity", "op": "eq", "value": "S2"}],
        )

    def test_unknown_field_skips(self):
        # Unknown field returns False (no match) but does not raise.
        assert not _matches_all(
            {}, [{"field": "totally_made_up", "op": "eq", "value": "x"}]
        )

    def test_and_semantics(self):
        data = {"priority": "Urgent", "tags": ["billing"]}
        # Both match → True
        assert _matches_all(
            data,
            [
                {"field": "priority", "op": "eq", "value": "Urgent"},
                {"field": "tags", "op": "eq", "value": "billing"},
            ],
        )
        # One fails → False
        assert not _matches_all(
            data,
            [
                {"field": "priority", "op": "eq", "value": "Urgent"},
                {"field": "tags", "op": "eq", "value": "shipping"},
            ],
        )

    def test_empty_conditions_match(self):
        # No conditions → "match all"
        assert _matches_all({"priority": "x"}, [])


# ---------------------------------------------------------------------------
# Strategy execution
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestStrategies:
    def test_direct_assigns_first_pool_member(self, org_a):
        agent = _profile(org_a, "direct@a.com")
        _rule(org_a, "Direct rule", strategy="direct", target_assignees=[agent])
        case = _case(org_a, priority="High")
        case.refresh_from_db()
        assignees = list(case.assigned_to.values_list("id", flat=True))
        assert agent.id in assignees
        # Activity row recorded.
        assert Activity.objects.filter(
            entity_type="Case", entity_id=case.pk, action="ROUTED"
        ).exists()

    def test_round_robin_advances_cursor(self, org_a):
        a1 = _profile(org_a, "rr1@a.com")
        a2 = _profile(org_a, "rr2@a.com")
        a3 = _profile(org_a, "rr3@a.com")
        _rule(
            org_a,
            "RR rule",
            strategy="round_robin",
            target_assignees=[a1, a2, a3],
        )
        cases = [_case(org_a, name=f"rr-{i}") for i in range(4)]
        # The pool ordering is by Profile.id; collect that order.
        ordered_pool = list(
            Profile.objects.filter(id__in=[a1.id, a2.id, a3.id]).order_by("id")
        )
        chosen = []
        for c in cases:
            c.refresh_from_db()
            chosen.append(list(c.assigned_to.all())[0].id)
        # Index sequence is 0,1,2,0 (modulo) regardless of which Profile came first.
        expected_ids = [
            ordered_pool[0].id,
            ordered_pool[1].id,
            ordered_pool[2].id,
            ordered_pool[0].id,
        ]
        assert chosen == expected_ids

    def test_least_busy_picks_freest_agent(self, org_a):
        a1 = _profile(org_a, "lb1@a.com")
        a2 = _profile(org_a, "lb2@a.com")
        # Stack 3 open cases on a1.
        for i in range(3):
            c = _case(org_a, name=f"prefill-{i}", priority="Low")
            c.assigned_to.add(a1)
        _rule(
            org_a,
            "LB rule",
            strategy="least_busy",
            target_assignees=[a1, a2],
        )
        case = _case(org_a, name="lb-target", priority="Urgent")
        case.refresh_from_db()
        assignees = list(case.assigned_to.values_list("id", flat=True))
        assert a2.id in assignees
        assert a1.id not in assignees

    def test_by_team_assigns_team(self, org_a):
        team = Teams.objects.create(name="Billing", org=org_a)
        _rule(org_a, "By team rule", strategy="by_team", target_team=team)
        case = _case(org_a, name="team-target", priority="High")
        case.refresh_from_db()
        team_ids = list(case.teams.values_list("id", flat=True))
        assert team.id in team_ids

    def test_priority_order_first_match_wins(self, org_a):
        first_agent = _profile(org_a, "first@a.com")
        second_agent = _profile(org_a, "second@a.com")
        # Lower priority_order runs first.
        _rule(
            org_a,
            "Second",
            priority_order=200,
            strategy="direct",
            target_assignees=[second_agent],
        )
        _rule(
            org_a,
            "First",
            priority_order=10,
            strategy="direct",
            target_assignees=[first_agent],
        )
        case = _case(org_a, name="ordering-target")
        case.refresh_from_db()
        ids = list(case.assigned_to.values_list("id", flat=True))
        assert first_agent.id in ids
        assert second_agent.id not in ids

    def test_stop_processing_false_continues(self, org_a):
        a1 = _profile(org_a, "stop1@a.com")
        a2 = _profile(org_a, "stop2@a.com")
        _rule(
            org_a,
            "Match all but don't stop",
            priority_order=10,
            strategy="direct",
            target_assignees=[a1],
            stop_processing=False,
        )
        _rule(
            org_a,
            "Lower priority match",
            priority_order=20,
            strategy="direct",
            target_assignees=[a2],
            stop_processing=True,
        )
        case = _case(org_a, name="dual-routed")
        case.refresh_from_db()
        # Both rules matched; both assignees are added.
        ids = set(case.assigned_to.values_list("id", flat=True))
        assert a1.id in ids
        assert a2.id in ids

    def test_empty_pool_falls_through(self, org_a):
        a1 = _profile(org_a, "fallthrough@a.com")
        # Rule 1 has no assignees → empty pool → reason recorded but no assignment.
        empty_rule = RoutingRule.objects.create(
            org=org_a,
            name="empty",
            priority_order=10,
            strategy="direct",
            stop_processing=False,
        )
        _rule(
            org_a,
            "Catch-all",
            priority_order=20,
            strategy="direct",
            target_assignees=[a1],
        )
        case = _case(org_a, name="empty-pool-case")
        case.refresh_from_db()
        ids = set(case.assigned_to.values_list("id", flat=True))
        assert a1.id in ids
        # First rule recorded an empty_pool Activity.
        empty_activity = Activity.objects.filter(
            entity_type="Case",
            entity_id=case.pk,
            action="ROUTED",
            metadata__rule_id=str(empty_rule.id),
        ).first()
        assert empty_activity is not None
        assert empty_activity.metadata.get("reason") == "empty_pool"

    def test_inactive_rules_ignored(self, org_a):
        agent = _profile(org_a, "inactive@a.com")
        _rule(
            org_a,
            "Disabled rule",
            strategy="direct",
            target_assignees=[agent],
            is_active=False,
        )
        case = _case(org_a, name="inactive-rule-case")
        case.refresh_from_db()
        assert case.assigned_to.count() == 0
        assert not Activity.objects.filter(
            entity_type="Case", entity_id=case.pk, action="ROUTED"
        ).exists()


# ---------------------------------------------------------------------------
# Conditional matching against Case fields (integration)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestConditionsAgainstCase:
    def test_priority_eq_condition_routes(self, org_a):
        agent = _profile(org_a, "urg@a.com")
        _rule(
            org_a,
            "Urgent only",
            strategy="direct",
            target_assignees=[agent],
            conditions=[{"field": "priority", "op": "eq", "value": "Urgent"}],
        )
        # Non-urgent: no routing.
        c1 = _case(org_a, name="not-urgent", priority="High")
        c1.refresh_from_db()
        assert c1.assigned_to.count() == 0
        # Urgent: routed.
        c2 = _case(org_a, name="urgent", priority="Urgent")
        c2.refresh_from_db()
        assert agent.id in list(c2.assigned_to.values_list("id", flat=True))

    def test_custom_field_severity_routes(self, org_a):
        agent = _profile(org_a, "s1@a.com")
        _rule(
            org_a,
            "S1 routes",
            strategy="direct",
            target_assignees=[agent],
            conditions=[
                {"field": "custom_fields.severity", "op": "eq", "value": "S1"}
            ],
        )
        case = _case(
            org_a,
            name="severity-s1",
            custom_fields={"severity": "S1"},
        )
        case.refresh_from_db()
        assert agent.id in list(case.assigned_to.values_list("id", flat=True))


# ---------------------------------------------------------------------------
# Inbound email integration: routing reads mailbox_id + from_email_domain
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestInboundIntegration:
    def _mailbox(self, org_a):
        return InboundMailbox.objects.create(
            org=org_a, address="support@example.com", provider="ses"
        )

    def _parsed(self, mailbox, message_id="<rt-1@example.com>"):
        return ParsedEmail(
            raw_headers={},
            message_id=message_id,
            in_reply_to="",
            references=[],
            from_address="vip@bigco.com",
            from_display_name="VIP",
            to_addresses=[mailbox.address],
            cc_addresses=[],
            subject="Help me",
            body_text="please",
            body_html="",
            received_at=timezone.now(),
            attachments=[],
            is_bounce=False,
        )

    def test_inbound_routes_on_from_domain(self, org_a):
        agent = _profile(org_a, "vip@a.com")
        _rule(
            org_a,
            "VIP domain",
            strategy="direct",
            target_assignees=[agent],
            conditions=[
                {
                    "field": "from_email_domain",
                    "op": "eq",
                    "value": "bigco.com",
                }
            ],
        )
        mailbox = self._mailbox(org_a)
        result = ingest(self._parsed(mailbox), mailbox)
        assert result.created_case
        case = result.case
        case.refresh_from_db()
        assert agent.id in list(case.assigned_to.values_list("id", flat=True))

    def test_inbound_routes_on_mailbox_id(self, org_a):
        agent = _profile(org_a, "mbx@a.com")
        mailbox = self._mailbox(org_a)
        _rule(
            org_a,
            "Mailbox routing",
            strategy="direct",
            target_assignees=[agent],
            conditions=[
                {"field": "mailbox_id", "op": "eq", "value": str(mailbox.id)}
            ],
        )
        result = ingest(self._parsed(mailbox), mailbox)
        assert result.created_case
        case = result.case
        case.refresh_from_db()
        assert agent.id in list(case.assigned_to.values_list("id", flat=True))


# ---------------------------------------------------------------------------
# Admin API
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestRoutingRuleAPI:
    def test_admin_can_list_create_update_delete(
        self, admin_client, admin_profile, org_a
    ):
        agent = _profile(org_a, "api1@a.com")
        # Create
        resp = admin_client.post(
            RULES_URL,
            data={
                "name": "Urgent",
                "priority_order": 10,
                "strategy": "direct",
                "conditions": [
                    {"field": "priority", "op": "eq", "value": "Urgent"}
                ],
                "target_assignee_ids": [str(agent.id)],
            },
            content_type="application/json",
        )
        assert resp.status_code == 201, resp.content
        rule_id = resp.json()["id"]
        # List
        resp = admin_client.get(RULES_URL)
        assert resp.status_code == 200
        names = [r["name"] for r in resp.json()["rules"]]
        assert "Urgent" in names
        # Update
        resp = admin_client.put(
            f"{RULES_URL}{rule_id}/",
            data={"priority_order": 5},
            content_type="application/json",
        )
        assert resp.status_code == 200
        # Delete
        resp = admin_client.delete(f"{RULES_URL}{rule_id}/")
        assert resp.status_code == 200

    def test_user_create_forbidden(self, user_client, org_a):
        agent = _profile(org_a, "api2@a.com")
        resp = user_client.post(
            RULES_URL,
            data={
                "name": "x",
                "strategy": "direct",
                "target_assignee_ids": [str(agent.id)],
            },
            content_type="application/json",
        )
        assert resp.status_code == 403

    def test_create_rejects_unknown_op(self, admin_client, org_a):
        agent = _profile(org_a, "api3@a.com")
        resp = admin_client.post(
            RULES_URL,
            data={
                "name": "bad",
                "strategy": "direct",
                "conditions": [
                    {"field": "priority", "op": "starts_with", "value": "U"}
                ],
                "target_assignee_ids": [str(agent.id)],
            },
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_test_endpoint_is_dry_run(self, admin_client, admin_profile, org_a):
        agent = _profile(org_a, "test-ep@a.com")
        rule = _rule(
            org_a,
            "RR for dry-run",
            strategy="round_robin",
            target_assignees=[agent],
            conditions=[
                {"field": "priority", "op": "eq", "value": "Urgent"}
            ],
        )
        # Build a Case the rule would match.
        case = _case(org_a, name="dryrun", priority="Urgent")
        # Reset state and assignment so we can verify dry-run doesn't mutate.
        case.assigned_to.clear()
        RoutingRuleState.objects.filter(rule=rule).update(last_assigned_index=0)
        Activity.objects.filter(
            entity_type="Case", entity_id=case.pk, action="ROUTED"
        ).delete()

        resp = admin_client.post(
            f"{RULES_URL}{rule.id}/test/",
            data={"case_id": str(case.id)},
            content_type="application/json",
        )
        assert resp.status_code == 200, resp.content
        body = resp.json()
        assert body["matched"] is True
        assert body["rule_name"] == "RR for dry-run"
        assert str(agent.id) in body["would_assign_profile_ids"]
        # No state change.
        case.refresh_from_db()
        assert case.assigned_to.count() == 0
        state = RoutingRuleState.objects.filter(rule=rule).first()
        assert state is None or state.last_assigned_index == 0

    def test_cross_org_isolation(self, admin_client, org_a, org_b):
        # A rule in org_b is invisible to org_a's admin client.
        other_agent = _profile(org_b, "other@b.com")
        _rule(
            org_b,
            "Other-org rule",
            strategy="direct",
            target_assignees=[other_agent],
        )
        resp = admin_client.get(RULES_URL)
        assert resp.status_code == 200
        names = [r["name"] for r in resp.json()["rules"]]
        assert "Other-org rule" not in names
