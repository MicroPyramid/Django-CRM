import logging
from collections import defaultdict
from datetime import date

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMessage
from django.db import connection
from django.template.loader import render_to_string
from django.utils import timezone

from common.models import Org, Profile
from opportunity.models import Opportunity, SalesGoal, StageAgingConfig

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
            context["url"] = settings.DOMAIN_NAME
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


@shared_task
def check_stale_opportunities():
    """Daily task: find rotten deals across all orgs and send email alerts."""
    from opportunity.workflow import CLOSED_STAGES, DEFAULT_STAGE_EXPECTED_DAYS, ROTTEN_MULTIPLIER

    now = timezone.now()
    orgs = Org.objects.filter(is_active=True)

    for org in orgs:
        try:
            _set_rls_context_safe(str(org.id))

            aging_configs = {
                c.stage: c for c in StageAgingConfig.objects.filter(org=org)
            }

            open_opps = Opportunity.objects.filter(
                org=org, is_active=True
            ).exclude(stage__in=CLOSED_STAGES).select_related("org")

            stale_opps = []
            for opp in open_opps:
                if not opp.stage_changed_at:
                    continue
                config = aging_configs.get(opp.stage)
                expected = (
                    config.expected_days
                    if config
                    else DEFAULT_STAGE_EXPECTED_DAYS.get(opp.stage)
                )
                if expected is None:
                    continue
                days = (now - opp.stage_changed_at).days
                if days >= expected * ROTTEN_MULTIPLIER:
                    stale_opps.append((opp, days, expected))

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
    for opp, days, expected in stale_opps:
        assigned = list(opp.assigned_to.filter(is_active=True))
        if assigned:
            for profile in assigned:
                user_deals[profile].append((opp, days, expected))
        else:
            # No one assigned - alert org admins
            for admin in org_admins:
                user_deals[admin].append((opp, days, expected))

    for profile, deals in user_deals.items():
        context = {
            "user": profile.user,
            "deals": [
                {
                    "name": opp.name,
                    "stage": opp.get_stage_display(),
                    "days_in_stage": days,
                    "expected_days": expected,
                }
                for opp, days, expected in deals
            ],
            "url": settings.DOMAIN_NAME,
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


@shared_task
def check_goal_milestones():
    """Daily: check goal progress milestones and send notifications."""
    today = date.today()
    orgs = Org.objects.filter(is_active=True)

    for org in orgs:
        try:
            _set_rls_context_safe(str(org.id))

            goals = SalesGoal.objects.filter(
                org=org,
                is_active=True,
                period_start__lte=today,
                period_end__gte=today,
            )

            for goal in goals:
                percent = goal.progress_percent
                progress_value = goal.compute_progress()
                notifications = []

                if percent >= 100 and not goal.milestone_100_notified:
                    goal.milestone_100_notified = True
                    notifications.append(("100%", percent, progress_value))
                elif percent >= 90 and not goal.milestone_90_notified:
                    goal.milestone_90_notified = True
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
            logger.exception(
                "Error processing goal milestones for org %s", org.id
            )


def _send_goal_milestone_email(profile, goal, milestone_label, percent, achieved):
    """Send a milestone notification email for a sales goal."""
    context = {
        "user": profile.user,
        "goal": goal,
        "milestone": milestone_label,
        "percent": percent,
        "achieved": achieved,
        "url": settings.DOMAIN_NAME,
    }
    subject = f"[BottleCRM] Goal '{goal.name}' reached {milestone_label}!"
    html_content = render_to_string(
        "opportunity/goal_milestone.html", context=context
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
            "Failed to send goal milestone email to %s", profile.user.email
        )
