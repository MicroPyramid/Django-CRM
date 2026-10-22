"""Background work for rules: the email a notify action sends to members, and
pruning old runs."""

import logging
from datetime import timedelta

from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone

from automation.limits import RUN_RETENTION_DAYS
from automation.models import FAILED, AutomationRun
from automation.validation import active_people
from common.links import frontend_url
from common.models import Org
from common.tasks import clear_rls_context, set_rls_context

logger = logging.getLogger(__name__)

EMAIL_FAILED = "The email could not be sent"


def mark_email_failed(org_id, run_id, step):
    """Mark action `step` of run `run_id` failed, and the run with it."""
    if run_id is None:
        return
    with transaction.atomic():
        run = (
            AutomationRun.objects.select_for_update()
            .filter(org_id=org_id, pk=run_id)
            .first()
        )
        if run is None:
            return
        for entry in run.steps:
            if entry.get("action") == step and entry.get("status") != FAILED:
                entry["status"] = FAILED
                entry["text"] = f"{entry.get('text', '')}. {EMAIL_FAILED}"
        run.status = FAILED
        run.reason = EMAIL_FAILED
        run.save(update_fields=["steps", "status", "reason", "updated_at"])
    # Imported here: the engine imports this module through the actions.
    from automation.engine import notify_failure

    notify_failure(run.rule, EMAIL_FAILED)


@shared_task
def send_member_email(profile_ids, subject, text, path, org_id, run_id=None, step=None):
    """Email `text` and a link to `path` to each active member of the org in `profile_ids`.

    `text` is a member's own words: the HTML part escapes it and the plain part
    carries it as written. A failed send marks the run's step failed.
    """
    set_rls_context(org_id)
    try:
        context = {"text": text, "url": frontend_url(path)}
        body = render_to_string("automation/member_email.txt", context)
        html = render_to_string("automation/member_email.html", context)
        people = active_people(org_id).filter(pk__in=profile_ids).select_related("user")
        failed = False
        for profile in people:
            if not profile.user.email:
                continue
            message = EmailMultiAlternatives(subject, body, to=[profile.user.email])
            message.attach_alternative(html, "text/html")
            try:
                message.send()
            except Exception as exc:
                # The exception's text can carry the address, so only its type.
                logger.warning(
                    "Automation email to profile %s failed: %s",
                    profile.pk,
                    type(exc).__name__,
                )
                failed = True
        if failed:
            mark_email_failed(org_id, run_id, step)
    finally:
        clear_rls_context()


@shared_task
def prune_org_runs(org_id) -> int:
    """Delete the org's runs older than `RUN_RETENTION_DAYS`; how many went."""
    cutoff = timezone.now() - timedelta(days=RUN_RETENTION_DAYS)
    set_rls_context(org_id)
    try:
        removed, _ = AutomationRun.objects.filter(
            org_id=org_id, created_at__lt=cutoff
        ).delete()
    finally:
        clear_rls_context()
    return removed


@shared_task
def prune_runs():
    """Delete every org's runs older than `RUN_RETENTION_DAYS`, org by org."""
    orgs = Org.objects.values_list("id", flat=True).iterator()
    deleted = sum(prune_org_runs(org_id) for org_id in orgs)
    if deleted:
        logger.info("Pruned %s automation runs", deleted)
    return deleted
