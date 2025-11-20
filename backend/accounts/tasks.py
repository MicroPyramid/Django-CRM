from datetime import datetime

import pytz
from celery import Celery
from django.conf import settings
from django.core.mail import EmailMessage
from django.template import Context, Template
from django.template.loader import render_to_string

from accounts.models import Account, AccountEmail, AccountEmailLog
from common.models import Profile
from common.utils import convert_to_custom_timezone

app = Celery("redis://")


@app.task
def send_email(email_obj_id):
    email_obj = Email.objects.filter(id=email_obj_id).first()
    if email_obj:
        from_email = email_obj.from_email
        contacts = email_obj.recipients.all()
        for contact_obj in contacts:
            if not EmailLog.objects.filter(
                email=email_obj, contact=contact_obj, is_sent=True
            ).exists():
                html = email_obj.message_body
                context_data = {
                    "email": contact_obj.primary_email
                    if contact_obj.primary_email
                    else "",
                    "name": contact_obj.first_name
                    if contact_obj.first_name
                    else "" + " " + contact_obj.last_name
                    if contact_obj.last_name
                    else "",
                }
                try:
                    html_content = Template(html).render(Context(context_data))
                    subject = email_obj.message_subject
                    msg = EmailMessage(
                        subject,
                        html_content,
                        from_email=from_email,
                        to=[
                            contact_obj.primary_email,
                        ],
                    )
                    msg.content_subtype = "html"
                    res = msg.send()
                    if res:
                        email_obj.rendered_message_body = html_content
                        email_obj.save()
                        EmailLog.objects.create(
                            email=email_obj, contact=contact_obj, is_sent=True
                        )
                except Exception as e:
                    print(e)


@app.task
def send_email_to_assigned_user(recipients, from_email):
    """Send Mail To Users When they are assigned to a contact"""
    account = Account.objects.filter(id=from_email).first()
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


@app.task
def send_scheduled_emails():
    email_objs = Email.objects.filter(scheduled_later=True)
    # TODO: modify this later , since models are updated
    for each in email_objs:
        scheduled_date_time = each.scheduled_date_time

        sent_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        sent_time = datetime.strptime(sent_time, "%Y-%m-%d %H:%M")
        local_tz = pytz.timezone(settings.TIME_ZONE)
        sent_time = local_tz.localize(sent_time)
        sent_time = convert_to_custom_timezone(sent_time, each.timezone, to_utc=True)

        # if (
        #     str(each.scheduled_date_time.date()) == str(sent_time.date()) and
        #     str(scheduled_date_time.hour) == str(sent_time.hour) and
        #     (str(scheduled_date_time.minute + 5) < str(sent_time.minute) or
        #     str(scheduled_date_time.minute - 5) > str(sent_time.minute))
        # ):
        #     send_email.delay(each.id)
        if (
            str(each.scheduled_date_time.date()) == str(sent_time.date())
            and str(scheduled_date_time.hour) == str(sent_time.hour)
            and str(scheduled_date_time.minute) == str(sent_time.minute)
        ):
            send_email.delay(each.id)
