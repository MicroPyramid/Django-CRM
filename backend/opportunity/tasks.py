from collections import defaultdict

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMessage
from django.db import connection
from django.template.loader import render_to_string
from django.utils import timezone

from common.models import Org, Profile
from opportunity.models import Opportunity, StageAgingConfig


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


def send_stale_deals_alert(org, stale_opps):
    """Send per-user email alerts for rotten deals."""
    # Group by assigned users
    user_deals = defaultdict(list)
    for opp, days, expected in stale_opps:
        assigned = list(opp.assigned_to.filter(is_active=True))
        if assigned:
            for profile in assigned:
                user_deals[profile].append((opp, days, expected))
        else:
            # No one assigned - alert org admins
            admins = Profile.objects.filter(org=org, role="ADMIN", is_active=True)
            for admin in admins:
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
        msg.send()
