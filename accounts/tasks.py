from celery.task import task
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.shortcuts import reverse

from accounts.models import Account, Email
from common.models import User
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



@task
def send_email_to_assigned_user(recipients, from_email, domain='demo.django-crm.io', protocol='http'):
    """ Send Mail To Users When they are assigned to a contact """
    account = Account.objects.filter(id=from_email).first()
    created_by = account.created_by
    for user in recipients:
        recipients_list = []
        user = User.objects.filter(id=user, is_active=True).first()
        if user:
            recipients_list.append(user.email)
            context = {}
            context["url"] = protocol + '://' + domain + \
                reverse('accounts:view_account', args=(account.id,))
            context["user"] = user
            context["account"] = account
            context["created_by"] = created_by
            subject = 'Assigned a account for you.'
            html_content = render_to_string(
                'assigned_to/account_assigned.html', context=context)

            msg = EmailMessage(
                subject,
                html_content,
                to=recipients_list
            )
            msg.content_subtype = "html"
            msg.send()
