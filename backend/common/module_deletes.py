"""Deletes that would reach an off module's records answer 409 instead.

While a module is off its records are out of sight, so deleting an account,
ticket or person that would cascade into them, or is blocked by them, names
them rather than destroying them. ``common/tests/test_module_deletes.py`` walks
every model, so a new link into a module cannot be left out of ``DELETE_GUARDS``.
"""

from dataclasses import dataclass

from django.apps import apps
from django.db import models

from common.modules import (
    Requires,
    available_modules,
    model_module,
    module,
    module_label,
    org_of,
)


@dataclass(frozen=True)
class Guard:
    child: str
    field: str
    noun: str
    plural: str


DELETE_GUARDS: dict[str, tuple[Guard, ...]] = {
    "accounts.Account": (
        Guard("cases.Case", "account", "ticket", "tickets"),
        Guard("opportunity.Opportunity", "account", "deal", "deals"),
        Guard("invoices.Invoice", "account", "invoice", "invoices"),
        Guard("invoices.Estimate", "account", "estimate", "estimates"),
        Guard(
            "invoices.RecurringInvoice",
            "account",
            "recurring invoice",
            "recurring invoices",
        ),
    ),
    "cases.Case": (Guard("cases.TimeEntry", "case", "time entry", "time entries"),),
    "common.Profile": (
        Guard("cases.TimeEntry", "profile", "time entry", "time entries"),
        Guard("cases.Approval", "requested_by", "approval", "approvals"),
        Guard("cases.Approval", "approver", "approval", "approvals"),
        Guard("cases.CaseWatcher", "profile", "watched ticket", "watched tickets"),
        Guard("macros.Macro", "owner", "saved reply", "saved replies"),
        Guard("tasks.Board", "owner", "board", "boards"),
        Guard("tasks.BoardMember", "profile", "board membership", "board memberships"),
    ),
}

# The models whose delete views call `delete_refusal`. Any other key above is
# consulted only when deleting one of these cascades into it.
ENTRY_POINTS = frozenset({"accounts.Account", "cases.Case", "common.Profile"})


def _blocking(guard, available):
    """The module keeping ``guard.child`` out of sight: its need first, so a
    time entry hidden by Tickets names Tickets."""
    key = model_module(guard.child)
    needs = module(key).needs
    return Requires((needs, key) if needs else (key,)).blocking(available)


def _rows(guard, parent):
    """``parent`` is the record being deleted, or a queryset of rows its
    delete cascades into."""
    lookup = guard.field if isinstance(parent, models.Model) else f"{guard.field}__in"
    return apps.get_model(guard.child)._base_manager.filter(**{lookup: parent})


def cascades(guard) -> bool:
    """Whether deleting the parent deletes ``guard``'s rows, in Django or in
    the database."""
    field = apps.get_model(guard.child)._meta.get_field(guard.field)
    return field.remote_field.on_delete in (models.CASCADE, models.DB_CASCADE)


def _refusal(org, available, label, parent, subject):
    guards = DELETE_GUARDS.get(label, ())
    for guard in guards:
        key = _blocking(guard, available)
        if key is None:
            continue
        count = _rows(guard, parent).count()
        if count:
            return _body(org, key, subject, guard, count)
    # Rows in an available module that go with the delete can carry rows of an
    # off one: an account's tickets take their time entries with them.
    for guard in guards:
        if _blocking(guard, available) is None and cascades(guard):
            found = _refusal(org, available, guard.child, _rows(guard, parent), subject)
            if found:
                return found
    return None


def _body(org, key, subject, guard, count):
    label = module_label(org, key)
    if count == 1:
        message = (
            f"{subject} has 1 {guard.noun}. {label} is switched off, so switch it "
            "on to review it before deleting."
        )
    else:
        message = (
            f"{subject} has {count} {guard.plural}. {label} is switched off, so "
            "switch it on to review them before deleting."
        )
    return {"error": True, "errors": message, "code": "module_off", "module": key}


def delete_refusal(instance, subject: str) -> dict | None:
    """The 409 body when deleting ``instance`` would reach records of a module
    that is off for its org, else None."""
    org = org_of(instance)
    return _refusal(
        org, available_modules(org), instance._meta.label, instance, subject
    )
