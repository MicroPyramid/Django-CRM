"""Who may do what to a task, two rules, beside the three in `cases.access`.

    access    admin · creator · assignee     read it, edit it, comment on it
    delete    admin · creator                destroy it

Two, not three, and that is the point of writing them down. A case splits
reading from writing because a *watcher* can follow a ticket without being
handed it; a task has no watcher, so everyone who may open one may also work
it. Deleting is narrower for the same reason it is narrower for a case: being
handed a task is a reason to do it, not a reason to erase it.

The list has to agree with the detail view or the queue lies, so `visible_tasks_qs`
is the queryset form of `access` and the two are derived from the same clauses.

**`created_by` is a `User`, not a `Profile`.** Every check this module replaced
compared `request.profile` to it, which is never equal, so the creator clause
was dead everywhere it appeared, and the list, which got it right with
`Q(created_by=profile.user)`, listed tasks the detail view then refused. The
comparison here is `profile.user_id == task.created_by_id`.

That dead clause is also why `created_by` has to be `read_only` on the
serializer, and the two changes belong in one commit: while nothing consults
the field, writing to it is a data-integrity bug; the moment the creator clause
starts returning `True`, a client that can PATCH a task can name itself the
creator and grant itself delete.
"""

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from django.http import Http404
from rest_framework.exceptions import PermissionDenied

# Re-exported, not redefined, the same arrangement `cases.access` uses. This
# was an eleventh copy of the admin rule and the only one that had taken the
# canonical name, so the guard test looking for private spellings walked past
# it. It read `role == "ADMIN" or is_admin`, which is now one fact and not two.
from common.permissions import is_org_admin  # noqa: F401
from tasks.models import Task

_DENIED = "You do not have Permission to perform this action"


def visible_tasks_qs(profile):
    """Tasks ``profile`` is allowed to open, the queryset form of `access`."""
    qs = Task.objects.filter(org=profile.org)
    if is_org_admin(profile):
        return qs
    return qs.filter(Q(created_by=profile.user) | Q(assigned_to=profile)).distinct()


def get_task_or_404(profile, pk):
    """Fetch a task in the requester's org, or raise ``Http404``.

    ``Task.id`` is a UUID column and the URL captures ``<str:pk>``, so
    ``filter(pk="nope")`` raises Django's ``ValidationError`` rather than
    matching nothing, which surfaced as a 500 on every verb, including the
    two that only need to say "no such task".
    """
    try:
        task = Task.objects.filter(pk=pk, org=profile.org).first()
    except (DjangoValidationError, ValueError):
        raise Http404("No such task.")
    if task is None:
        raise Http404("No such task.")
    return task


def has_task_access(profile, task):
    """Non-raising form of `access`, for deciding what to put in a response."""
    if is_org_admin(profile):
        return True
    if profile.user_id == task.created_by_id:
        return True
    return profile.id in {p.id for p in task.assigned_to.all()}


def assert_task_access(profile, task):
    """Raise 403 unless ``profile`` may open or change ``task``."""
    if not has_task_access(profile, task):
        raise PermissionDenied(_DENIED)


def has_task_delete_access(profile, task):
    """Non-raising form of `delete`."""
    if is_org_admin(profile):
        return True
    return profile.user_id == task.created_by_id


def assert_task_delete_access(profile, task):
    """Raise 403 unless ``profile`` may destroy ``task``.

    Narrower than `access` on purpose: see the module docstring.
    """
    if not has_task_delete_access(profile, task):
        raise PermissionDenied(_DENIED)
