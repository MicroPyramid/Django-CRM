import logging

from botocore.exceptions import ClientError
from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMessage
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db import connection
from django.template.loader import render_to_string
from django.utils import timezone

from common.models import Comment, MagicLinkToken, Profile, Teams, User

logger = logging.getLogger(__name__)


def set_rls_context(org_id):
    """
    Set RLS context for Celery tasks that query org-scoped tables.

    Celery workers don't go through Django middleware, so RLS context
    must be set explicitly before querying org-scoped data.

    Args:
        org_id: Organization UUID (string or UUID object)
    """
    if org_id:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT set_config('app.current_org', %s, false)", [str(org_id)]
            )


@shared_task
def send_welcome_email(user_id):
    """Send welcome email to newly created users."""
    user_obj = User.objects.filter(id=user_id).first()
    if not user_obj:
        return

    email = user_obj.email.strip()
    try:
        validate_email(email)
    except ValidationError:
        logger.warning("Welcome email skipped: invalid email for user %s", user_id)
        return

    context = {"url": settings.FRONTEND_URL}
    subject = "Welcome to BottleCRM"
    html_content = render_to_string("welcome_email.html", context=context)

    msg = EmailMessage(
        subject,
        html_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email],
    )
    msg.content_subtype = "html"
    try:
        msg.send()
    except ClientError:
        logger.exception("SES rejected welcome email for user %s", user_id)


@shared_task
def send_magic_link_email(token_id):
    """Send magic link email for passwordless authentication."""
    magic_token = MagicLinkToken.objects.filter(id=token_id).first()
    if not magic_token:
        return

    email = magic_token.email.strip()
    try:
        validate_email(email)
    except ValidationError:
        logger.warning("Magic link skipped: invalid email format for token %s", token_id)
        return

    magic_link_url = f"{settings.FRONTEND_URL}/login/verify?token={magic_token.token}"

    html_content = render_to_string(
        "magic_link_email.html",
        {"magic_link_url": magic_link_url},
    )
    msg = EmailMessage(
        "Your BottleCRM sign-in link",
        html_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email],
    )
    msg.content_subtype = "html"
    try:
        msg.send()
    except ClientError:
        logger.exception("SES rejected email for magic link token %s", token_id)


@shared_task
def send_email_user_mentions(
    comment_id,
    called_from,
    org_id=None,
):
    """Send Mail To Mentioned Users In The Comment"""
    # Set RLS context for org-scoped queries
    set_rls_context(org_id)

    comment = Comment.objects.filter(id=comment_id).first()
    if comment:
        comment_text = comment.comment
        comment_text_list = comment_text.split()
        recipients = []
        for comment_text in comment_text_list:
            if comment_text.startswith("@"):
                if comment_text.strip("@").strip(",") not in recipients:
                    if User.objects.filter(
                        username=comment_text.strip("@").strip(","), is_active=True
                    ).exists():
                        email = (
                            User.objects.filter(
                                username=comment_text.strip("@").strip(",")
                            )
                            .first()
                            .email
                        )
                        recipients.append(email)

        context = {}
        context["commented_by"] = comment.commented_by
        context["comment_description"] = comment.comment
        subject = None
        if called_from == "accounts":
            subject = "New comment on Account. "
        elif called_from == "contacts":
            subject = "New comment on Contact. "
        elif called_from == "leads":
            subject = "New comment on Lead. "
        elif called_from == "opportunity":
            subject = "New comment on Opportunity. "
        elif called_from == "cases":
            subject = "New comment on Case. "
        elif called_from == "tasks":
            subject = "New comment on Task. "
        elif called_from == "invoices":
            subject = "New comment on Invoice. "
        if subject:
            context["url"] = settings.DOMAIN_NAME
        else:
            context["url"] = ""
        # subject = 'Django CRM : comment '
        if recipients:
            for recipient in recipients:
                recipients_list = [
                    recipient,
                ]
                context["mentioned_user"] = recipient
                html_content = render_to_string("comment_email.html", context=context)
                msg = EmailMessage(
                    subject,
                    html_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=recipients_list,
                )
                msg.content_subtype = "html"
                msg.send()


@shared_task
def send_email_user_status(
    user_id,
    status_changed_user="",
):
    """Send Mail To Users Regarding their status i.e active or inactive"""
    user = User.objects.filter(id=user_id).first()
    if user:
        context = {}
        context["message"] = "deactivated"
        context["email"] = user.email
        context["url"] = settings.DOMAIN_NAME
        if user.has_marketing_access:
            context["url"] = context["url"] + "/marketing"
        if user.is_active:
            context["message"] = "activated"
        context["status_changed_user"] = status_changed_user
        if context["message"] == "activated":
            subject = "Account Activated "
            html_content = render_to_string(
                "user_status_activate.html", context=context
            )
        else:
            subject = "Account Deactivated "
            html_content = render_to_string(
                "user_status_deactivate.html", context=context
            )
        recipients = []
        recipients.append(user.email)
        if recipients:
            msg = EmailMessage(
                subject,
                html_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipients,
            )
            msg.content_subtype = "html"
            msg.send()


