"""Running automation rules on the changes `automation.capture` collects.

`process` takes each change, re-reads its record, and runs every matching
rule of the org on that object in list order. Each rule runs in its own
transaction as its owner and is recorded as an `AutomationRun`. A rule's own
writes are changes of the same chain, processed after it one level deeper,
up to `MAX_DEPTH`; a rule acts on a record once per chain and never on its own
run's writes, and an org runs at most `RUNS_PER_HOUR` rules an hour.
"""

import logging
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field, replace
from datetime import timedelta

from crum import impersonate
from django.core.cache import cache
from django.db import connection, transaction
from django.db.models import Q
from django.utils import timezone

from automation.actions import RunContext, StepFailed, StepSkipped, plan_action
from automation.capture import UPDATED
from automation.conditions import conditions_match, trigger_matches
from automation.limits import MAX_DEPTH, RUNS_PER_HOUR
from automation.models import DONE, FAILED, SKIPPED, AutomationRule, AutomationRun
from automation.objects import adapter_for
from automation.plan import runnable
from automation.serializers import RULE_KEYS
from automation.tasks import prune_org_runs
from automation.validation import active_people, validate_rule
from common import notifications
from common.actor import acting_for
from common.models import Org
from common.permissions import is_org_admin
from common.tasks import set_rls_context

logger = logging.getLogger(__name__)

PLANNED = "planned"
UNDONE = "undone"
SOMETHING_WENT_WRONG = "Something went wrong in this step"
FAILED_VERB = "automation.failed"
LIMIT_VERB = "automation.limit"
SETTINGS_PATH = "/settings/automation"
NOTICE_EVERY = timedelta(hours=24)
PRUNE_EVERY = 24 * 60 * 60
WINDOW_SECONDS = 60 * 60


@dataclass
class Chain:
    """One saved change and every change the rules it sets off go on to make."""

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    # (rule id, record id) pairs a rule has acted on.
    seen: set = field(default_factory=set)
    changes: dict = field(default_factory=dict)
    wrote: bool = False


_chain: ContextVar[Chain | None] = ContextVar("automation_chain", default=None)


class _RuleFailed(Exception):
    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason


def current_chain():
    """The chain a running rule belongs to, or None when no rule is running.

    Capture merges the changes a rule's own writes make into the chain's
    `changes`, a dict keyed by `(object_key, record_id)` like a request's.
    """
    return _chain.get()


def process(changes) -> None:
    """Run the rules each of `changes` sets off. Never raises."""
    for change in changes:
        try:
            with _as_org(change.org_id):
                _start(change)
        except Exception:
            # Logged without the record's data.
            logger.exception("Automation rules could not run for a change")


def try_rule(rule, record, owner=None) -> list[dict]:
    """What each of the rule's actions would do on `record`, writing nothing.

    Plans as the rule's owner, or as `owner` (the admin trying it) when nobody
    has switched it on yet. A rule that no longer validates answers every step
    failed, with that step's own error or else the rule's first.
    """
    org = rule.org
    actions = rule.actions if isinstance(rule.actions, list) else []
    errors = _errors(org, rule)
    if errors:
        first = _first_error(errors)
        return [
            _step(i, action, FAILED, _first_error(errors, f"actions[{i}]") or first)
            for i, action in enumerate(actions)
        ]
    adapter = adapter_for(org, rule.object_key)
    ctx = RunContext(org, rule, record, adapter, rule.owner or owner)
    steps = []
    for index, action in enumerate(actions):
        try:
            text = plan_action(ctx, index, action).text
            steps.append(_step(index, action, PLANNED, text))
        except StepSkipped as exc:
            steps.append(_step(index, action, SKIPPED, exc.text))
        except Exception as exc:
            steps.append(_step(index, action, FAILED, _failure(exc, rule, index)))
    return steps


def notify_failure(rule, reason):
    """Tell the rule's owner it failed, at most once a day per rule."""
    owner = rule.owner
    if owner is None:
        return
    now = timezone.now()
    due = Q(last_failure_notice_at__isnull=True) | Q(
        last_failure_notice_at__lt=now - NOTICE_EVERY
    )
    claimed = AutomationRule.objects.filter(due, org_id=rule.org_id, pk=rule.pk).update(
        last_failure_notice_at=now
    )
    if not claimed:
        return
    notifications.create(
        owner,
        FAILED_VERB,
        entity_name=rule.name[:255],
        link=f"{SETTINGS_PATH}/{rule.pk}",
        data={"rule": rule.name, "rule_id": str(rule.pk), "reason": reason},
    )


@contextmanager
def _as_org(org_id):
    """Run the block with the RLS context set to `org_id`, then restore it."""
    if connection.vendor != "postgresql":
        yield
        return
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_setting('app.current_org', true)")
        previous = cursor.fetchone()[0] or ""
    set_rls_context(org_id)
    try:
        yield
    finally:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT set_config('app.current_org', %s, false)", [previous]
            )


