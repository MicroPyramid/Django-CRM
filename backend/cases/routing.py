"""Auto-routing engine for newly created Cases.

See docs/cases/tier1/auto-routing.md.

Public API:
    evaluate(case, *, dry_run=False) -> RoutingDecision

The evaluator is invoked synchronously from `cases.signals` (post_save on
Case, created=True) and from `cases.inbound.pipeline` after email-to-ticket
creates a Case. It runs inside the caller's transaction, so the assignment is
committed atomically with the Case row.

`dry_run=True` runs the same matching/strategy logic but does NOT mutate
state — used by the `test/` API endpoint to preview which agent a sample Case
would route to.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Iterable

from django.db import connection, transaction
from django.db.models import Count, Q

from cases.models import RoutingRule, RoutingRuleState
from cases.workflow import TERMINAL_STATUSES
from common.models import Activity, Profile

logger = logging.getLogger(__name__)


SUPPORTED_OPS = {"eq", "in", "contains", "regex"}
SUPPORTED_FIELDS = {
    "priority",
    "case_type",
    "account",  # account_id (uuid as string)
    "tags",  # any tag name in the list
    "from_email_domain",
    "mailbox_id",
}
# `custom_fields.<key>` is matched dynamically.


@dataclass
class RoutingDecision:
    matched_rule_id: str | None = None
    matched_rule_name: str = ""
    strategy: str = ""
    assigned_profile_ids: list[str] = field(default_factory=list)
    assigned_team_id: str | None = None
    reason: str = ""  # populated when matched but pool was empty / etc.


# ---------------------------------------------------------------------------
# Condition matching
# ---------------------------------------------------------------------------


def _resolve_field(case_data: dict, field: str):
    """Pull the relevant value off the case context for `field`.

    `case_data` is a dict produced by `_case_to_dict` (or supplied by the test
    endpoint) so this function works for both real Case rows and dry-run input.
    """
    if field.startswith("custom_fields."):
        key = field[len("custom_fields.") :]
        return (case_data.get("custom_fields") or {}).get(key)
    if field == "account":
        return case_data.get("account_id")
    if field == "tags":
        return list(case_data.get("tags") or [])
    return case_data.get(field)


def _match_condition(case_data: dict, condition: dict) -> bool:
    f = condition.get("field")
    op = condition.get("op", "eq")
    value = condition.get("value")
    if op not in SUPPORTED_OPS:
        logger.warning("RoutingRule unknown op %r — skipping condition", op)
        return False
    if not (f in SUPPORTED_FIELDS or f.startswith("custom_fields.")):
        logger.warning("RoutingRule unknown field %r — skipping condition", f)
        return False
    actual = _resolve_field(case_data, f)

    if op == "eq":
        if isinstance(actual, list):
            return value in actual
        return _coerce(actual) == _coerce(value)
    if op == "in":
        if not isinstance(value, (list, tuple)):
            return False
        coerced_value = [_coerce(v) for v in value]
        if isinstance(actual, list):
            return any(_coerce(a) in coerced_value for a in actual)
        return _coerce(actual) in coerced_value
    if op == "contains":
        if actual is None:
            return False
        if isinstance(actual, list):
            return _coerce(value) in [_coerce(a) for a in actual]
        return str(value) in str(actual)
    if op == "regex":
        if actual is None:
            return False
        try:
            pattern = re.compile(str(value))
        except re.error:
            return False
        if isinstance(actual, list):
            return any(pattern.search(str(a)) for a in actual)
        return bool(pattern.search(str(actual)))
    return False


def _coerce(v):
    """Best-effort type coercion for the eq/in cases. UUIDs come through as
    str everywhere, so we just stringify non-None scalars."""
    if v is None:
        return None
    if isinstance(v, (int, bool)):
        return v
    return str(v)


def _matches_all(case_data: dict, conditions: list[dict]) -> bool:
    for cond in conditions or []:
        try:
            if not _match_condition(case_data, cond):
                return False
        except Exception:
            logger.exception("RoutingRule condition raised; treating as no-match")
            return False
    return True


# ---------------------------------------------------------------------------
# Strategy execution
# ---------------------------------------------------------------------------


def _active_pool(rule: RoutingRule) -> list[Profile]:
    return list(
        rule.target_assignees.filter(is_active=True).order_by("id")
    )


def _least_busy(profiles: Iterable[Profile]) -> Profile | None:
    profiles = list(profiles)
    if not profiles:
        return None
    counts = (
        Profile.objects.filter(id__in=[p.id for p in profiles])
        .annotate(
            open_cases=Count(
                "case_assigned_users",
                filter=~Q(case_assigned_users__status__in=TERMINAL_STATUSES)
                & Q(case_assigned_users__is_active=True),
            )
        )
        .values("id", "open_cases")
    )
    by_id = {row["id"]: row["open_cases"] for row in counts}
    profiles.sort(key=lambda p: (by_id.get(p.id, 0), str(p.id)))
    return profiles[0]


def _round_robin(rule: RoutingRule, pool: list[Profile], dry_run: bool) -> Profile | None:
    if not pool:
        return None
    if dry_run:
        # Don't take a row lock; just preview the next agent without advancing.
        state = RoutingRuleState.objects.filter(rule=rule).first()
        idx = (state.last_assigned_index if state else 0) % len(pool)
        return pool[idx]

    with transaction.atomic():
        state = (
            RoutingRuleState.objects.select_for_update()
            .filter(rule=rule)
            .first()
        )
        if state is None:
            state = RoutingRuleState.objects.create(
                rule=rule, org=rule.org, last_assigned_index=0
            )
        idx = state.last_assigned_index % len(pool)
        chosen = pool[idx]
        state.last_assigned_index = (idx + 1) % max(len(pool), 1)
        state.save(update_fields=["last_assigned_index", "updated_at"])
        return chosen


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def _case_to_dict(case) -> dict:
    """Snapshot the fields the engine reads — keeps real Case + synthetic
    dicts behind the same shape.

    The inbound pipeline attaches `_routing_mailbox_id` and
    `_routing_from_domain` on the Case instance before save so the post_save
    signal can match on email-only fields without a separate query.
    """
    tag_names = []
    if case.pk:
        try:
            tag_names = list(case.tags.values_list("name", flat=True))
        except ValueError:
            tag_names = []
    from_domain = getattr(case, "_routing_from_domain", "") or ""
    if not from_domain and case.pk:
        contact = case.contacts.first()
        if contact and contact.email and "@" in contact.email:
            from_domain = contact.email.split("@", 1)[1].lower()
    mailbox_id = getattr(case, "_routing_mailbox_id", None)
    return {
        "priority": case.priority,
        "case_type": case.case_type,
        "account_id": str(case.account_id) if case.account_id else None,
        "tags": tag_names,
        "custom_fields": case.custom_fields or {},
        "from_email_domain": from_domain.lower() if from_domain else "",
        "mailbox_id": str(mailbox_id) if mailbox_id else None,
    }


def evaluate(case, *, dry_run: bool = False, case_data: dict | None = None) -> RoutingDecision:
    """Evaluate active routing rules for `case.org` against the case.

    Walks rules in `priority_order` ASC. The first matching rule executes its
    strategy and (when `stop_processing=True`) ends the walk. On a dry run,
    no Activity row is written and round_robin does not advance its cursor.
    """
    org_id = case.org_id
    rules = list(
        RoutingRule.objects.filter(org_id=org_id, is_active=True)
        .order_by("priority_order", "created_at")
        .prefetch_related("target_assignees")
    )
    if not rules:
        return RoutingDecision()

    if case_data is None:
        case_data = _case_to_dict(case)

    decision = RoutingDecision()

    for rule in rules:
        if not _matches_all(case_data, rule.conditions or []):
            continue

        decision.matched_rule_id = str(rule.id)
        decision.matched_rule_name = rule.name
        decision.strategy = rule.strategy

        chosen_profile = None
        pool = _active_pool(rule)

        if rule.strategy == "by_team":
            if rule.target_team_id is None:
                decision.reason = "missing_team"
            else:
                decision.assigned_team_id = str(rule.target_team_id)
        elif rule.strategy == "direct":
            if not pool:
                decision.reason = "empty_pool"
            else:
                chosen_profile = pool[0]
        elif rule.strategy == "least_busy":
            if not pool:
                decision.reason = "empty_pool"
            else:
                chosen_profile = _least_busy(pool)
        elif rule.strategy == "round_robin":
            if not pool:
                decision.reason = "empty_pool"
            else:
                chosen_profile = _round_robin(rule, pool, dry_run=dry_run)

        if chosen_profile is not None:
            decision.assigned_profile_ids = [str(chosen_profile.id)]

        if not dry_run:
            _apply(case, rule, chosen_profile, decision)

        if rule.stop_processing:
            return decision
        # otherwise: keep evaluating but accumulate later matches by
        # overwriting; only the last applied rule "wins" for the decision
        # return value.

    return decision


def _apply(case, rule: RoutingRule, chosen_profile: Profile | None, decision: RoutingDecision):
    """Persist assignment + write an Activity(ROUTED) row.

    No-ops if the rule matched but produced no target (empty pool / missing
    team). The Activity row still records the match so admins can see the
    rule fired.
    """
    if chosen_profile is not None:
        case.assigned_to.add(chosen_profile)
    if rule.strategy == "by_team" and rule.target_team_id is not None:
        case.teams.add(rule.target_team_id)

    metadata = {
        "rule_id": str(rule.id),
        "rule_name": rule.name,
        "strategy": rule.strategy,
    }
    if chosen_profile is not None:
        metadata["target_profile_id"] = str(chosen_profile.id)
    if rule.strategy == "by_team":
        metadata["target_team_id"] = (
            str(rule.target_team_id) if rule.target_team_id else None
        )
    if decision.reason:
        metadata["reason"] = decision.reason

    Activity.objects.create(
        user=None,
        action="ROUTED",
        entity_type="Case",
        entity_id=case.pk,
        entity_name=str(case)[:255],
        metadata=metadata,
        org_id=case.org_id,
    )
