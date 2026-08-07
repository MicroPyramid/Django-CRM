import logging
import re

from celery import shared_task
from crum import impersonate
from django.conf import settings
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.db.models import Q
from django.template.loader import render_to_string

from accounts.models import Account
from common.links import frontend_url
from common.models import Org, Profile
from common.tasks import set_rls_context
from leads.models import Lead

logger = logging.getLogger(__name__)


def get_rendered_html(template_name, context=None):
    if context is None:
        context = {}
    html_content = render_to_string(template_name, context)
    return html_content


@shared_task
def send_email(
    subject,
    html_content,
    text_content=None,
    from_email=None,
    recipients=None,
    attachments=None,
    bcc=None,
    cc=None,
):
    # send email to user with attachment
    if recipients is None:
        recipients = []
    if attachments is None:
        attachments = []
    if bcc is None:
        bcc = []
    if cc is None:
        cc = []
    if not from_email:
        from_email = settings.DEFAULT_FROM_EMAIL
    if not text_content:
        text_content = ""
    email = EmailMultiAlternatives(
        subject, text_content, from_email, recipients, bcc=bcc, cc=cc
    )
    email.attach_alternative(html_content, "text/html")
    for attachment in attachments:
        # Example: email.attach('design.png', img_data, 'image/png')
        email.attach(*attachment)
    email.send()


@shared_task
def send_lead_assigned_emails(lead_id, new_assigned_to_list, org_id):
    set_rls_context(org_id)
    lead_instance = Lead.objects.filter(
        ~Q(status="converted"), pk=lead_id, is_active=True
    ).first()
    if not (lead_instance and new_assigned_to_list):
        return False

    users = Profile.objects.filter(id__in=new_assigned_to_list).distinct()
    subject = f"Lead '{lead_instance}' has been assigned to you"
    from_email = settings.DEFAULT_FROM_EMAIL
    template_name = "assigned_to/leads_assigned.html"

    # The `site_address` argument this used to take was built by its one caller
    # from `request.META["HTTP_HOST"]`, on an endpoint an unauthenticated web
    # form posts to. That named the API host, where `/leads/<id>` does not
    # exist, and it put a client-supplied value into the link of an email this
    # system sends to its own users.
    context = {
        # `lead`, not `lead_instance`: the template's two senders used
        # different names for the same object and it hedged with
        # `{{ lead.title|default:lead_instance }}`. Django resolves a filter's
        # argument eagerly, so that expression raised `VariableDoesNotExist`
        # out of `render_to_string` for whichever sender supplied `lead`,
        # which is the one that runs on an ordinary assignment. That email
        # never rendered, let alone sent.
        "lead": lead_instance,
        "url": frontend_url(f"/leads/{lead_instance.id}"),
    }
    mail_kwargs = {"subject": subject, "from_email": from_email}
    for profile in users:
        if profile.user.email:
            context["user"] = profile.user
            html_content = get_rendered_html(template_name, context)
            mail_kwargs["html_content"] = html_content
            mail_kwargs["recipients"] = [profile.user.email]
            send_email.delay(**mail_kwargs)
    return None


@shared_task
def send_email_to_assigned_user(recipients, lead_id, org_id, source=""):
    """Send Mail To Users When they are assigned to a lead"""
    set_rls_context(org_id)
    lead = Lead.objects.get(id=lead_id)
    created_by = lead.created_by
    for user in recipients:
        recipients_list = []
        profile = Profile.objects.filter(id=user, is_active=True).first()
        if profile:
            recipients_list.append(profile.user.email)
            context = {}
            context["url"] = frontend_url(f"/leads/{lead.id}")
            context["user"] = profile.user
            context["lead"] = lead
            context["created_by"] = created_by
            context["source"] = source
            subject = "Assigned a lead for you. "
            html_content = render_to_string(
                "assigned_to/leads_assigned.html", context=context
            )
            msg = EmailMessage(subject, html_content, to=recipients_list)
            msg.content_subtype = "html"
            try:
                msg.send()
            except Exception as e:
                logger.error(
                    "Failed to send lead assignment email to %s: %s",
                    profile.user.email,
                    e,
                )


@shared_task
def create_lead_from_file(validated_rows, invalid_rows, user_id, source, company_id):
    """Parameters : validated_rows, invalid_rows, user_id.
    This function is used to create leads from a given file.
    """
    set_rls_context(company_id)
    email_regex = r"^[_a-zA-Z0-9-]+(\.[_a-zA-Z0-9-]+)*@[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*(\.[a-zA-Z]{2,4})$"
    profile = Profile.objects.get(id=user_id)
    org = Org.objects.filter(id=company_id).first()
    for row in validated_rows:
        # The collision check was unscoped, so a title already used by another
        # org silently suppressed the row. RLS masks this wherever it is
        # active, but the org filter is the contract, not the safety net.
        if not Lead.objects.filter(title=row.get("title"), org=org).exists():
            # `email` is not a required CSV header (the form only requires
            # `title`), so `row.get("email")` is None for a file without that
            # column. `re.match` raises TypeError on None, and this line sits
            # outside the per-row try, so one such file killed the whole task.
            # The caller had already been told "Leads created Successfully",
            # because the task is dispatched with .delay(), so the import
            # failed in total silence.
            email = row.get("email") or ""
            if email and re.match(email_regex, email) is not None:
                try:
                    lead = Lead()
                    lead.title = row.get("title", "")[:64]
                    lead.first_name = row.get("first name", "")[:255]
                    lead.last_name = row.get("last name", "")[:255]
                    lead.website = row.get("website", "")[:255]
                    lead.email = row.get("email", "")
                    lead.phone = row.get("phone", "")
                    lead.address_line = row.get("address", "")[:255]
                    lead.city = row.get("city", "")[:255]
                    lead.state = row.get("state", "")[:255]
                    lead.postcode = row.get("postcode", "")[:64]
                    lead.country = row.get("country", "")[:3]
                    lead.description = row.get("description", "")
                    lead.status = row.get("status", "")
                    # Look up company by name if provided in CSV
                    account_name = row.get("account_name", "").strip()[:255]
                    if account_name:
                        company = Account.objects.filter(
                            name__iexact=account_name, org=org
                        ).first()
                        if company:
                            lead.company = company
                    lead.org = org
                    # `created_by` is a FK to `User`; this assigned a
                    # `Profile`, which raises ValueError before any SQL runs.
                    # The bare `except` below swallowed it, so every row was
                    # dropped and the import created nothing, ever, while the
                    # caller held a "Leads created Successfully" 200.
                    #
                    # `BaseModel.save()` then overwrites `created_by` from
                    # crum's current user, which is None inside a worker, so
                    # assigning the field here is not enough on its own.
                    # Impersonating the importer is how `seed_data` solves the
                    # same problem, and it makes the audit trail name the
                    # person who uploaded the file.
                    with impersonate(profile.user):
                        lead.save()
                except Exception:
                    logger.exception(
                        "Skipped a row while importing leads for org %s", company_id
                    )
