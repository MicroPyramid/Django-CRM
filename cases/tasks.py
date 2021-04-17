from celery import Celery
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, EmailMessage
from django.db.models import Q
from django.shortcuts import reverse
from django.template.loader import render_to_string

from accounts.models import User
from cases.models import Case

app = Celery("redis://")


@app.task
def send_email_to_assigned_user(
    recipients, case_id, domain="demo.django-crm.io", protocol="http"
):
    """ Send Mail To Users When they are assigned to a case """
    case = Case.objects.get(id=case_id)
    created_by = case.created_by
    for user in recipients:
        recipients_list = []
        user = User.objects.filter(id=user, is_active=True).first()
        if user:
            recipients_list.append(user.email)
            context = {}
            context["url"] = protocol + "://" + domain
            context["user"] = user
            context["case"] = case
            context["created_by"] = created_by
            subject = "Assigned to case."
            html_content = render_to_string(
                "assigned_to/cases_assigned.html", context=context
            )

            msg = EmailMessage(subject, html_content, to=recipients_list)
            msg.content_subtype = "html"
            msg.send()