def _start(change):
    org = Org.objects.filter(pk=change.org_id).first()
    if org is None:
        return
    chain = Chain()
    token = _chain.set(chain)
    try:
        _handle(org, chain, change, 1, None, None)
    finally:
        _chain.reset(token)
    if chain.wrote:
        _prune(org)


def _prune(org):
    """Queue deleting the org's expired runs, at most once a day per org.

    Queued, never run here: each deleted run first has its `triggered_by`
    children set null, row by row, and a request must not wait on that.
    """
    org_id = str(org.pk)
    try:
        if cache.add(
            f"automation-prune:{org_id}:{timezone.now().date()}", 1, PRUNE_EVERY
        ):
            transaction.on_commit(lambda: _queue_prune(org_id))
    except Exception:
        logger.exception(
            "Could not queue pruning the automation runs of org %s", org_id
        )


def _queue_prune(org_id):
    try:
        prune_org_runs.delay(org_id)
    except Exception:
        # Not the exception: a broker error can carry the broker's URL.
        logger.warning("Could not queue pruning the automation runs of org %s", org_id)


def _handle(org, chain, change, depth, cause, cause_rule):
    """Run the rules `change` sets off, `depth` deep in `chain`, after run
    `cause` of the rule with id `cause_rule`."""
    adapter = adapter_for(org, change.object_key)
    record = adapter.load(org, change.record_id) if adapter is not None else None
    if record is None:
        return
    change = _confirmed(adapter, record, change)
    if change is None:
        return
    for rule in _rules(org, change.object_key):
        try:
            _consider(org, chain, rule, change, depth, cause, cause_rule)
        except Exception:
            logger.exception("Automation rule %s could not run", rule.pk)


def _confirmed(adapter, record, change):
    """`change` less the fields whose re-read value is not the captured one.

    A write rolled back later in the request, or a save of stale in-memory
    fields, was captured without sticking, so it must not set rules off.
    """
    if change.event != UPDATED:
        return change
    kept = {}
    for key, (old, new) in change.changes.items():
        try:
            if adapter.read(record, key) == new:
                kept[key] = (old, new)
        except KeyError:
            continue
    return replace(change, changes=kept) if kept else None


def _rules(org, object_key):
    """The org's rules on `object_key` that may run, in list order."""
    active = list(
        AutomationRule.objects.filter(org=org, is_active=True, paused_reason="")
        .select_related("owner__user")
        .order_by("position", "created_at")
    )
    allowed = runnable(org, active).rule_ids
    return [r for r in active if r.object_key == object_key and r.id in allowed]


def _may_act(rule):
    """Whether the rule's owner is an active admin of its org."""
    owner = rule.owner
    return (
        owner is not None
        and owner.org_id == rule.org_id
        and owner.is_active
        and owner.user.is_active
        and is_org_admin(owner)
    )


def _consider(org, chain, rule, change, depth, cause, cause_rule):
    if rule.pk == cause_rule:
        return
    if not _may_act(rule) or not trigger_matches(rule.trigger, change):
        return
    if (rule.pk, str(change.record_id)) in chain.seen:
        return
    adapter = adapter_for(org, rule.object_key)
    record = adapter.load(org, change.record_id) if adapter is not None else None
    if record is None:
        return
    # An earlier rule may have moved the record since the change was captured.
    change = _confirmed(adapter, record, change)
    if change is None or not trigger_matches(rule.trigger, change):
        return
    previous = {key: old for key, (old, _) in change.changes.items()}
    values = _values(adapter, record, rule.conditions)
    if not conditions_match(rule.match, rule.conditions, values, previous):
        return
    window = timezone.now().replace(minute=0, second=0, microsecond=0)
    if _runs_since(org, window) >= RUNS_PER_HOUR:
        _skip(org, chain, rule, adapter, record, depth, cause, window)
        return
    chain.seen.add((rule.pk, str(record.pk)))
    ran = _run(org, chain, rule, adapter, record, depth, cause)
    if ran is None or depth >= MAX_DEPTH:
        return
    run_id, produced = ran
    for later in produced.values():
        _handle(org, chain, later, depth + 1, run_id, rule.pk)


def _values(adapter, record, conditions):
    """The record's current values of the fields `conditions` read."""
    values = {}
    for condition in conditions:
        key = condition.get("field")
        if isinstance(key, str) and key not in values:
            try:
                values[key] = adapter.read(record, key)
            except KeyError:
                continue
    return values


def _runs_since(org, window):
    return (
        AutomationRun.objects.filter(org=org, created_at__gte=window)
        .exclude(status=SKIPPED)
        .count()
    )


