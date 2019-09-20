import datetime

from celery.task import task
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import EmailMessage
from django.shortcuts import reverse
from django.template.loader import render_to_string
from django.utils import six, timezone
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from common.models import Comment, Profile, User
from common.token_generator import account_activation_token
from marketing.models import BlockedDomain, BlockedEmail


@task
def send_email_to_new_user(user_email, created_by, domain='demo.django-crm.io', protocol='http'):
    """ Send Mail To Users When their account is created """

    user_obj = User.objects.filter(email=user_email).first()
    user_obj.is_active = False
    user_obj.save()
    if user_obj:
        context = {}
        context["user_email"] = user_email
        context["created_by"] = created_by
        context["url"] = protocol + '://' + domain
        context["uid"] = urlsafe_base64_encode(force_bytes(user_obj.pk)),
        context["token"] = account_activation_token.make_token(user_obj)
        time_delta_two_hours = datetime.datetime.strftime(
            timezone.now() + datetime.timedelta(hours=2), "%Y-%m-%d-%H-%M-%S")
        context["token"] = context["token"]
        activation_key = context["token"] + time_delta_two_hours
        Profile.objects.create(user=user_obj, activation_key=activation_key)
        context["complete_url"] = context["url"] + \
            reverse('common:activate_user', args=(
                context['uid'][0], context['token'], activation_key))
        recipients = []
        recipients.append(user_email)
        subject = 'Welcome to Django CRM'
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
                    if User.objects.filter(username=comment_text.strip('@').strip(','), is_active=True).exists():
                        email = User.objects.filter(
                            username=comment_text.strip('@').strip(',')).first().email
                        recipients.append(email)

        context = {}
        context["commented_by"] = comment.commented_by
        context["comment_description"] = comment.comment
        if called_from == 'accounts':
            context["url"] = protocol + '://' + domain + \
                reverse('accounts:view_account', args=(comment.account.id,))
            subject = 'New comment on Account. '
        elif called_from == 'contacts':
            context["url"] = protocol + '://' + domain + \
                reverse('contacts:view_contact', args=(comment.contact.id,))
            subject = 'New comment on Contact. '
        elif called_from == 'leads':
            context["url"] = protocol + '://' + domain + \
                reverse('leads:view_lead', args=(comment.lead.id,))
            subject = 'New comment on Lead. '
        elif called_from == 'opportunity':
            context["url"] = protocol + '://' + domain + \
                reverse('opportunity:opp_view', args=(comment.opportunity.id,))
            subject = 'New comment on Opportunity. '
        elif called_from == 'cases':
            context["url"] = protocol + '://' + domain + \
                reverse('cases:view_case', args=(comment.case.id,))
            subject = 'New comment on Case. '
        elif called_from == 'tasks':
            context["url"] = protocol + '://' + domain + \
                reverse('tasks:task_detail', args=(comment.task.id,))
            subject = 'New comment on Task. '
        elif called_from == 'invoices':
            context["url"] = protocol + '://' + domain + \
                reverse('invoices:invoice_details', args=(comment.invoice.id,))
            subject = 'New comment on Invoice. '
        elif called_from == 'events':
            context["url"] = protocol + '://' + domain + \
                reverse('events:detail_view', args=(comment.event.id,))
            subject = 'New comment on Event. '
        else:
            context["url"] = ''
        # subject = 'Django CRM : comment '
        blocked_domains = BlockedDomain.objects.values_list('domain', flat=True)
        blocked_emails = BlockedEmail.objects.values_list('email', flat=True)
        if recipients:
            for recipient in recipients:
                if (recipient not in blocked_emails) and (recipient.split('@')[-1] not in blocked_domains):
                    recipients_list = [recipient, ]
                    context["mentioned_user"] = recipient
                    html_content = render_to_string('comment_email.html', context=context)
                    msg = EmailMessage(
                        subject,
                        html_content,
                        from_email=comment.commented_by.email,
                        to=recipients_list
                    )
                    msg.content_subtype = "html"
                    msg.send()


@task
def send_email_user_status(user_id, status_changed_user="", domain='demo.django-crm.io', protocol='http'):
    """ Send Mail To Users Regarding their status i.e active or inactive """
    user = User.objects.filter(id=user_id).first()
    if user:
        context = {}
        context["message"] = 'deactivated'
        context["email"] = user.email
        if user.has_sales_access:
            context["url"] = protocol + '://' + domain + '/'
        elif user.has_marketing_access:
            context["url"] = protocol + '://' + domain + '/marketing'
        else:
            context["url"] = protocol + '://' + domain + '/'
        if user.is_active:
            context["message"] = 'activated'
        context["status_changed_user"] = status_changed_user
        if context["message"] == 'activated':
            subject = 'Account Activated '
            html_content = render_to_string('user_status_activate.html', context=context)
        else:
            subject = 'Account Deactivated '
            html_content = render_to_string('user_status_deactivate.html', context=context)
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
def send_email_user_delete(user_email, deleted_by="", domain='demo.django-crm.io', protocol='http'):
    """ Send Mail To Users When their account is deleted """
    if user_email:
        context = {}
        context["message"] = 'deleted'
        context["deleted_by"] = deleted_by
        context["email"] = user_email
        recipients = []
        recipients.append(user_email)
        subject = 'CRM : Your account is Deleted. '
        html_content = render_to_string('user_delete_email.html', context=context)
        if recipients:
            msg = EmailMessage(
                subject,
                html_content,
                to=recipients
            )
            msg.content_subtype = "html"
            msg.send()


@task
def resend_activation_link_to_user(user_email="", domain='demo.django-crm.io', protocol='http'):
    """ Send Mail To Users When their account is created """

    user_obj = User.objects.filter(email=user_email).first()
    user_obj.is_active = False
    user_obj.save()
    if user_obj:
        context = {}
        context["user_email"] = user_email
        context["url"] = protocol + '://' + domain
        context["uid"] = urlsafe_base64_encode(force_bytes(user_obj.pk)),
        context["token"] = account_activation_token.make_token(user_obj)
        time_delta_two_hours = datetime.datetime.strftime(
            timezone.now() + datetime.timedelta(hours=2), "%Y-%m-%d-%H-%M-%S")
        context["token"] = context["token"]
        activation_key = context["token"] + time_delta_two_hours
        Profile.objects.filter(user=user_obj).update(
            activation_key=activation_key, key_expires=timezone.now() + datetime.timedelta(hours=2))
        context["complete_url"] = context["url"] + \
            reverse('common:activate_user', args=(
                context['uid'][0], context['token'], activation_key))
        recipients = []
        recipients.append(user_email)
        subject = 'Welcome to Django CRM'
        html_content = render_to_string('user_status_in.html', context=context)
        if recipients:
            msg = EmailMessage(
                subject,
                html_content,
                to=recipients
            )
            msg.content_subtype = "html"
            msg.send()
