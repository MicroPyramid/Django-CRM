from celery.task import task
from django.core.mail import EmailMessage
from django.shortcuts import reverse
from django.template.loader import render_to_string

from common.models import User
from contacts.models import Contact


@task
def send_email_to_assigned_user(recipients, contact_id, domain='demo.django-crm.io', protocol='http'):
    """ Send Mail To Users When they are assigned to a contact """
    contact = Contact.objects.get(id=contact_id)
    for user in recipients:
        recipients_list = []
        user = User.objects.filter(id=user).first()
        if user:
            recipients_list.append(user.email)
            context = {}
            context["url"] = protocol + '://' + domain + \
                reverse('contacts:view_contact', args=(contact.id,))
            context["user"] = user
            context["contact"] = contact
            subject = 'Assigned to contact.'
            html_content = render_to_string(
                'assigned_to/contact_assigned.html', context=context)

            msg = EmailMessage(
                subject,
                html_content,
                to=recipients_list
            )
            msg.content_subtype = "html"
            msg.send()
