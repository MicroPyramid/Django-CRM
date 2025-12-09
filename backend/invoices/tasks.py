"""
Celery tasks for Invoice module.

Tasks include:
- Email notifications
- Recurring invoice generation
- Overdue invoice checking
- Payment reminders
- Estimate expiry checking
"""

import datetime
import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils import timezone

from common.models import Profile
from common.tasks import set_rls_context

logger = logging.getLogger(__name__)


@shared_task
def send_email(invoice_id, recipients, org_id, domain="localhost", protocol="http"):
    """
    Send notification email when invoice is assigned to users.

    Args:
        invoice_id: UUID of the invoice
        recipients: List of user profile IDs
        org_id: UUID of the organization
        domain: Domain for URL generation
        protocol: HTTP or HTTPS
    """
    from invoices.models import Invoice

    set_rls_context(org_id)
    invoice = Invoice.objects.filter(id=invoice_id).first()
    if not invoice:
        logger.warning(f"Invoice {invoice_id} not found")
        return

    for user_id in recipients:
        profile = Profile.objects.filter(id=user_id, is_active=True).first()
        if profile and profile.user and profile.user.email:
            subject = f"Invoice #{invoice.invoice_number} has been assigned to you"
            context = {
                "invoice": invoice,
                "invoice_title": invoice.invoice_title,
                "invoice_number": invoice.invoice_number,
                "url": f"{protocol}://{domain}/invoices/{invoice.id}",
                "user": profile.user,
                "assigned_by": invoice.created_by.user if invoice.created_by else None,
            }
            html_content = render_to_string(
                "invoices/emails/assigned_to_email.html", context=context
            )
            msg = EmailMessage(
                subject=subject,
                body=html_content,
                to=[profile.user.email],
            )
            msg.content_subtype = "html"
            try:
                msg.send()
                logger.info(
                    f"Sent assignment email for invoice {invoice_id} to {profile.user.email}"
                )
            except Exception as e:
                logger.error(f"Failed to send email: {e}")


@shared_task
def send_invoice_to_client(
    invoice_id, org_id, domain="localhost", protocol="http", include_pdf=True
):
    """
    Send invoice to client via email with optional PDF attachment.

    Args:
        invoice_id: UUID of the invoice
        org_id: UUID of the organization
        domain: Domain for URL generation
        protocol: HTTP or HTTPS
        include_pdf: Whether to attach PDF
    """
    from invoices.models import Invoice
    from invoices.pdf import generate_invoice_filename, generate_invoice_pdf

    set_rls_context(org_id)
    invoice = Invoice.objects.filter(id=invoice_id).first()
    if not invoice:
        logger.warning(f"Invoice {invoice_id} not found")
        return

    if not invoice.client_email:
        logger.warning(f"Invoice {invoice_id} has no client email")
        return

    subject = f"Invoice #{invoice.invoice_number} from {invoice.org.name}"

    # Build public URL if enabled
    public_url = None
    if invoice.public_link_enabled and invoice.public_token:
        public_url = f"{protocol}://{domain}/portal/invoice/{invoice.public_token}"

    context = {
        "invoice": invoice,
        "public_url": public_url,
        "org": invoice.org,
    }
    html_content = render_to_string(
        "invoices/emails/invoice_to_client.html", context=context
    )

    msg = EmailMessage(
        subject=subject,
        body=html_content,
        to=[invoice.client_email],
    )
    msg.content_subtype = "html"

    # Attach PDF if requested
    if include_pdf:
        try:
            pdf_content = generate_invoice_pdf(invoice)
            filename = generate_invoice_filename(invoice)
            msg.attach(filename, pdf_content, "application/pdf")
        except Exception as e:
            logger.error(f"Failed to generate PDF for invoice {invoice_id}: {e}")

    try:
        msg.send()
        # Update invoice
        invoice.is_email_sent = True
        invoice.sent_at = timezone.now()
        if invoice.status == "Draft":
            invoice.status = "Sent"
        invoice.save()
        logger.info(f"Sent invoice {invoice_id} to {invoice.client_email}")
    except Exception as e:
        logger.error(f"Failed to send invoice email: {e}")


