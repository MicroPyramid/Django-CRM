"""One path each for creating a task and for editing one that exists.

The task views (`TaskListView.post`, `TaskDetailView.patch`) and automation
rules write through `create_task` and `update_task`, so a gate added here
holds for all of them, as `cases.updates.update_case` does for tickets.

Authorization is the caller's job and happens first: the detail view looks
the task up with `tasks.access.get_task_or_404` and then checks
`assert_task_access`.
"""

import json

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction

from common.custom_fields import validate_payload as validate_custom_fields_payload
from common.models import Profile, Tags, Teams
from common.validators import payload_id_list
from contacts.access import replace_visible_contacts
from tasks.celery_tasks import send_email_to_assigned_user
from tasks.serializer import TaskCreateSerializer


def _model_errors(exc):
    """Django's ``ValidationError`` in the shape this API answers 400 with.

    ``Task.save()`` calls ``full_clean()``, so a model-level rule, today, "one
    parent entity", fires on the way to the database. Django's exception is
    not DRF's, so nothing caught it and the client got a 500 for breaking a
    documented rule. Same rule, same wording, now with the right status.
    """
    return (
        exc.message_dict if hasattr(exc, "message_dict") else {"detail": exc.messages}
    )


def notify_newly_assigned(request, task, previous_assignee_ids=()):
    """Email whoever this write just put on the task, and nobody else.

    Shared by create, PUT and PATCH, as in cases and contacts. Tasks used to
    send nothing on any of them. Queued once the surrounding transaction
    commits, as `cases.updates.notify_newly_assigned` explains.
    """
    current = set(task.assigned_to.values_list("id", flat=True))
    recipients = sorted(str(pk) for pk in current - set(previous_assignee_ids))
    if not recipients:
        return
    task_id = str(task.id)
    org_id = str(request.profile.org.id)
    transaction.on_commit(
        lambda: send_email_to_assigned_user.delay(recipients, task_id, org_id),
        robust=True,
    )


def create_task(request, data):
    """Create a task from ``data`` in the caller's org, created by them.

    Returns ``(task, None)``, or ``(None, errors)`` with the dict a 400
    carries, before anything is written. A malformed id in ``contacts``,
    ``teams``, ``assigned_to`` or ``tags`` raises DRF's ``ValidationError``
    (a 400).
    """
    org = request.profile.org
    serializer = TaskCreateSerializer(data=data, request_obj=request)
    if not serializer.is_valid():
        return None, serializer.errors

    cf_payload = data.get("custom_fields")
    if isinstance(cf_payload, str):
        try:
            cf_payload = json.loads(cf_payload)
        except (TypeError, ValueError):
            cf_payload = None
    cleaned_cf, cf_errors = validate_custom_fields_payload(
        "Task", cf_payload or {}, org
    )
    if cf_errors:
        return None, {"custom_fields": cf_errors}
    # Every id list is parsed before the first write, so a malformed one is a
    # 400 with no half-created task behind it.
    contact_ids = payload_id_list(data.get("contacts"), "contacts")
    team_ids = payload_id_list(data.get("teams"), "teams")
    assigned_ids = payload_id_list(data.get("assigned_to"), "assigned_to")
    tag_ids = payload_id_list(data.get("tags"), "tags")
    try:
        task = serializer.save(
            created_by=request.profile.user,
            due_date=data.get("due_date"),
            org=org,
            custom_fields=cleaned_cf,
        )
    except DjangoValidationError as exc:
        return None, _model_errors(exc)

    if contact_ids:
        replace_visible_contacts(task.contacts, contact_ids, request.profile)
    if team_ids:
        task.teams.add(*Teams.objects.filter(id__in=team_ids, org=org))
    if assigned_ids:
        task.assigned_to.add(
            *Profile.objects.filter(id__in=assigned_ids, org=org, is_active=True)
        )
    if tag_ids:
        task.tags.add(*Tags.objects.filter(id__in=tag_ids, org=org, is_active=True))

    notify_newly_assigned(request, task)
    return task, None


def update_task(request, task, data):
    """Apply ``data`` to ``task`` as a partial update.

    Returns ``None`` once saved, or the error dict a 400 carries, before
    anything is written. Only the keys present in ``data`` change;
    ``assigned_to`` replaces. A malformed id in ``contacts``, ``teams``,
    ``assigned_to`` or ``tags`` raises DRF's ``ValidationError`` (a 400).
    """
    org = request.profile.org
    serializer = TaskCreateSerializer(
        data=data,
        instance=task,
        request_obj=request,
        partial=True,
    )
    if not serializer.is_valid():
        return serializer.errors

    save_kwargs = {}
    if "custom_fields" in data:
        cf_payload = data.get("custom_fields")
        if isinstance(cf_payload, str):
            try:
                cf_payload = json.loads(cf_payload)
            except (TypeError, ValueError):
                cf_payload = None
        cleaned_cf, cf_errors = validate_custom_fields_payload(
            "Task",
            cf_payload or {},
            org,
            existing=task.custom_fields or {},
        )
        if cf_errors:
            return {"custom_fields": cf_errors}
        save_kwargs["custom_fields"] = cleaned_cf
    # Parsed before the first write, as in PUT. An absent key parses to [].
    contact_ids = payload_id_list(data.get("contacts"), "contacts")
    team_ids = payload_id_list(data.get("teams"), "teams")
    assigned_ids = payload_id_list(data.get("assigned_to"), "assigned_to")
    tag_ids = payload_id_list(data.get("tags"), "tags")
    try:
        task = serializer.save(**save_kwargs)
    except DjangoValidationError as exc:
        return _model_errors(exc)

    if "contacts" in data:
        replace_visible_contacts(task.contacts, contact_ids, request.profile)

    if "teams" in data:
        task.teams.clear()
        if team_ids:
            task.teams.add(*Teams.objects.filter(id__in=team_ids, org=org))

    if "assigned_to" in data:
        previous_assignee_ids = list(task.assigned_to.values_list("id", flat=True))
        task.assigned_to.clear()
        if assigned_ids:
            task.assigned_to.add(
                *Profile.objects.filter(id__in=assigned_ids, org=org, is_active=True)
            )
        notify_newly_assigned(request, task, previous_assignee_ids)

    if "tags" in data:
        task.tags.clear()
        if tag_ids:
            task.tags.add(*Tags.objects.filter(id__in=tag_ids, org=org, is_active=True))
    # Parent FKs are the serializer's job: it scopes all four to the org.
    return None
