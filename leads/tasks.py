import re

from celery.task import task
from django.conf import settings
from django.core.cache import cache
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.db.models import Q
from django.shortcuts import reverse
from django.template.loader import render_to_string

from accounts.models import User
from leads.models import Lead
from marketing.models import BlockedDomain, BlockedEmail


def get_rendered_html(template_name, context={}):
    html_content = render_to_string(template_name, context)
    return html_content


@task
def send_email(subject, html_content,
               text_content=None, from_email=None,
               recipients=[], attachments=[], bcc=[], cc=[]):
    # send email to user with attachment
    if not from_email:
        from_email = settings.DEFAULT_FROM_EMAIL
    if not text_content:
        text_content = ''
    email = EmailMultiAlternatives(
        subject, text_content, from_email, recipients, bcc=bcc, cc=cc
    )
    email.attach_alternative(html_content, "text/html")
    for attachment in attachments:
        # Example: email.attach('design.png', img_data, 'image/png')
        email.attach(*attachment)
    email.send()


@task
def send_lead_assigned_emails(lead_id, new_assigned_to_list, site_address):
    lead_instance = Lead.objects.filter(
        ~Q(status='converted'), pk=lead_id, is_active=True
    ).first()
    if not (lead_instance and new_assigned_to_list):
        return False

    users = User.objects.filter(id__in=new_assigned_to_list).distinct()
    subject = "Lead '%s' has been assigned to you" % lead_instance
    from_email = settings.DEFAULT_FROM_EMAIL
    template_name = 'lead_assigned.html'

    url = site_address
    url += '/leads/' + str(lead_instance.id) + '/view/'

    context = {
        "lead_instance": lead_instance,
        "lead_detail_url": url,
    }
    mail_kwargs = {"subject": subject, "from_email": from_email}
    for user in users:
        if user.email:
            context["user"] = user
            html_content = get_rendered_html(template_name, context)
            mail_kwargs["html_content"] = html_content
            mail_kwargs["recipients"] = [user.email]
            send_email.delay(**mail_kwargs)


@task
def send_email_to_assigned_user(recipients, lead_id, domain='demo.django-crm.io', protocol='http', source=''):
    """ Send Mail To Users When they are assigned to a lead """
    lead = Lead.objects.get(id=lead_id)
    created_by = lead.created_by
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
                    reverse('leads:view_lead', args=(lead.id,))
                context["user"] = user
                context["lead"] = lead
                context["created_by"] = created_by
                context["source"] = source
                subject = 'Assigned a lead for you. '
                html_content = render_to_string(
                    'assigned_to/leads_assigned.html', context=context)
                msg = EmailMessage(
                    subject,
                    html_content,
                    to=recipients_list
                )
                msg.content_subtype = "html"
                msg.send()


@task
def create_lead_from_file(validated_rows, invalid_rows, user_id, source):
    """Parameters : validated_rows, invalid_rows, user_id.
    This function is used to create leads from a given file.
    """
    email_regex = '^[_a-zA-Z0-9-]+(\.[_a-zA-Z0-9-]+)*@[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*(\.[a-zA-Z]{2,4})$'
    user = User.objects.get(id=user_id)
    for row in validated_rows:
        if not Lead.objects.filter(title=row.get('title')).exists():
            if re.match(email_regex, row.get('email')) is not None:
                lead = Lead()
                lead.title = row.get('title')
                lead.first_name = row.get('first name')
                lead.last_name = row.get('last name')
                lead.website = row.get('website')
                lead.email = row.get('email')
                lead.phone = row.get('phone')
                lead.address_line = row.get('address')
                # lead.city = row.get('city')
                # lead.state = row.get('state')
                # lead.postcode = row.get('postcode')
                # lead.country = row.get('country')
                lead.created_by = user
                lead.save()


@task
def update_leads_cache():
    queryset = Lead.objects.all().exclude(status='converted').select_related('created_by'
            ).prefetch_related('tags', 'assigned_to',)
    open_leads = queryset.exclude(status='closed')
    close_leads = queryset.filter(status='closed')
    cache.set('admin_leads_open_queryset', open_leads, 60*60)
    cache.set('admin_leads_close_queryset', close_leads, 60*60)
