from automation.objects import Adapter, FieldSpec, model_choices
from contacts.models import Contact
from contacts.updates import update_contact
from webhooks.events import contact_data


class ContactAdapter(Adapter):
    route = "/contacts/{id}"
    FIELDS = (
        FieldSpec("first_name", "First name", "text"),
        FieldSpec("last_name", "Last name", "text"),
        FieldSpec("email", "Email", "text"),
        FieldSpec("phone", "Phone", "text"),
        FieldSpec("organization", "Company", "text"),
        FieldSpec("title", "Job title", "text"),
        FieldSpec("department", "Department", "text"),
        FieldSpec("city", "City", "text"),
        FieldSpec("country", "Country", "choice", model_choices(Contact, "country")),
        FieldSpec("do_not_call", "Do not call", "boolean"),
        FieldSpec("assigned_to", "Assigned to", "people"),
    )

    def name(self, record):
        full = f"{record.first_name or ''} {record.last_name or ''}".strip()
        return full or record.email or "Unnamed contact"

    def task_parent(self, record):
        return {"contacts": [str(record.pk)]}

    def webhook_data(self, record):
        return contact_data(record)

    def update(self, request, record, data):
        return update_contact(request, record, data)
