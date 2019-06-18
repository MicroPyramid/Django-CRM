from celery.task import task
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from accounts.models import Account, Email
from contacts.models import Contact


@task
def send_email(subject, html_content, from_email=None,
               recipients=[]):
    account = Account.objects.filter(id=from_email).first()
    if account:
        contacts = recipients
        for contact in contacts:
            contact_obj = Contact.objects.filter(email=contact).first()
            if contact_obj:
                Email.objects.create(sender=account,
                    recipient=contact_obj,message_subject=subject,
                    message_body=html_content)
                msg = EmailMessage(
                    subject,
                    html_content,
                    from_email=account.email,
                    to=[contact_obj.email, ]
                )
                msg.content_subtype = "html"
                msg.send()