@shared_task
def create_invoice_history(invoice_id, updated_by_user_id, changed_fields, org_id):
    """
    Create a history record for invoice changes.

    Args:
        invoice_id: UUID of the invoice
        updated_by_user_id: UUID of the profile who made changes
        changed_fields: List of field names that changed
        org_id: UUID of the organization
    """
    from invoices.models import Invoice, InvoiceHistory

    set_rls_context(org_id)
    invoice = Invoice.objects.filter(id=invoice_id).first()
    if not invoice:
        logger.warning(f"Invoice {invoice_id} not found")
        return

    updated_by = Profile.objects.filter(id=updated_by_user_id).first()

    # Format changed fields message
    if changed_fields:
        changed_data = [
            (" ".join(field.split("_")).title()) for field in changed_fields
        ]
        if len(changed_data) > 1:
            changed_data = (
                ", ".join(changed_data[:-1])
                + " and "
                + changed_data[-1]
                + " have changed."
            )
        elif len(changed_data) == 1:
            changed_data = changed_data[0] + " has changed."
        else:
            changed_data = None
    else:
        changed_data = None

    # First history entry
    if invoice.invoice_history.count() == 0:
        changed_data = "Invoice created."

    InvoiceHistory.objects.create(
        invoice=invoice,
        invoice_title=invoice.invoice_title,
        invoice_number=invoice.invoice_number,
        total_amount=invoice.total_amount,
        currency=invoice.currency,
        updated_by=updated_by,
        created_by=invoice.created_by,
        amount_due=invoice.amount_due,
        client_name=invoice.client_name,
        client_email=invoice.client_email,
        status=invoice.status,
        details=changed_data,
        due_date=invoice.due_date,
        org=invoice.org,
    )
    logger.info(f"Created history entry for invoice {invoice_id}")


@shared_task
def generate_recurring_invoices():
    """
    Generate invoices from active recurring invoice templates.
    Should be scheduled to run daily.
    """
    from invoices.models import Invoice, InvoiceLineItem, RecurringInvoice

    logger.info("Starting recurring invoice generation")
    today = timezone.now().date()

    # Get all active recurring invoices due for generation
    recurring_invoices = RecurringInvoice.objects.filter(
        is_active=True,
        next_generation_date__lte=today,
    ).select_related("org", "account", "contact")

    for recurring in recurring_invoices:
        # Check end date
        if recurring.end_date and recurring.end_date < today:
            recurring.is_active = False
            recurring.save()
            logger.info(
                f"Deactivated recurring invoice {recurring.id} - end date reached"
            )
            continue

        # Set RLS context for this org
        set_rls_context(str(recurring.org.id))

        try:
            # Create new invoice
            invoice = Invoice.objects.create(
                invoice_title=recurring.title,
                status="Draft" if not recurring.auto_send else "Sent",
                account=recurring.account,
                contact=recurring.contact,
                client_name=recurring.client_name,
                client_email=recurring.client_email,
                discount_type=recurring.discount_type,
                discount_value=recurring.discount_value,
                tax_rate=recurring.tax_rate,
                currency=recurring.currency,
                issue_date=today,
                payment_terms=recurring.payment_terms,
                notes=recurring.notes,
                terms=recurring.terms,
                org=recurring.org,
            )

            # Copy line items
            for item in recurring.line_items.all():
                InvoiceLineItem.objects.create(
                    invoice=invoice,
                    product=item.product,
                    name=item.name,
                    description=item.description,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    discount_type=item.discount_type,
                    discount_value=item.discount_value,
                    tax_rate=item.tax_rate,
                    order=item.order,
                    org=recurring.org,
                )

            # Recalculate totals
            invoice.recalculate_totals()
            invoice.save()

            # Update recurring invoice
            recurring.next_generation_date = recurring.calculate_next_date()
            recurring.invoices_generated += 1
            recurring.save()

            logger.info(f"Created invoice {invoice.id} from recurring {recurring.id}")

            # Auto-send if enabled
            if recurring.auto_send:
                send_invoice_to_client.delay(
                    str(invoice.id),
                    str(recurring.org.id),
                    domain=getattr(settings, "DOMAIN_NAME", "localhost"),
                    protocol="https"
                    if getattr(settings, "USE_HTTPS", False)
                    else "http",
                )

        except Exception as e:
            logger.error(
                f"Failed to generate invoice from recurring {recurring.id}: {e}"
            )

    logger.info("Finished recurring invoice generation")


