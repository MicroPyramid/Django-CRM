from celery.task import task
from django.core.mail import EmailMessage
from django.shortcuts import reverse
from django.template.loader import render_to_string

from common.models import Comment, User


@task
def send_email_to_new_user(user_email, created_by, domain='demo.django-crm.io', protocol='http'):
    """ Send Mail To Users When their account is created """
    if user_email:
        context = {}
        context["user_email"] = user_email
        context["created_by"] = created_by
        context["url"] = protocol + '://' + domain + '/'
        recipients = []
        recipients.append(user_email)
        subject = 'Created account in CRM'
        html_content = render_to_string('user_status_in.html', context=context)
        if recipients:
            msg = EmailMessage(
                subject,
                html_content,
                to=recipients
            )
            msg.content_subtype = "html"
            msg.send()


@task
def send_email_user_mentions(comment_id, called_from, domain='demo.django-crm.io', protocol='http'):
    """ Send Mail To Mentioned Users In The Comment """
    comment = Comment.objects.filter(id=comment_id).first()
    if comment:
        comment_text = comment.comment
        comment_text_list = comment_text.split()
        recipients = []
        for comment_text in comment_text_list:
            if comment_text.startswith('@'):
                if comment_text.strip('@').strip(',') not in recipients:
                    if User.objects.filter(username=comment_text.strip('@').strip(',')).exists():
                        email = User.objects.filter(
                            username=comment_text.strip('@').strip(',')).first().email
                        recipients.append(email)

        context = {}
        context["name"] = comment.commented_by
        context["comment_description"] = comment.comment
        if called_from == 'accounts':
            context["url"] = protocol + '://' + domain + \
                reverse('accounts:view_account', args=(comment.account.id,))
        elif called_from == 'contacts':
            context["url"] = protocol + '://' + domain + \
                reverse('contacts:view_contact', args=(comment.contact.id,))
        elif called_from == 'leads':
            context["url"] = protocol + '://' + domain + \
                reverse('leads:view_lead', args=(comment.lead.id,))
        elif called_from == 'opportunity':
            context["url"] = protocol + '://' + domain + \
                reverse('opportunity:opp_view', args=(comment.opportunity.id,))
        elif called_from == 'cases':
            context["url"] = protocol + '://' + domain + \
                reverse('cases:view_case', args=(comment.case.id,))
        elif called_from == 'tasks':
            context["url"] = protocol + '://' + domain + \
                reverse('tasks:task_detail', args=(comment.task.id,))
        elif called_from == 'invoices':
            context["url"] = protocol + '://' + domain + \
                reverse('invoices:invoice_details', args=(comment.invoice.id,))
        elif called_from == 'events':
            context["url"] = protocol + '://' + domain + \
                reverse('events:detail_view', args=(comment.event.id,))
        else:
            context["url"] = ''
        html_content = render_to_string('comment_email.html', context=context)
        subject = 'Django CRM : comment '
        if recipients:
            msg = EmailMessage(
                subject,
                html_content,
                from_email=comment.commented_by.email,
                to=recipients
            )
            msg.content_subtype = "html"
            msg.send()


@task
def send_email_user_status(user_id, domain='demo.django-crm.io', protocol='http'):
    """ Send Mail To Users Regarding their status i.e active or inactive """
    user = User.objects.filter(id=user_id).first()
    if user:
        context = {}
        context["message"] = 'deactivated'
        if user.is_active:
            context["url"] = protocol + '://' + domain + '/'
            context["message"] = 'activated'
        html_content = render_to_string('user_status.html', context=context)
        subject = 'CRM : User Status '
        recipients = []
        recipients.append(user.email)
        if recipients:
            msg = EmailMessage(
                subject,
                html_content,
                to=recipients
            )
            msg.content_subtype = "html"
            msg.send()

@task
def send_email_user_delete(user_email, domain='demo.django-crm.io', protocol='http'):
    """ Send Mail To Users When their account is deleted """
    if user_email:
        context = {}
        context["message"] = 'deleted'
        recipients = []
        recipients.append(user_email)
        subject = 'CRM : User Deleted. '
        html_content = render_to_string('user_status.html', context=context)
        if recipients:
            msg = EmailMessage(
                subject,
                html_content,
                to=recipients
            )
            msg.content_subtype = "html"
            msg.send()
