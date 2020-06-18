from celery.task import task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, EmailMessage
from django.db.models import Q
from django.shortcuts import reverse
from django.template.loader import render_to_string

from accounts.models import User
from opportunity.models import Opportunity
from marketing.models import BlockedDomain, BlockedEmail


@task
def send_email_to_assigned_user(recipients, opportunity_id, domain='demo.django-crm.io', protocol='http'):
    """ Send Mail To Users When they are assigned to a opportunity """
    opportunity = Opportunity.objects.get(id=opportunity_id)
    created_by = opportunity.created_by
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
                    reverse('opportunity:opp_view', args=(opportunity.id,))
                context["user"] = user
                context["opportunity"] = opportunity
                context["created_by"] = created_by
                subject = 'Assigned an opportunity for you.'
                html_content = render_to_string(
                    'assigned_to/opportunity_assigned.html', context=context)

                msg = EmailMessage(
                    subject,
                    html_content,
                    to=recipients_list
                )
                msg.content_subtype = "html"
                msg.send()
