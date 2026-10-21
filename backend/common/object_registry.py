"""The record types the app knows as objects, and what each one supports.

Callers ask the registry which object a target name or a record belongs to,
and read its capability flags, instead of keeping their own per-model lists.
Read rules are not restated here: an entry points at its module's own
`visible_*_qs` by dotted path. Models and rules resolve at call time, never
cached, because those modules import from `common` and a module-level import
would be circular.

`model_label` and `read_rule` are for the registry's own use. Callers use only
`key`, `custom_field_target`, `attachments`, `activity_feed`, `model`,
`records()` and `readable()`.
"""

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

    @property
    def model(self):
        return apps.get_model(self.model_label)

    def records(self, org):
        return self.model.objects.filter(org=org)

    def readable(self, profile):
        return import_string(self.read_rule)(profile)


BUILT_IN = (
    ObjectEntry(
        "lead",
        "leads.Lead",
        "Lead",
        "leads.access.visible_leads_qs",
        attachments=True,
        activity_feed=True,
    ),
    ObjectEntry(
        "contact",
        "contacts.Contact",
        "Contact",
        "contacts.access.visible_contacts_qs",
        attachments=True,
        activity_feed=True,
    ),
    ObjectEntry(
        "account",
        "accounts.Account",
        "Account",
        "accounts.access.visible_accounts_qs",
        attachments=True,
        activity_feed=True,
    ),
    ObjectEntry(
        "deal",
        "opportunity.Opportunity",
        "Opportunity",
        "opportunity.access.visible_deals_qs",
        attachments=True,
        activity_feed=True,
    ),
    ObjectEntry(
        "ticket",
        "cases.Case",
        "Case",
        "cases.access.visible_cases_qs",
        attachments=True,
        activity_feed=True,
    ),
    ObjectEntry(
        "task",
        "tasks.Task",
        "Task",
        "tasks.access.visible_tasks_qs",
        attachments=True,
        activity_feed=True,
    ),
    ObjectEntry(
        "invoice",
        "invoices.Invoice",
        "Invoice",
        "invoices.permissions.visible_invoices_qs",
        attachments=True,
        activity_feed=True,
    ),
    ObjectEntry(
        "estimate",
        "invoices.Estimate",
        "Estimate",
        "invoices.permissions.visible_estimates_qs",
        attachments=False,
        activity_feed=False,
    ),
    ObjectEntry(
        "recurring_invoice",
        "invoices.RecurringInvoice",
        "RecurringInvoice",
        "invoices.permissions.visible_recurring_qs",
        attachments=False,
        activity_feed=False,
    ),
)


def all_objects(org):
    return BUILT_IN


def object_for_target(org, target):
    return next((e for e in all_objects(org) if e.custom_field_target == target), None)


def object_for_record(org, content_type, object_id):
    """The entry the record at `content_type` and `object_id` belongs to.

    The record id is in the signature because built-ins are decided by content
    type alone, but from step 2 one content type (`CustomRecord`) holds many
    objects, so the record decides. Never calls `content_type.model_class()`,
    which is None for a model that is gone.
    """
    for entry in all_objects(org):
        meta = entry.model._meta
        if (meta.app_label, meta.model_name) == (
            content_type.app_label,
            content_type.model,
        ):
            return entry
    return None