@shared_task
def check_overdue_invoices():
    """
    Mark invoices as overdue if past due date.
    Should be scheduled to run daily.
    """
    from invoices.models import Invoice

    logger.info("Checking for overdue invoices")
    today = timezone.now().date()

    # Find invoices that are past due but not yet marked overdue
    overdue_invoices = Invoice.objects.filter(
        due_date__lt=today,
        status__in=["Sent", "Viewed", "Partially_Paid"],
    )

    count = 0
    for invoice in overdue_invoices:
        set_rls_context(str(invoice.org.id))
        invoice.status = "Overdue"
        invoice.save()
        count += 1
        logger.info(f"Marked invoice {invoice.id} as overdue")

    logger.info(f"Marked {count} invoices as overdue")


@shared_task
def send_payment_reminder(invoice_id, org_id, domain="localhost", protocol="http"):
    """
    Send a payment reminder for an invoice.

    Args:
        invoice_id: UUID of the invoice
        org_id: UUID of the organization
        domain: Domain for URL generation
        protocol: HTTP or HTTPS
    """
    from invoices.models import Invoice

    set_rls_context(org_id)
    invoice = Invoice.objects.filter(id=invoice_id).first()
    if not invoice:
        logger.warning(f"Invoice {invoice_id} not found")
        return

    if not invoice.client_email:
        logger.warning(f"Invoice {invoice_id} has no client email")
        return

    # Don't send reminders for paid or cancelled invoices
    if invoice.status in ["Paid", "Cancelled"]:
        logger.info(f"Skipping reminder for {invoice_id} - status is {invoice.status}")
        return

    subject = f"Payment Reminder: Invoice #{invoice.invoice_number}"

    public_url = None
    if invoice.public_link_enabled and invoice.public_token:
        public_url = f"{protocol}://{domain}/portal/invoice/{invoice.public_token}"

    context = {
        "invoice": invoice,
        "public_url": public_url,
        "org": invoice.org,
        "days_overdue": (timezone.now().date() - invoice.due_date).days
        if invoice.due_date
        else 0,
    }
    html_content = render_to_string(
        "invoices/emails/payment_reminder.html", context=context
    )

    msg = EmailMessage(
        subject=subject,
        body=html_content,
        to=[invoice.client_email],
    )
    msg.content_subtype = "html"

    try:
        msg.send()
        invoice.last_reminder_sent = timezone.now()
        invoice.reminder_count += 1
        invoice.save()
        logger.info(f"Sent payment reminder for invoice {invoice_id}")
    except Exception as e:
        logger.error(f"Failed to send payment reminder: {e}")


