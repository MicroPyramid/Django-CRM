import logging
from collections import defaultdict
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMessage
from django.db import connection
from django.template.loader import render_to_string
from django.utils import timezone

from common.links import frontend_url
from common.models import Activity, Org, Profile
from common.modules import module_is_available, module_on_since
from common.org_time import activate_org_timezone, org_timezone
from opportunity.models import Opportunity, SalesGoal

logger = logging.getLogger(__name__)


def _set_rls_context_safe(org_id):
    """Set RLS context, skipping on non-PostgreSQL backends."""
    if connection.vendor == "postgresql":
        from common.tasks import set_rls_context

        set_rls_context(org_id)


@shared_task
def send_email_to_assigned_user(recipients, opportunity_id, org_id):
    """Send Mail To Users When they are assigned to an opportunity"""
    _set_rls_context_safe(org_id)
    opportunity = Opportunity.objects.get(id=opportunity_id)
    created_by = opportunity.created_by
    for user in recipients:
        recipients_list = []
        profile = Profile.objects.filter(id=user, is_active=True).first()
        if profile:
            recipients_list.append(profile.user.email)
            context = {}
            context["url"] = frontend_url(f"/pipeline/{opportunity.id}")
            context["user"] = profile.user
            context["opportunity"] = opportunity
            context["created_by"] = created_by
            subject = "Assigned an opportunity for you."
            html_content = render_to_string(
                "assigned_to/opportunity_assigned.html", context=context
            )

            msg = EmailMessage(subject, html_content, to=recipients_list)
            msg.content_subtype = "html"
            msg.send()


# Stale-deal alerts go only to orgs someone used lately. A dormant org's admin
# would otherwise get the same email every day about deals nobody works.
STALE_ALERT_ACTIVE_DAYS = 30


def _used_recently(org):
    """Whether anyone worked in the org, or signed in to it, in the last
    STALE_ALERT_ACTIVE_DAYS days. Runs under the org's RLS context."""
    since = timezone.now() - timedelta(days=STALE_ALERT_ACTIVE_DAYS)
    return (
        Activity.objects.filter(org=org, created_at__gte=since).exists()
        or Profile.objects.filter(
            org=org, is_active=True, user__last_login__gte=since
        ).exists()
    )


@shared_task
def check_stale_opportunities():
    """Daily task: find rotten deals across all orgs and send email alerts."""
    from opportunity.stages import aging_q, stage_index

    orgs = Org.objects.filter(is_active=True)

    for org in orgs:
        if not module_is_available(org, "deals"):
            continue
        try:
            _set_rls_context_safe(str(org.id))
            if not _used_recently(org):
                continue

            stages = stage_index(org.id)
            rotten_q = aging_q(stages.values(), "red")
            since = module_on_since(org, "deals")
            if since is not None:
                # Already rotten when Pipeline came back on: it went stale
                # while nobody could see it, so it is never alerted.
                rotten_q &= ~aging_q(stages.values(), "red", since)
            # A pack's sample deals are nobody's work, so they never alert.
            rotten = Opportunity.objects.filter(
                rotten_q, org=org, is_active=True, is_sample=False
            ).select_related("org")

            stale_opps = []
            for opp in rotten:
                stage = opp.current_stage(stages)
                stale_opps.append(
                    (opp, stage.label, opp.days_in_current_stage, stage.expected_days)
                )

            if stale_opps:
                send_stale_deals_alert(org, stale_opps)
        except Exception:
            logger.exception("Error processing stale deals for org %s", org.id)


def send_stale_deals_alert(org, stale_opps):
    """Send per-user email alerts for rotten deals."""
    # Pre-fetch org admins for unassigned deals
    org_admins = list(Profile.objects.filter(org=org, role="ADMIN", is_active=True))

    # Group by assigned users
    user_deals = defaultdict(list)
    for opp, label, days, expected in stale_opps:
        assigned = list(opp.assigned_to.filter(is_active=True))
        if assigned:
            for profile in assigned:
                user_deals[profile].append((opp, label, days, expected))
        else:
            # No one assigned - alert org admins
            for admin in org_admins:
                user_deals[admin].append((opp, label, days, expected))

    for profile, deals in user_deals.items():
        context = {
            "user": profile.user,
            "deals": [
                {
                    "name": opp.name,
                    "stage": label,
                    "days_in_stage": days,
                    "expected_days": expected,
                }
                for opp, label, days, expected in deals
            ],
            "url": frontend_url("/pipeline?rotten=true"),
            "deal_count": len(deals),
        }
        subject = f"[BottleCRM] {len(deals)} stale deal{'s' if len(deals) > 1 else ''} need attention"
        html_content = render_to_string(
            "opportunity/stale_deals_alert.html", context=context
        )
        msg = EmailMessage(
            subject,
            html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[profile.user.email],
        )
        msg.content_subtype = "html"
        try:
            msg.send()
        except Exception:
            logger.exception(
                "Failed to send stale deals alert to %s", profile.user.email
            )