def _skip(org, chain, rule, adapter, record, depth, cause, window):
    """Count one more run of `rule` past the hourly limit on its row for `window`."""
    with transaction.atomic():
        first = not AutomationRun.objects.filter(
            org=org, status=SKIPPED, window_start=window
        ).exists()
        row, created = AutomationRun.objects.select_for_update().get_or_create(
            org=org,
            rule=rule,
            status=SKIPPED,
            window_start=window,
            defaults={
                "object_key": rule.object_key,
                "record_id": record.pk,
                "record_name": adapter.name(record)[:255],
                "chain_id": chain.id,
                "depth": depth,
                "triggered_by_id": cause,
                "skipped_count": 1,
                "reason": _skipped(1),
            },
        )
        if not created:
            row.skipped_count += 1
            row.reason = _skipped(row.skipped_count)
            row.save(update_fields=["skipped_count", "reason", "updated_at"])
    chain.wrote = True
    # The row check misses another process crossing the limit at the same moment.
    key = f"automation-limit:{org.pk}:{window.isoformat()}"
    if first and cache.add(key, 1, WINDOW_SECONDS):
        data = {"window_start": window.isoformat()}
        for person in active_people(org).select_related("user"):
            if is_org_admin(person):
                notifications.create(person, LIMIT_VERB, link=SETTINGS_PATH, data=data)


def _skipped(count):
    return f"{count} runs skipped: the org reached its hourly limit"


def _run(org, chain, rule, adapter, record, depth, cause):
    """Run `rule` on `record` and record it.

    Answers `(run id, the changes its writes made)` when it is done, or None
    when it failed: then nothing it wrote is kept and its owner is told.
    """
    run_id = uuid.uuid4()
    owner = rule.owner

    def write(status, steps, reason=""):
        AutomationRun.objects.create(
            id=run_id,
            org=org,
            rule=rule,
            object_key=rule.object_key,
            record_id=record.pk,
            record_name=adapter.name(record)[:255],
            status=status,
            reason=reason[:255],
            chain_id=chain.id,
            depth=depth,
            triggered_by_id=cause,
            steps=steps,
        )
        chain.wrote = True

    def fail(steps, reason):
        write(FAILED, steps, reason)
        notify_failure(rule, reason)

    errors = _errors(org, rule)
    if errors:
        fail([], _first_error(errors))
        return None
    ctx = RunContext(org, rule, record, adapter, owner, run_id)
    planned = []
    for index, action in enumerate(rule.actions):
        try:
            planned.append((index, action, plan_action(ctx, index, action)))
        except StepSkipped as exc:
            planned.append((index, action, exc))
        except Exception as exc:
            text = _failure(exc, rule, index)
            fail([_step(index, action, FAILED, text)], text)
            return None

    steps = []
    outer, chain.changes = chain.changes, {}
    try:
        with impersonate(owner.user), acting_for(owner, rule.name):
            try:
                # Written last inside the transaction, so the emails it queues
                # for after the commit find their run.
                with transaction.atomic():
                    _apply(rule, planned, steps)
                    write(DONE, steps)
            except _RuleFailed as failure:
                fail(steps, failure.reason)
                return None
        return run_id, chain.changes
    finally:
        chain.changes = outer


def _apply(rule, planned, steps):
    """Apply each planned step, adding its entry to `steps`; `_RuleFailed` on a failure."""
    for index, action, step in planned:
        if isinstance(step, StepSkipped):
            steps.append(_step(index, action, SKIPPED, step.text))
            continue
        try:
            steps.append(_step(index, action, DONE, step.apply()))
        except StepSkipped as exc:
            steps.append(_step(index, action, SKIPPED, exc.text))
        except Exception as exc:
            text = _failure(exc, rule, index)
            # The rule rolls back, so no step before this one stands.
            for entry in steps:
                if entry["status"] == DONE:
                    entry["status"] = UNDONE
            steps.append(_step(index, action, FAILED, text))
            raise _RuleFailed(text) from exc


def _failure(exc, rule, index):
    """What a step's failure says: its own text, or a plain sentence for a bug."""
    if isinstance(exc, StepFailed):
        return exc.text
    logger.exception("Action %s of automation rule %s broke", index, rule.pk)
    return SOMETHING_WENT_WRONG


def _errors(org, rule):
    return validate_rule(org, {key: getattr(rule, key) for key in RULE_KEYS})


def _first_error(errors, prefix=None):
    """The first error as "path: message", the first under `prefix` if given."""
    for path, messages in errors.items():
        if prefix is None or path == prefix or path.startswith(f"{prefix}."):
            return f"{path}: {messages[0]}"
    return None


def _step(index, action, status, text):
    kind = action.get("type") if isinstance(action, dict) else None
    return {"action": index, "type": kind, "status": status, "text": text}
