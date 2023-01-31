import datetime

from celery import Celery
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from common.models import Comment, Profile, User
from common.token_generator import account_activation_token

app = Celery("redis://")


@app.task
def send_email_to_new_user(user_id):

    """Send Mail To Users When their account is created"""
    user_obj = User.objects.filter(id=user_id).first()

    if user_obj:
        context = {}
        user_email = user_obj.email
        context["url"] = settings.DOMAIN_NAME
        context["uid"] = (urlsafe_base64_encode(force_bytes(user_obj.pk)),)
        context["token"] = account_activation_token.make_token(user_obj)
        time_delta_two_hours = datetime.datetime.strftime(
            timezone.now() + datetime.timedelta(hours=2), "%Y-%m-%d-%H-%M-%S"
        )
        # creating an activation token and saving it in user model
        activation_key = context["token"] + time_delta_two_hours
        user_obj.activation_key = activation_key
        user_obj.save()

        context["complete_url"] = context[
            "url"
        ] + "/auth/activate-user/{}/{}/{}/".format(
            context["uid"][0],
            context["token"],
            activation_key,
        )
        recipients = [
            user_email,
        ]
        subject = "Welcome to Bottle CRM"
        html_content = render_to_string("user_status_in.html", context=context)

        msg = EmailMessage(
            subject,
            html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipients,
        )
        msg.content_subtype = "html"
        msg.send()


@app.task
def send_email_user_mentions(
    comment_id,
    called_from,
):
    """Send Mail To Mentioned Users In The Comment"""
    comment = Comment.objects.filter(id=comment_id).first()
    if comment:
        comment_text = comment.comment
        comment_text_list = comment_text.split()
        recipients = []
        for comment_text in comment_text_list:
            if comment_text.startswith("@"):
                if comment_text.strip("@").strip(",") not in recipients:
                    if User.objects.filter(
                        username=comment_text.strip("@").strip(","), is_active=True
                    ).exists():
                        email = (
                            User.objects.filter(
                                username=comment_text.strip("@").strip(",")
                            )
                            .first()
                            .email
                        )
                        recipients.append(email)

        context = {}
        context["commented_by"] = comment.commented_by
        context["comment_description"] = comment.comment
        subject = None
        if called_from == "accounts":
            subject = "New comment on Account. "
        elif called_from == "contacts":
            subject = "New comment on Contact. "
        elif called_from == "leads":
            subject = "New comment on Lead. "
        elif called_from == "opportunity":
            subject = "New comment on Opportunity. "
        elif called_from == "cases":
            subject = "New comment on Case. "
        elif called_from == "tasks":
            subject = "New comment on Task. "
        elif called_from == "invoices":
            subject = "New comment on Invoice. "
        elif called_from == "events":
            subject = "New comment on Event. "
        if subject:
            context["url"] = settings.DOMAIN_NAME
        else:
            context["url"] = ""
        # subject = 'Django CRM : comment '
        if recipients:
            for recipient in recipients:
                recipients_list = [
                    recipient,
                ]
                context["mentioned_user"] = recipient
                html_content = render_to_string("comment_email.html", context=context)
                msg = EmailMessage(
                    subject,
                    html_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=recipients_list,
                )
                msg.content_subtype = "html"
                msg.send()


@app.task
def send_email_user_status(
    user_id,
    status_changed_user="",
):
    """Send Mail To Users Regarding their status i.e active or inactive"""
    user = User.objects.filter(id=user_id).first()
    if user:
        context = {}
        context["message"] = "deactivated"
        context["email"] = user.email
        context["url"] = settings.DOMAIN_NAME
        if user.has_marketing_access:
            context["url"] = context["url"] + "/marketing"
        if user.is_active:
            context["message"] = "activated"
        context["status_changed_user"] = status_changed_user
        if context["message"] == "activated":
            subject = "Account Activated "
            html_content = render_to_string(
                "user_status_activate.html", context=context
            )
        else:
            subject = "Account Deactivated "
            html_content = render_to_string(
                "user_status_deactivate.html", context=context
            )
        recipients = []
        recipients.append(user.email)
        if recipients:
            msg = EmailMessage(
                subject,
                html_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipients,
            )
            msg.content_subtype = "html"
            msg.send()


@app.task
def send_email_user_delete(
    user_email,
    deleted_by="",
):
    """Send Mail To Users When their account is deleted"""
    if user_email:
        context = {}
        context["message"] = "deleted"
        context["deleted_by"] = deleted_by
        context["email"] = user_email
        recipients = []
        recipients.append(user_email)
        subject = "CRM : Your account is Deleted. "
        html_content = render_to_string("user_delete_email.html", context=context)
        if recipients:
            msg = EmailMessage(
                subject,
                html_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipients,
            )
            msg.content_subtype = "html"
            msg.send()


@app.task
def resend_activation_link_to_user(
    user_email="",
):
    """Send Mail To Users When their account is created"""

    user_obj = User.objects.filter(email=user_email).first()
    user_obj.is_active = False
    user_obj.save()
    if user_obj:
        context = {}
        context["user_email"] = user_email
        context["url"] = settings.DOMAIN_NAME
        context["uid"] = (urlsafe_base64_encode(force_bytes(user_obj.pk)),)
        context["token"] = account_activation_token.make_token(user_obj)
        time_delta_two_hours = datetime.datetime.strftime(
            timezone.now() + datetime.timedelta(hours=2), "%Y-%m-%d-%H-%M-%S"
        )
        context["token"] = context["token"]
        activation_key = context["token"] + time_delta_two_hours
        # Profile.objects.filter(user=user_obj).update(
        #     activation_key=activation_key,
        #     key_expires=timezone.now() + datetime.timedelta(hours=2),
        # )
        user_obj.activation_key = activation_key
        user_obj.key_expires = timezone.now() + datetime.timedelta(hours=2)
        user_obj.save()

        context["complete_url"] = context[
            "url"
        ] + "/auth/activate_user/{}/{}/{}/".format(
            context["uid"][0],
            context["token"],
            activation_key,
        )
        recipients = [context["complete_url"]]
        recipients.append(user_email)
        subject = "Welcome to Bottle CRM"
        html_content = render_to_string("user_status_in.html", context=context)
        if recipients:
            msg = EmailMessage(
                subject,
                html_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipients,
            )
            msg.content_subtype = "html"
            msg.send()


@app.task
def send_email_to_reset_password(user_email):
    """Send Mail To Users When their account is created"""
    user = User.objects.filter(email=user_email).first()
    context = {}
    context["user_email"] = user_email
    context["url"] = settings.DOMAIN_NAME
    context["uid"] = (urlsafe_base64_encode(force_bytes(user.pk)),)
    context["token"] = default_token_generator.make_token(user)
    context["token"] = context["token"]
    context["complete_url"] = context[
        "url"
    ] + "/auth/reset-password/{uidb64}/{token}/".format(
        uidb64=context["uid"][0], token=context["token"]
    )
    subject = "Set a New Password"
    recipients = []
    recipients.append(user_email)
    html_content = render_to_string(
        "registration/password_reset_email.html", context=context
    )
    if recipients:
        msg = EmailMessage(
            subject, html_content, from_email=settings.DEFAULT_FROM_EMAIL, to=recipients
        )
        msg.content_subtype = "html"
        msg.send()
