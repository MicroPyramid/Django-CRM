from celery.task import task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, EmailMessage
from django.db.models import Q
from django.shortcuts import reverse
from django.template.loader import render_to_string

from accounts.models import User
from leads.models import Lead


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
def send_email_to_assigned_user(recipients, lead_id, domain='demo.django-crm.io', protocol='http'):
    """ Send Mail To Users When they are assigned to a lead """
    lead = Lead.objects.get(id=lead_id)
    for user in recipients:
        recipients_list = []
        user = User.objects.filter(id=user).first()
        if user:
            recipients_list.append(user.email)
            context = {}
            context["url"] = protocol + '://' + domain + \
                reverse('leads:view_lead', args=(lead.id,))
            context["user"] = user
            context["lead"] = lead
            subject = 'Assigned to lead.'
            html_content = render_to_string(
                'assigned_to/leads_assigned.html', context=context)

            msg = EmailMessage(
                subject,
                html_content,
                to=recipients_list
            )
            msg.content_subtype = "html"
            msg.send()
