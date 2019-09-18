from django.test import TestCase
from django.test.utils import override_settings

from invoices.tasks import (send_email, send_invoice_email,
                            send_invoice_email_cancel)
from invoices.tests import InvoiceCreateTest


class TestSendMailOnInvoiceCreationTask(InvoiceCreateTest, TestCase):

    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                       CELERY_ALWAYS_EAGER=True,
                       BROKER_BACKEND='memory')
    def test_send_mail_on_invoice_creation_task(self):
        task = send_email.apply((self.invoice.id, [self.user.id, self.user1.id]))
        self.assertEqual('SUCCESS', task.state)

        task = send_invoice_email.apply((self.invoice.id,))
        self.assertEqual('SUCCESS', task.state)

        task = send_invoice_email_cancel.apply((self.invoice.id,))
        self.assertEqual('SUCCESS', task.state)
