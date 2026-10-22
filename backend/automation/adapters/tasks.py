from automation.adapters import same_org
from automation.objects import Adapter, FieldSpec, model_choices
from tasks.models import Task
from tasks.updates import update_task
from webhooks.events import task_data

# A task's parent columns and the object each one points at.
PARENTS = (
    ("lead", "lead"),
    ("account", "account"),
    ("opportunity", "deal"),
    ("case", "ticket"),
)


class TaskAdapter(Adapter):
    route = "/tasks/{id}"
    FIELDS = (
        FieldSpec("title", "Title", "text"),
        FieldSpec("status", "Status", "choice", model_choices(Task, "status")),
        FieldSpec("priority", "Priority", "choice", model_choices(Task, "priority")),
        FieldSpec("due_date", "Due date", "date"),
        FieldSpec("assigned_to", "Assigned to", "people"),
    )

    def name(self, record):
        return record.title

    def parent(self, record):
        for column, key in PARENTS:
            parent = same_org(record, column)
            if parent is not None:
                return key, parent
        return None

    def webhook_data(self, record):
        return task_data(record)

    def update(self, request, record, data):
        return update_task(request, record, data)
