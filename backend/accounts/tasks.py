from celery import Celery
from django.conf import settings
from django.core.mail import EmailMessage
from django.template import Context, Template
from django.template.loader import render_to_string

from accounts.models import Account, AccountEmail, AccountEmailLog
from common.models import Profile
from common.tasks import set_rls_context

app = Celery("redis://")


@app.task
def send_email(email_obj_id, org_id):
    set_rls_context(org_id)
    email_obj = AccountEmail.objects.filter(id=email_obj_id).first()
    if email_obj:
        from_email = email_obj.from_email
        contacts = email_obj.recipients.all()
        for contact_obj in contacts:
            if not AccountEmailLog.objects.filter(
                email=email_obj, contact=contact_obj, is_sent=True
            ).exists():
                html = email_obj.message_body
                context_data = {
                    "email": contact_obj.email if contact_obj.email else "",
                    "name": (
                        contact_obj.first_name
                        if contact_obj.first_name
                        else (
                            "" + " " + contact_obj.last_name
                            if contact_obj.last_name
                            else ""
                        )
                    ),
                }
                try:
                    html_content = Template(html).render(Context(context_data))
                    subject = email_obj.message_subject
                    msg = EmailMessage(
                        subject,
                        html_content,
                        from_email=from_email,
                        to=[
                            contact_obj.email,
                        ],
                    )
                    msg.content_subtype = "html"
                    res = msg.send()
                    if res:
                        email_obj.rendered_message_body = html_content
                        email_obj.save()
                        AccountEmailLog.objects.create(
                            email=email_obj, contact=contact_obj, is_sent=True
                        )
                except Exception:
                    pass


@app.task
def send_email_to_assigned_user(recipients, account_id, org_id):
    """Send Mail To Users When they are assigned to an account"""
    set_rls_context(org_id)
    account = Account.objects.filter(id=account_id).first()
    if not account:
        return
    created_by = account.created_by

    for profile_id in recipients:
        recipients_list = []
        profile = Profile.objects.filter(id=profile_id, is_active=True).first()
        if profile:
            recipients_list.append(profile.user.email)
            context = {}
            context["url"] = settings.DOMAIN_NAME
            context["user"] = profile.user
            context["account"] = account
            context["created_by"] = created_by
            subject = "Assigned a account for you."
            html_content = render_to_string(
                "assigned_to/account_assigned.html", context=context
            )

            msg = EmailMessage(subject, html_content, to=recipients_list)
            msg.content_subtype = "html"
            msg.send()
