import boto.ses
import sendgrid
import requests
import mandrill
from django.core.mail import EmailMultiAlternatives
from django.conf import settings


def send_mail(mto, mfrom, msubject, mbody, user_active):
    if mfrom:
        mfrom = mfrom
    else:
        mfrom = settings.DEFAULT_FROM_EMAIL
    if user_active:
        mail_sender = settings.MAIL_SENDER
    else:
        mail_sender = settings.INACTIVE_MAIL_SENDER
    if mail_sender == 'AMAZON':
        # conn=SESConnection(settings.AM_ACCESS_KEY, settings.AM_PASS_KEY)
        conn = boto.ses.connect_to_region(
            settings.AWS_REGION,
            aws_access_key_id=settings.AM_ACCESS_KEY,
            aws_secret_access_key=settings.AM_PASS_KEY
        )
        response = conn.send_email(mfrom, msubject, mbody, mto, format='html')
    elif mail_sender == 'MAILGUN':
        response = requests.post(
            settings.MGUN_API_URL,
            auth=('api', settings.MGUN_API_KEY),
            data={
                'from': mfrom,
                'to': mto,
                'subject': msubject,
                'html': mbody,
            })
    elif mail_sender == 'SENDGRID':
        sg = sendgrid.SendGridClient(settings.SG_USER, settings.SG_PWD)
        sending_msg = sendgrid.Mail()
        sending_msg.set_subject(msubject)
        sending_msg.set_html(mbody)
        sending_msg.set_text(msubject)
        sending_msg.set_from(mfrom)
        sending_msg.add_to(mto)
        response = sg.send(sending_msg)
    elif mail_sender == 'MANDRILL':
        api_key = settings.MANDRILL_API_KEY
        mandrill_client = mandrill.Mandrill(api_key)

        message = {
            "html": mbody,
            "subject": msubject,
            "from_email": mfrom,
            "from_name": "Django CRM",
            "to": [{'email': i, 'type': 'to'} for i in mto]
        }
        response = mandrill_client.messages.send(message=message)

    else:
        msg = EmailMultiAlternatives(msubject, mbody, mfrom, [mto])
        msg.attach_alternative(mbody, "text/html")
        response = msg.send()
    return response
