from celery import Celery
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from accounts.models import Profile
from cases.models import Case

app = Celery("redis://")


@app.task
def send_email_to_assigned_user(recipients, case_id):
    """Send Mail To Users When they are assigned to a case"""
    case = Case.objects.get(id=case_id)
    created_by = case.created_by
    for profile_id in recipients:
        recipients_list = []
        profile = Profile.objects.filter(id=profile_id, is_active=True).first()
        if profile:
            recipients_list.append(profile.user.email)
            context = {}
            context["url"] = settings.DOMAIN_NAME
            context["user"] = profile.user
            context["case"] = case
            context["created_by"] = created_by
            subject = "Assigned to case."
            html_content = render_to_string(
                "assigned_to/cases_assigned.html", context=context
            )

            msg = EmailMessage(subject, html_content, to=recipients_list)
            msg.content_subtype = "html"
            msg.send()
