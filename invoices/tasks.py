from celery.task import task
from django.conf import settings
from django.core.mail import EmailMessage
from django.shortcuts import reverse
from django.template.loader import render_to_string

from common.models import User
from invoices.models import Invoice, InvoiceHistory
from marketing.models import BlockedDomain, BlockedEmail


@task
def send_email(invoice_id, recipients, domain='demo.django-crm.io', protocol='http'):
    invoice = Invoice.objects.filter(id=invoice_id).first()
    created_by = invoice.created_by
    blocked_domains = BlockedDomain.objects.values_list('domain', flat=True)
    blocked_emails = BlockedEmail.objects.values_list('email', flat=True)
    for user in recipients:
        recipients_list = []
        user = User.objects.filter(id=user, is_active=True).first()
        if user:
            if (user.email not in blocked_emails) and (user.email.split('@')[-1] not in blocked_domains):
                recipients_list.append(user.email)
                subject = 'Shared an invoice with you.'
                context = {}
                context['invoice_title'] = invoice.invoice_title
                context['invoice_id'] = invoice_id
                context['invoice_created_by'] = invoice.created_by
                context["url"] = protocol + '://' + domain + \
                    reverse('invoices:invoice_details', args=(invoice.id,))

                context['user'] = user
                html_content = render_to_string(
                    'assigned_to_email_template.html', context=context)
                msg = EmailMessage(
                    subject=subject, body=html_content, to=recipients_list)
                msg.content_subtype = "html"
                msg.send()
    recipients = invoice.accounts.filter(status='open')
    if recipients.count() > 0:
        subject = 'Shared an invoice with you.'
        context = {}
        context['invoice_title'] = invoice.invoice_title
        context['invoice_id'] = invoice_id
        context['invoice_created_by'] = invoice.created_by
        context["url"] = protocol + '://' + domain + \
            reverse('invoices:invoice_details', args=(invoice.id,))
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


@task
def create_invoice_history(original_invoice_id, updated_by_user_id, changed_fields):
    """original_invoice_id, updated_by_user_id, changed_fields"""
    original_invoice = Invoice.objects.filter(id=original_invoice_id).first()
    created_by = original_invoice.created_by
    updated_by_user = User.objects.get(id=updated_by_user_id)
    changed_data = [(' '.join(field.split('_')).title()) for field in changed_fields]
    if len(changed_data) > 1:
        changed_data = ', '.join(changed_data[:-1]) + ' and ' + changed_data[-1] + ' have changed.'
    elif len(changed_data) == 1:
        changed_data = ', '.join(changed_data) + ' has changed.'
    else:
        changed_data = None

    if original_invoice.invoice_history.count() == 0:
        changed_data = 'Invoice Created.'
    if original_invoice:
        invoice_history = InvoiceHistory()
        invoice_history.invoice = original_invoice
        invoice_history.invoice_title = original_invoice.invoice_title
        invoice_history.invoice_number = original_invoice.invoice_number
        invoice_history.from_address = original_invoice.from_address
        invoice_history.to_address = original_invoice.to_address
        invoice_history.name = original_invoice.name
        invoice_history.email = original_invoice.email
        invoice_history.quantity = original_invoice.quantity
        invoice_history.rate = original_invoice.rate
        invoice_history.total_amount = original_invoice.total_amount
        invoice_history.currency = original_invoice.currency
        invoice_history.phone = original_invoice.phone
        invoice_history.updated_by = updated_by_user
        invoice_history.created_by = original_invoice.created_by
        invoice_history.amount_due = original_invoice.amount_due
        invoice_history.amount_paid = original_invoice.amount_paid
        invoice_history.is_email_sent = original_invoice.is_email_sent
        invoice_history.status = original_invoice.status
        invoice_history.details = changed_data
        invoice_history.due_date = original_invoice.due_date
        invoice_history.save()
        invoice_history.assigned_to.set(original_invoice.assigned_to.all())