@shared_task
def process_payment_reminders():
    """
    Process all invoices that need payment reminders.
    Should be scheduled to run daily.
    """
    from invoices.models import Invoice

    logger.info("Processing payment reminders")
    today = timezone.now().date()

    # Get invoices with reminders enabled
    invoices = (
        Invoice.objects.filter(
            reminder_enabled=True,
            status__in=["Sent", "Viewed", "Partially_Paid", "Overdue"],
        )
        .exclude(client_email__isnull=True)
        .exclude(client_email="")
    )

    for invoice in invoices:
        set_rls_context(str(invoice.org.id))

        # Check if we should send a reminder
        should_send = False
        days_until_due = (invoice.due_date - today).days if invoice.due_date else None

        # Determine reminder interval based on frequency setting
        reminder_interval_days = 7  # default
        if invoice.reminder_frequency == "ONCE":
            reminder_interval_days = 9999  # effectively only once
        elif invoice.reminder_frequency == "WEEKLY":
            reminder_interval_days = 7

        # Before due date reminder
        if days_until_due is not None and days_until_due > 0:
            if (
                invoice.reminder_days_before
                and days_until_due <= invoice.reminder_days_before
            ):
                # Check if we haven't sent a reminder recently
                if not invoice.last_reminder_sent or (
                    (today - invoice.last_reminder_sent.date()).days
                    >= reminder_interval_days
                ):
                    should_send = True

        # After due date reminder
        elif days_until_due is not None and days_until_due < 0:
            days_overdue = abs(days_until_due)
            if (
                invoice.reminder_days_after
                and days_overdue >= invoice.reminder_days_after
            ):
                # Check reminder frequency
                if not invoice.last_reminder_sent or (
                    (today - invoice.last_reminder_sent.date()).days
                    >= reminder_interval_days
                ):
                    should_send = True

        if should_send:
            send_payment_reminder.delay(
                str(invoice.id),
                str(invoice.org.id),
                domain=getattr(settings, "DOMAIN_NAME", "localhost"),
                protocol="https" if getattr(settings, "USE_HTTPS", False) else "http",
            )

    logger.info("Finished processing payment reminders")


@shared_task
def check_expired_estimates():
    """
    Mark estimates as expired if past valid_until date.
    Should be scheduled to run daily.
    """
    from invoices.models import Estimate

    logger.info("Checking for expired estimates")
    today = timezone.now().date()

    # Find estimates that are past expiry_date but not yet marked expired
    expired_estimates = Estimate.objects.filter(
        expiry_date__lt=today,
        status__in=["Draft", "Sent", "Viewed"],
    )

    count = 0
    for estimate in expired_estimates:
        set_rls_context(str(estimate.org.id))
        estimate.status = "Expired"
        estimate.save()
        count += 1
        logger.info(f"Marked estimate {estimate.id} as expired")

    logger.info(f"Marked {count} estimates as expired")


@shared_task
def send_estimate_to_client(
    estimate_id, org_id, domain="localhost", protocol="http", include_pdf=True
):
    """
    Send estimate to client via email with optional PDF attachment.

    Args:
        estimate_id: UUID of the estimate
        org_id: UUID of the organization
        domain: Domain for URL generation
        protocol: HTTP or HTTPS
        include_pdf: Whether to attach PDF
    """
    from invoices.models import Estimate
    from invoices.pdf import generate_estimate_filename, generate_estimate_pdf

    set_rls_context(org_id)
    estimate = Estimate.objects.filter(id=estimate_id).first()
    if not estimate:
        logger.warning(f"Estimate {estimate_id} not found")
        return

    if not estimate.client_email:
        logger.warning(f"Estimate {estimate_id} has no client email")
        return

    subject = f"Estimate #{estimate.estimate_number} from {estimate.org.name}"

    public_url = None
    if estimate.public_link_enabled and estimate.public_token:
        public_url = f"{protocol}://{domain}/portal/estimate/{estimate.public_token}"

    context = {
        "estimate": estimate,
        "public_url": public_url,
        "org": estimate.org,
    }
    html_content = render_to_string(
        "invoices/emails/estimate_to_client.html", context=context
    )

    msg = EmailMessage(
        subject=subject,
        body=html_content,
        to=[estimate.client_email],
    )
    msg.content_subtype = "html"

    if include_pdf:
        try:
            pdf_content = generate_estimate_pdf(estimate)
            filename = generate_estimate_filename(estimate)
            msg.attach(filename, pdf_content, "application/pdf")
        except Exception as e:
            logger.error(f"Failed to generate PDF for estimate {estimate_id}: {e}")

    try:
        msg.send()
        estimate.sent_at = timezone.now()
        if estimate.status == "Draft":
            estimate.status = "Sent"
        estimate.save()
        logger.info(f"Sent estimate {estimate_id} to {estimate.client_email}")
    except Exception as e:
        logger.error(f"Failed to send estimate email: {e}")
