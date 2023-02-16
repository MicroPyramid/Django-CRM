from celery import Celery
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from common.models import Profile
from events.models import Event

app = Celery("redis://")


@app.task
def send_email(event_id, recipients):
    event = Event.objects.filter(id=event_id).first()
    subject = " Invitation for an event."
    context = {}
    context["event"] = event.name
    context["event_id"] = event_id
    context["event_created_by"] = event.created_by
    context["event_date_of_meeting"] = event.date_of_meeting
    context["url"] = settings.DOMAIN_NAME
    # recipients = event.assigned_to.filter(is_active=True)
    for profile_id in recipients:
        recipients_list = []
        profile = Profile.objects.filter(id=profile_id, is_active=True).first()
        if profile:
            recipients_list.append(profile.user.email)
            event_members = event.assigned_to.filter(is_active=True)

            context["other_members"] = list(
                event_members.exclude(id=profile.id).values_list(
                    "user__email", flat=True
                )
            )
            if len(context["other_members"]) > 0:
                context["other_members"] = ", ".join(context["other_members"])
            else:
                context["other_members"] = ""
            context["user"] = profile.user.email
            html_content = render_to_string(
                "assigned_to_email_template_event.html", context=context
            )
            msg = EmailMessage(subject=subject, body=html_content, to=recipients_list)
            msg.content_subtype = "html"
            msg.send()

    # if recipients.count() > 0:
    #     for recipient in recipients:
    #         context['other_members'] = list(recipients.exclude(
    #             id=recipient.id).values_list('email', flat=True))
    #         if len(context['other_members']) > 0:
    #             context['other_members'] = ', '.join(context['other_members'])
    #         else:
    #             context['other_members'] = ''
    #         context['user'] = recipient.email
    #         html_content = render_to_string(
    #             'assigned_to_email_template_event.html', context=context)
    #         msg = EmailMessage(
    #             subject=subject, body=html_content, to=[recipient.email, ])
    #         msg.content_subtype = "html"
    #         msg.send()

    # if recipients.count() > 0:
    #     for recipient in recipients:
    #         context['other_members'] = list(recipients.exclude(
    #             id=recipient.id).values_list('email', flat=True))
    #         if len(context['other_members']) > 0:
    #             context['other_members'] = ', '.join(context['other_members'])
    #         else:
    #             context['other_members'] = ''
    #         context['user'] = recipient.email
    #         html_content = render_to_string(
    #             'assigned_to_email_template_event.html', context=context)
    #         msg = EmailMessage(
    #             subject=subject, body=html_content, to=[recipient.email, ])
    #         msg.content_subtype = "html"
    #         msg.send()

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
