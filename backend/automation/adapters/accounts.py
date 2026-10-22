from accounts.models import Account
from accounts.updates import update_account
from automation.objects import Adapter, FieldSpec, model_choices
from webhooks.events import account_data


class AccountAdapter(Adapter):
    route = "/accounts/{id}"
    FIELDS = (
        FieldSpec("name", "Name", "text"),
        FieldSpec("email", "Email", "text"),
        FieldSpec("phone", "Phone", "text"),
        FieldSpec("website", "Website", "text"),
        FieldSpec("city", "City", "text"),
        FieldSpec("country", "Country", "choice", model_choices(Account, "country")),
        FieldSpec("industry", "Industry", "choice", model_choices(Account, "industry")),
        FieldSpec("number_of_employees", "Employees", "number"),
        FieldSpec("annual_revenue", "Annual revenue", "number"),
        FieldSpec("assigned_to", "Assigned to", "people"),
    )

    def name(self, record):
        return record.name

    def task_parent(self, record):
        return {"account": str(record.pk)}

    def webhook_data(self, record):
        return account_data(record)

    def update(self, request, record, data):
        return update_account(request, record, data)
