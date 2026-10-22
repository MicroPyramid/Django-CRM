"""The record types the app knows as objects, and what each one supports.

Callers ask the registry which object a target name or a record belongs to,
and read its capability flags, instead of keeping their own per-model lists.
Read rules are not restated here: an entry points at its module's own
`visible_*_qs` by dotted path. Models and rules resolve at call time, never
cached, because those modules import from `common` and a module-level import
would be circular.

An installed app adds per-org entries with `register_hook`. `model_label`,
`read_rule` and `edit_rule` are for the registry's own use. Callers use only
`key`, `label`, `label_plural`, `custom_field_target`, `attachments`,
`activity_feed`, `links`, `model`, `records(org)`, `readable(profile)`,
`editable(profile)` and `automation_adapter()`.
"""

from collections.abc import Callable, Iterable
from dataclasses import dataclass

from django.apps import apps
from django.utils.module_loading import import_string


@dataclass(frozen=True)
class ObjectEntry:
    key: str
    model_label: str
    custom_field_target: str
    read_rule: str
    attachments: bool
    activity_feed: bool
    label: str
    label_plural: str
    links: bool
    edit_rule: str | None
    automation: str | None = None

    @property
    def model(self):
        return apps.get_model(self.model_label)

    def records(self, org):
        return self.model.objects.filter(org=org)

    def readable(self, profile):
        return import_string(self.read_rule)(profile)

    def editable(self, profile):
        if self.edit_rule is None:
            return self.model.objects.none()
        return import_string(self.edit_rule)(profile)

    def automation_adapter(self):
        """What rules use to reach this object's records, or None if they cannot."""
        if self.automation is None:
            return None
        return import_string(self.automation)(self)


class RegistryConflict(Exception):
    pass


_HOOKS = []


BUILT_IN = (
    ObjectEntry(
        "lead",
        "leads.Lead",
        "Lead",
        "leads.access.visible_leads_qs",
        attachments=True,
        activity_feed=True,
        label="Lead",
        label_plural="Leads",
        links=True,
        edit_rule="leads.access.visible_leads_qs",
        automation="automation.adapters.leads.LeadAdapter",
    ),
    ObjectEntry(
        "contact",
        "contacts.Contact",
        "Contact",
        "contacts.access.visible_contacts_qs",
        attachments=True,
        activity_feed=True,
        label="Contact",
        label_plural="Contacts",
        links=True,
        edit_rule="contacts.access.visible_contacts_qs",
        automation="automation.adapters.contacts.ContactAdapter",
    ),
    ObjectEntry(
        "account",
        "accounts.Account",
        "Account",
        "accounts.access.visible_accounts_qs",
        attachments=True,
        activity_feed=True,
        label="Account",
        label_plural="Accounts",
        links=True,
        edit_rule="accounts.access.visible_accounts_qs",
        automation="automation.adapters.accounts.AccountAdapter",
    ),
    ObjectEntry(
        "deal",
        "opportunity.Opportunity",
        "Opportunity",
        "opportunity.access.visible_deals_qs",
        attachments=True,
        activity_feed=True,
        label="Deal",
        label_plural="Deals",
        links=True,
        edit_rule="opportunity.access.visible_deals_qs",
        automation="automation.adapters.deals.DealAdapter",
    ),
    ObjectEntry(
        "ticket",
        "cases.Case",
        "Case",
        "cases.access.visible_cases_qs",
        attachments=True,
        activity_feed=True,
        label="Ticket",
        label_plural="Tickets",
        links=True,
        edit_rule="cases.access.writable_cases_qs",
        automation="automation.adapters.tickets.TicketAdapter",
    ),
    ObjectEntry(
        "task",
        "tasks.Task",
        "Task",
        "tasks.access.visible_tasks_qs",
        attachments=True,
        activity_feed=True,
        label="Task",
        label_plural="Tasks",
        links=True,
        edit_rule="tasks.access.visible_tasks_qs",
        automation="automation.adapters.tasks.TaskAdapter",
    ),
    ObjectEntry(
        "invoice",
        "invoices.Invoice",
        "Invoice",
        "invoices.permissions.visible_invoices_qs",
        attachments=True,
        activity_feed=True,
        label="Invoice",
        label_plural="Invoices",
        links=False,
        edit_rule=None,
    ),
    ObjectEntry(
        "estimate",
        "invoices.Estimate",
        "Estimate",
        "invoices.permissions.visible_estimates_qs",
        attachments=False,
        activity_feed=False,
        label="Estimate",
        label_plural="Estimates",
        links=False,
        edit_rule=None,
    ),
    ObjectEntry(
        "recurring_invoice",
        "invoices.RecurringInvoice",
        "RecurringInvoice",
        "invoices.permissions.visible_recurring_qs",
        attachments=False,
        activity_feed=False,
        label="Recurring invoice",
        label_plural="Recurring invoices",
        links=False,
        edit_rule=None,
    ),
)


def all_objects(org):
    """BUILT_IN, then each hook's entries for `org`; no hook runs when org is None."""
    entries = BUILT_IN
    if org is not None:
        extra = [e for hook in _HOOKS for e in hook(org)]
        entries = (*BUILT_IN, *extra)
    seen_keys, seen_targets = set(), set()
    for entry in entries:
        for seen, value in (
            (seen_keys, entry.key),
            (seen_targets, entry.custom_field_target),
        ):
            if value in seen:
                raise RegistryConflict(f"{value!r} is registered twice")
            seen.add(value)
    return entries


def register_hook(hook: Callable[[object], Iterable]) -> None:
    if hook not in _HOOKS:
        _HOOKS.append(hook)


def object_for_key(org, key):
    return next((e for e in all_objects(org) if e.key == key), None)


def object_for_target(org, target):
    return next((e for e in all_objects(org) if e.custom_field_target == target), None)


def object_for_record(org, content_type, object_id):
    """The entry the record at `content_type` and `object_id` belongs to.

    One entry on the content type is decided with no query. When several share
    it (one model holding many objects), the one whose records hold the id wins.
    Never calls `content_type.model_class()`, which is None for a model that is
    gone.
    """
    matches = [
        e
        for e in all_objects(org)
        if (e.model._meta.app_label, e.model._meta.model_name)
        == (content_type.app_label, content_type.model)
    ]
    if len(matches) <= 1:
        return matches[0] if matches else None
    return next(
        (e for e in matches if e.records(org).filter(pk=object_id).exists()), None
    )
