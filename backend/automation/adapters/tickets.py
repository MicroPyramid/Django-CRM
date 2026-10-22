from automation.adapters import same_org
from automation.objects import Adapter, FieldSpec, model_choices
from cases.models import Case
from cases.updates import update_case
from webhooks.events import ticket_data


class TicketAdapter(Adapter):
    parent_key = "account"
    route = "/tickets/{id}"
    FIELDS = (
        FieldSpec("name", "Subject", "text"),
        # Duplicate is set only by a merge, which moves the ticket's thread.
        FieldSpec(
            "status",
            "Status",
            "choice",
            model_choices(Case, "status", unsettable={"Duplicate"}),
        ),
        FieldSpec("priority", "Priority", "choice", model_choices(Case, "priority")),
        FieldSpec("case_type", "Type", "choice", model_choices(Case, "case_type")),
        FieldSpec("closed_on", "Closed on", "date"),
        FieldSpec("assigned_to", "Assigned to", "people"),
    )

    def name(self, record):
        return record.name

    def parent(self, record):
        account = same_org(record, "account")
        return ("account", account) if account is not None else None

    def task_parent(self, record):
        return {"case": str(record.pk)}

    def webhook_data(self, record):
        return ticket_data(record)

    def update(self, request, record, data):
        return update_case(request, record, data)
