from celery.task import task
from django.conf import settings
from django.core.mail import EmailMessage
from django.shortcuts import reverse
from django.template.loader import render_to_string

from common.models import User
from contacts.models import Contact
from events.models import Event


@task
def send_email(event_id, domain='demo.django-crm.io', protocol='http'):
    event = Event.objects.filter(id=event_id).first()
    subject = ' Invitation for an event.'
    context = {}
    context['event'] = event.name
    context['event_id'] = event_id
    context['event_created_by'] = event.created_by
    context['event_date_of_meeting'] = event.date_of_meeting
    context["url"] = protocol + '://' + domain + \
        reverse('events:detail_view', args=(event.id,))
    recipients = event.assigned_to.filter(is_active=True)
    if recipients.count() > 0:
        for recipient in recipients:
            context['other_members'] = list(recipients.exclude(
                id=recipient.id).values_list('email', flat=True))
            if len(context['other_members']) > 0:
                context['other_members'] = ', '.join(context['other_members'])
            else:
                context['other_members'] = ''
            context['user'] = recipient.email
            html_content = render_to_string(
                'assigned_to_email_template_event.html', context=context)
            msg = EmailMessage(
                subject=subject, body=html_content, to=[recipient.email, ])
            msg.content_subtype = "html"
            msg.send()

        # might need to add contacts to TODO
        # recipients = event.contacts.all()
        # if recipients.count() > 0:
        #     for recipient in recipients:
        #         context['user'] = recipient.email
        #         html_content = render_to_string(
        #             'assigned_to_email_template.html', context=context)
        #         msg = EmailMessage(
        #             subject=subject, body=html_content, to=[recipient.email, ])
        #         msg.content_subtype = "html"
        #         msg.send
