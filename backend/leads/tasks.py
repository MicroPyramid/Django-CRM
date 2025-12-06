import re

from celery import Celery
from django.conf import settings
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.db.models import Q
from django.template.loader import render_to_string

from accounts.models import Account
from common.models import Org, Profile
from common.tasks import set_rls_context
from leads.models import Lead

app = Celery("redis://")


def get_rendered_html(template_name, context={}):
    html_content = render_to_string(template_name, context)
    return html_content


@app.task
def send_email(
    subject,
    html_content,
    text_content=None,
    from_email=None,
    recipients=[],
    attachments=[],
    bcc=[],
    cc=[],
):
    # send email to user with attachment
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


@app.task
def send_lead_assigned_emails(lead_id, new_assigned_to_list, site_address, org_id):
    set_rls_context(org_id)
    lead_instance = Lead.objects.filter(
        ~Q(status="converted"), pk=lead_id, is_active=True
    ).first()
    if not (lead_instance and new_assigned_to_list):
        return False

    users = Profile.objects.filter(id__in=new_assigned_to_list).distinct()
    subject = "Lead '%s' has been assigned to you" % lead_instance
    from_email = settings.DEFAULT_FROM_EMAIL
    template_name = "assigned_to/leads_assigned.html"

    url = site_address
    url += "/leads/" + str(lead_instance.id) + "/view/"

    context = {
        "lead_instance": lead_instance,
        "lead_detail_url": url,
    }
    mail_kwargs = {"subject": subject, "from_email": from_email}
    for profile in users:
        if profile.user.email:
            context["user"] = profile.user
            html_content = get_rendered_html(template_name, context)
            mail_kwargs["html_content"] = html_content
            mail_kwargs["recipients"] = [profile.user.email]
            send_email.delay(**mail_kwargs)


@app.task
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
            context["url"] = settings.DOMAIN_NAME
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
            msg.send()


@app.task
def create_lead_from_file(validated_rows, invalid_rows, user_id, source, company_id):
    """Parameters : validated_rows, invalid_rows, user_id.
    This function is used to create leads from a given file.
    """
    set_rls_context(company_id)
    email_regex = r"^[_a-zA-Z0-9-]+(\.[_a-zA-Z0-9-]+)*@[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*(\.[a-zA-Z]{2,4})$"
    profile = Profile.objects.get(id=user_id)
    org = Org.objects.filter(id=company_id).first()
    for row in validated_rows:
        if not Lead.objects.filter(title=row.get("title")).exists():
            if re.match(email_regex, row.get("email")) is not None:
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
                    lead.created_by = profile
                    lead.org = org
                    lead.save()
                except Exception:
                    pass