def _current_goals(org):
    """``org``'s active goals whose period covers today. Call with the org's
    timezone active."""
    today = timezone.localdate()
    return SalesGoal.objects.filter(
        org=org, is_active=True, period_start__lte=today, period_end__gte=today
    )


def _mark_milestones(goal):
    """Set the milestone flags ``goal``'s progress has newly reached, and
    return the milestone to announce, if any."""
    progress_value = goal.compute_progress()
    if goal.target_value and goal.target_value != 0:
        percent = min(int(progress_value / goal.target_value * 100), 100)
    else:
        percent = 0
    notifications = []

    if percent >= 100 and not goal.milestone_100_notified:
        goal.milestone_100_notified = True
        goal.milestone_90_notified = True
        goal.milestone_50_notified = True
        notifications.append(("100%", percent, progress_value))
    elif percent >= 90 and not goal.milestone_90_notified:
        goal.milestone_90_notified = True
        goal.milestone_50_notified = True
        notifications.append(("90%", percent, progress_value))
    elif percent >= 50 and not goal.milestone_50_notified:
        goal.milestone_50_notified = True
        notifications.append(("50%", percent, progress_value))

    if notifications:
        goal.save(
            update_fields=[
                "milestone_50_notified",
                "milestone_90_notified",
                "milestone_100_notified",
            ]
        )
    return notifications


def settle_goal_milestones(org) -> None:
    """Goals is back on: mark the milestones already reached as announced,
    sending nothing, so only those reached from now on send an email."""
    with org_timezone(org):
        for goal in _current_goals(org):
            _mark_milestones(goal)


@shared_task
def check_goal_milestones():
    """Daily: check goal progress milestones and send notifications."""
    orgs = Org.objects.filter(is_active=True)

    try:
        for org in orgs:
            if not module_is_available(org, "goals"):
                continue
            try:
                _set_rls_context_safe(str(org.id))
                # A quarter ends when it ends where the org is, so the window is
                # resolved per org rather than once for the whole sweep.
                activate_org_timezone(org)

                for goal in _current_goals(org):
                    notifications = _mark_milestones(goal)
                    if notifications:
                        recipients = []
                        if goal.assigned_to:
                            recipients.append(goal.assigned_to)
                        elif goal.team:
                            recipients.extend(
                                Profile.objects.filter(
                                    user_teams=goal.team, is_active=True
                                )
                            )
                        else:
                            recipients.extend(
                                Profile.objects.filter(
                                    org=org, role="ADMIN", is_active=True
                                )
                            )

                        for milestone_label, pct, achieved in notifications:
                            for profile in recipients:
                                _send_goal_milestone_email(
                                    profile, goal, milestone_label, pct, achieved
                                )
            except Exception:
                logger.exception("Error processing goal milestones for org %s", org.id)
    finally:
        # Worker threads outlive a task; the next one must not inherit this
        # org's day. Same reason the request middleware deactivates.
        timezone.deactivate()


def _send_goal_milestone_email(profile, goal, milestone_label, percent, achieved):
    """Send a milestone notification email for a sales goal."""
    context = {
        "user": profile.user,
        "goal": goal,
        "milestone": milestone_label,
        "percent": percent,
        "achieved": achieved,
        "url": frontend_url("/goals"),
    }
    subject = f"[BottleCRM] Goal '{goal.name}' reached {milestone_label}!"
    html_content = render_to_string("opportunity/goal_milestone.html", context=context)
    msg = EmailMessage(
        subject,
        html_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[profile.user.email],
    )
    msg.content_subtype = "html"
    try:
        msg.send()
    except Exception:
        logger.exception(
            "Failed to send goal milestone email to %s", profile.user.email
        )
