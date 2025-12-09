from celery import Celery
from django.conf import settings
from django.core.mail import EmailMessage
from django.shortcuts import reverse
from django.template.loader import render_to_string

from accounts.models import Account
from common.models import User
from common.tasks import set_rls_context
from contacts.models import Contact
from tasks.models import Task

app = Celery("redis://")


@app.task
def send_email(
    task_id, recipients, org_id, domain="demo.django-crm.io", protocol="http"
):
    set_rls_context(org_id)
    task = Task.objects.filter(id=task_id).first()
    created_by = task.created_by
    for user in recipients:
        recipients_list = []
        user = User.objects.filter(id=user, is_active=True).first()
        if user:
            recipients_list.append(user.email)
            subject = " Assigned a task for you ."
            context = {}
            context["task_title"] = task.title
            context["task_id"] = task.id
            context["task_created_by"] = task.created_by
            context["url"] = protocol + "://" + domain
            context["user"] = user
            html_content = render_to_string(
                "tasks_email_template.html", context=context
            )
            msg = EmailMessage(subject=subject, body=html_content, to=recipients_list)
            msg.content_subtype = "html"
            msg.send()