@shared_task
def send_email_user_delete(
    user_email,
    deleted_by="",
):
    """Send Mail To Users When their account is deleted"""
    if user_email:
        context = {}
        context["message"] = "deleted"
        context["deleted_by"] = deleted_by
        context["email"] = user_email
        recipients = []
        recipients.append(user_email)
        subject = "CRM : Your account is Deleted. "
        html_content = render_to_string("user_delete_email.html", context=context)
        if recipients:
            msg = EmailMessage(
                subject,
                html_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipients,
            )
            msg.content_subtype = "html"
            msg.send()


@shared_task
def remove_users(removed_users_list, team_id, org_id=None):
    # Set RLS context for org-scoped queries
    set_rls_context(org_id)

    removed_users_list = [i for i in removed_users_list if i.isdigit()]
    users_list = Profile.objects.filter(id__in=removed_users_list)
    if users_list.exists():
        team = Teams.objects.filter(id=team_id).first()
        if team:
            accounts = team.account_teams.all()
            for account in accounts:
                for user in users_list:
                    account.assigned_to.remove(user)

            contacts = team.contact_teams.all()
            for contact in contacts:
                for user in users_list:
                    contact.assigned_to.remove(user)

            leads = team.lead_teams.all()
            for lead in leads:
                for user in users_list:
                    lead.assigned_to.remove(user)

            opportunities = team.oppurtunity_teams.all()
            for opportunity in opportunities:
                for user in users_list:
                    opportunity.assigned_to.remove(user)

            cases = team.cases_teams.all()
            for case in cases:
                for user in users_list:
                    case.assigned_to.remove(user)

            docs = team.document_teams.all()
            for doc in docs:
                for user in users_list:
                    doc.shared_to.remove(user)

            tasks = team.tasks_teams.all()
            for task in tasks:
                for user in users_list:
                    task.assigned_to.remove(user)

            invoices = team.invoices_teams.all()
            for invoice in invoices:
                for user in users_list:
                    invoice.assigned_to.remove(user)


@shared_task
def update_team_users(team_id, org_id=None):
    """this function updates assigned_to field on all models when a team is updated"""
    # Set RLS context for org-scoped queries
    set_rls_context(org_id)

    team = Teams.objects.filter(id=team_id).first()
    if team:
        teams_members = team.users.all()

        accounts = team.account_teams.all()
        for account in accounts:
            account_assigned_to_users = account.assigned_to.all()
            for team_member in teams_members:
                if team_member not in account_assigned_to_users:
                    account.assigned_to.add(team_member)

        contacts = team.contact_teams.all()
        for contact in contacts:
            contact_assigned_to_users = contact.assigned_to.all()
            for team_member in teams_members:
                if team_member not in contact_assigned_to_users:
                    contact.assigned_to.add(team_member)

        leads = team.lead_teams.all()
        for lead in leads:
            lead_assigned_to_users = lead.assigned_to.all()
            for team_member in teams_members:
                if team_member not in lead_assigned_to_users:
                    lead.assigned_to.add(team_member)

        opportunities = team.oppurtunity_teams.all()
        for opportunity in opportunities:
            opportunity_assigned_to_users = opportunity.assigned_to.all()
            for team_member in teams_members:
                if team_member not in opportunity_assigned_to_users:
                    opportunity.assigned_to.add(team_member)

        cases = team.cases_teams.all()
        for case in cases:
            case_assigned_to_users = case.assigned_to.all()
            for team_member in teams_members:
                if team_member not in case_assigned_to_users:
                    case.assigned_to.add(team_member)

        docs = team.document_teams.all()
        for doc in docs:
            doc_assigned_to_users = doc.shared_to.all()
            for team_member in teams_members:
                if team_member not in doc_assigned_to_users:
                    doc.shared_to.add(team_member)

        tasks = team.tasks_teams.all()
        for task in tasks:
            task_assigned_to_users = task.assigned_to.all()
            for team_member in teams_members:
                if team_member not in task_assigned_to_users:
                    task.assigned_to.add(team_member)

        invoices = team.invoices_teams.all()
        for invoice in invoices:
            invoice_assigned_to_users = invoice.assigned_to.all()
            for team_member in teams_members:
                if team_member not in invoice_assigned_to_users:
                    invoice.assigned_to.add(team_member)
