from celery.task import task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, EmailMessage
from django.db.models import Q
from django.shortcuts import reverse
from django.template.loader import render_to_string

from accounts.models import User
from cases.models import Case
from marketing.models import BlockedDomain, BlockedEmail


@task
def send_email_to_assigned_user(recipients, case_id, domain='demo.django-crm.io', protocol='http'):
    """ Send Mail To Users When they are assigned to a case """
    case = Case.objects.get(id=case_id)
    created_by = case.created_by
    blocked_domains = BlockedDomain.objects.values_list('domain', flat=True)
    blocked_emails = BlockedEmail.objects.values_list('email', flat=True)
    for user in recipients:
        recipients_list = []
        user = User.objects.filter(id=user, is_active=True).first()
        if user:
            if (user.email not in blocked_emails) and (user.email.split('@')[-1] not in blocked_domains):
                recipients_list.append(user.email)
                context = {}
                context["url"] = protocol + '://' + domain + \
                    reverse('cases:view_case', args=(case.id,))
                context["user"] = user
                context["case"] = case
                context["created_by"] = created_by
                subject = 'Assigned to case.'
                html_content = render_to_string(
                    'assigned_to/cases_assigned.html', context=context)

                msg = EmailMessage(
                    subject,
                    html_content,
                    to=recipients_list
                )
                msg.content_subtype = "html"
                msg.send()
