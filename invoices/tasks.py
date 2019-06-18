from celery.task import task
from django.conf import settings
from django.core.mail import EmailMessage
from django.shortcuts import reverse
from django.template.loader import render_to_string

from common.models import User
from invoices.models import Invoice


@task
def send_email(invoice_id, domain='demo.django-crm.io', protocol='http'):
    invoice = Invoice.objects.filter(id=invoice_id).first()
    if invoice:
        subject = 'Invoice : {0}'.format(invoice.invoice_title)
        context = {}
        context['invoice_title'] = invoice.invoice_title
        context['invoice_id'] = invoice_id
        context['invoice_created_by'] = invoice.created_by
        context["url"] = protocol + '://' + domain + \
            reverse('invoices:invoice_details', args=(invoice.id,))
        recipients = invoice.assigned_to.all()
        if recipients.count() > 0:
            for recipient in recipients:
                context['user'] = recipient.email
                html_content = render_to_string(
                    'assigned_to_email_template.html', context=context)
                msg = EmailMessage(
                    subject=subject, body=html_content, to=[recipient.email, ])
                msg.content_subtype = "html"
                msg.send()


@task
def send_invoice_email(invoice_id, domain='demo.django-crm.io', protocol='http'):
    invoice = Invoice.objects.filter(id=invoice_id).first()
    if invoice:
        subject = 'CRM Invoice : {0}'.format(invoice.invoice_title)
        recipients = [invoice.email]
        context = {}
        context['invoice'] = invoice
        context['url'] = protocol + '://' + domain + \
            reverse('invoices:invoice_details', args=(invoice.id,))
        html_content = render_to_string(
            'invoice_detail_email.html', context=context)
        msg = EmailMessage(subject=subject, body=html_content,
                           to=recipients)
        msg.content_subtype = "html"
        msg.send()


@task
def send_invoice_email_cancel(invoice_id, domain='demo.django-crm.io', protocol='http'):
    invoice = Invoice.objects.filter(id=invoice_id).first()
    if invoice:
        subject = 'CRM Invoice : {0}'.format(invoice.invoice_title)
        recipients = [invoice.email]
        context = {}
        context['invoice'] = invoice
        context['url'] = protocol + '://' + domain + \
            reverse('invoices:invoice_details', args=(invoice.id,))
        html_content = render_to_string(
            'invoice_cancelled.html', context=context)
        msg = EmailMessage(subject=subject, body=html_content,
                           to=recipients)
        msg.content_subtype = "html"
        msg.send()
