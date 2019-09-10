from datetime import datetime, timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from accounts.models import Account
from common.models import Address, Attachments, Comment, User
from invoices.models import Invoice, InvoiceHistory
from teams.models import Teams


class InvoiceCreateTest(object):

    def setUp(self):
        self.user = User.objects.create(
            first_name="johnInvoice", username='johnDoeInvoice', email='johnDoeInvoice@example.com', role='ADMIN')
        self.user.set_password('password')
        self.user.save()

        self.user1 = User.objects.create(
            first_name="janeInvoice",
            username='janeDoeInvoice',
            email='janeDoeInvoice@example.com',
            role="USER",
            has_sales_access=True)
        self.user1.set_password('password')
        self.user1.save()

        self.user2 = User.objects.create(
            first_name="joeInvoice",
            username='joeInvoice',
            email='joeInvoice@example.com',
            role="USER",
            has_sales_access=True)
        self.user2.set_password('password')
        self.user2.save()

        self.team_dev = Teams.objects.create(name='invoices teams')
        self.team_dev.users.add(self.user2.id)

        self.account = Account.objects.create(
            name="john invoice", email="johnDoeInvoice@example.com", phone="123456789",
            billing_address_line="", billing_street="street name",
            billing_city="city name",
            billing_state="state", billing_postcode="1234",
            billing_country="US",
            website="www.example.como", created_by=self.user, status="open",
            industry="SOFTWARE", description="Testing")
        self.account.assigned_to.add(self.user1.id)

        self.from_address = Address.objects.create(
            street="from street number",
            city="from city",
            state="from state",
            postcode=12346, country="IN")

        self.to_address = Address.objects.create(
            street="to street number",
            city="to city",
            state="to state",
            postcode=12346, country="IN")

        self.invoice = Invoice.objects.create(
            invoice_title='invoice title',
            invoice_number='invoice number',
            currency='USD',
            email='invoiceTitle@email.com',
            due_date=(datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'),
            total_amount='1000',
            created_by=self.user,
            from_address=self.from_address,
            to_address=self.to_address,
        )
        self.invoice.assigned_to.add(self.user1.id)
        self.invoice.accounts.add(self.account.id)

        self.invoice_history = InvoiceHistory.objects.create(
            invoice_title='invoice title',
            invoice_number='invoice number',
            currency='USD',
            email='invoiceTitle@email.com',
            due_date=(datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'),
            total_amount='1000',
            from_address=self.from_address,
            to_address=self.to_address,
            invoice=self.invoice
        )

        self.invoice_1 = Invoice.objects.create(
            invoice_title='invoice title',
            invoice_number='invoice_1 number',
            currency='USD',
            email='invoiceTitle@email.com',
            due_date=(datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'),
            total_amount='1000',
            created_by=self.user1
        )
        self.invoice_1.assigned_to.add(self.user2.id)
        self.invoice_1.assigned_to.add(self.user1.id)
        self.invoice_1.accounts.add(self.account.id)

        self.comment = Comment.objects.create(
            comment='test comment', invoice=self.invoice,
            commented_by=self.user
        )
        self.attachment = Attachments.objects.create(
            attachment='image.png', invoice=self.invoice,
            created_by=self.user
        )


class InvoiceListTestCase(InvoiceCreateTest, TestCase):

    def test_invoices_list(self):
        self.client.login(email='johnDoeInvoice@example.com',
                          password='password')
        response = self.client.get(reverse('invoices:invoices_list'))
        self.assertEqual(response.status_code, 200)

        self.client.login(email='janeDoeInvoice@example.com',
                          password='password')
        response = self.client.get(reverse('invoices:invoices_list'))
        self.assertEqual(response.status_code, 200)

        data = {
            'invoice_title_number': 'title',
            'created_by': self.user.id,
            'assigned_to': self.user1.id,
            'status': 'Draft',
            'total_amount': '1000',
        }
        self.client.login(email='johnDoeInvoice@example.com',
                          password='password')
        response = self.client.post(reverse('invoices:invoices_list'), data)
        self.assertEqual(response.status_code, 200)

        self.client.login(email='janeDoeInvoice@example.com',
                          password='password')
        response = self.client.post(reverse('invoices:invoices_list'), data)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(str(self.invoice), 'invoice number')
        self.assertEqual(str(self.invoice.formatted_rate()), '0 USD')
        self.assertEqual(str(self.invoice.formatted_total_quantity()), '0 Hours')

        self.assertEqual(str(self.invoice_history), 'invoice number')
        self.assertEqual(str(self.invoice_history.formatted_rate()), '0 USD')
        self.assertEqual(str(self.invoice_history.formatted_total_quantity()), '0 Hours')
        self.assertEqual(str(self.invoice_history.formatted_total_amount()), 'USD 1000')

        self.assertTrue(self.invoice_history.created_on_arrow in ['just now' or 'seconds ago'])



class InvoiceAddTestCase(InvoiceCreateTest, TestCase):

    def test_invoices_create(self):
        self.client.login(email='johnDoeInvoice@example.com',
                          password='password')
        response = self.client.get(reverse('invoices:invoices_create'))
        self.assertEqual(response.status_code, 200)

        data = {
            'invoice_title': 'invoice title create',
            'status': 'Draft',
            'invoice_number': 'invoice number',
            'currency': 'INR',
            'email': 'invoice@example.com',
            'due_data': (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'),
            'total_amount': '1234',
            'teams': self.team_dev.id,
            'accounts': self.account.id,
            'assigned_to': self.user1.id,
        }

        response = self.client.post(reverse('invoices:invoices_create'), data)
        self.assertEqual(response.status_code, 200)

        data = {
            'invoice_title': 'invoice title',
            'status': 'Draft',
            'invoice_number': 'INV123',
            'currency': 'INR',
            'email': 'invoice@example.com',
            'due_date': (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'),
            'total_amount': '1234',
            'teams': self.team_dev.id,
            'accounts': self.account.id,
            'assigned_to': self.user1.id,
            'quantity': 0,
        }
        response = self.client.post(reverse('invoices:invoices_create'), data)
        self.assertEqual(response.status_code, 200)

        data = {
            'invoice_title': 'invoice title',
            'status': 'Draft',
            'invoice_number': 'INV1234',
            'currency': 'INR',
            'email': 'invoice@example.com',
            'due_date': (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'),
            'total_amount': '1234',
            'teams': self.team_dev.id,
            'accounts': self.account.id,
            'assigned_to': self.user1.id,
            'quantity': 0,
            'from_account': self.account.id
        }
        response = self.client.post(reverse('invoices:invoices_create'), data)
        self.assertEqual(response.status_code, 200)

        self.client.login(email='janeDoeInvoice@example.com',
                          password='password')
        response = self.client.get(reverse('invoices:invoices_list'))
        self.assertEqual(response.status_code, 200)


class InvoiceDetailTestCase(InvoiceCreateTest, TestCase):

    def test_invoices_detail(self):
        self.client.login(email='johnDoeInvoice@example.com',
                          password='password')
        response = self.client.get(
            reverse('invoices:invoice_details', args=(self.invoice.id,)))
        self.assertEqual(response.status_code, 200)

        self.client.login(email='janeDoeInvoice@example.com',
                          password='password')
        response = self.client.get(
            reverse('invoices:invoice_details', args=(self.invoice.id,)))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(
            reverse('invoices:invoice_details', args=(self.invoice_1.id,)))
        self.assertEqual(response.status_code, 200)

        self.client.login(email='joeInvoice@example.com',
                          password='password')
        response = self.client.get(
            reverse('invoices:invoice_details', args=(self.invoice.id,)))
        self.assertEqual(response.status_code, 403)


class InvoiceEditTestCase(InvoiceCreateTest, TestCase):

    def test_invoices_edit(self):
        self.client.login(email='johnDoeInvoice@example.com',
                          password='password')
        response = self.client.get(
            reverse('invoices:invoice_edit', args=(self.invoice.id,)))
        self.assertEqual(response.status_code, 200)

        self.client.login(email='janeDoeInvoice@example.com',
                          password='password')
        response = self.client.get(
            reverse('invoices:invoice_edit', args=(self.invoice_1.id,)))
        self.assertEqual(response.status_code, 200)

        self.client.login(email='joeInvoice@example.com',
                          password='password')
        response = self.client.get(
            reverse('invoices:invoice_edit', args=(self.invoice.id,)))
        self.assertEqual(response.status_code, 403)

        data = {
            'invoice_title': 'invoice title',
            'status': 'Draft',
            'invoice_number': 'INV1234',
            'currency': 'INR',
            'email': 'invoice@example.com',
            'due_date': (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'),
            'total_amount': '1234',
            'teams': self.team_dev.id,
            'accounts': self.account.id,
            'assigned_to': self.user1.id,
            'quantity': 0,
            'from_account': self.account.id,
            'from-address_line': '',
            'from-street': '',
            'from-city': '',
            'from-state': '',
            'from-postcode': '',
            'from-country': '',
            'to-address_line': '',
            'to-street': '',
            'to-city': '',
            'to-state': '',
            'to-postcode': '',
            'to-country': '',
        }

        self.client.login(email='johnDoeInvoice@example.com',
                          password='password')
        response = self.client.post(
            reverse('invoices:invoice_edit', args=(self.invoice.id,)), data)
        self.assertEqual(response.status_code, 200)

        data.pop('from_account')
        self.client.login(email='johnDoeInvoice@example.com',
                          password='password')
        response = self.client.post(
            reverse('invoices:invoice_edit', args=(self.invoice.id,)), data)
        self.assertEqual(response.status_code, 200)

        data.pop('invoice_number')
        self.client.login(email='johnDoeInvoice@example.com',
                          password='password')
        response = self.client.post(
            reverse('invoices:invoice_edit', args=(self.invoice.id,)), data)
        self.assertEqual(response.status_code, 200)


class InvoiceSendMailTestCase(InvoiceCreateTest, TestCase):

    def test_invoices_send_mail(self):

        self.client.login(email='joeInvoice@example.com',
                          password='password')
        response = self.client.get(
            reverse('invoices:invoice_send_mail', args=(self.invoice_1.id,)))
        self.assertEqual(response.status_code, 403)

        self.client.login(email='janeDoeInvoice@example.com',
                          password='password')
        response = self.client.get(
            reverse('invoices:invoice_send_mail', args=(self.invoice_1.id,)))
        self.assertEqual(response.status_code, 302)


class InvoiceChangeStatusPaidTestCase(InvoiceCreateTest, TestCase):

    def test_invoices_change_status_to_paid(self):

        self.client.login(email='joeInvoice@example.com',
                          password='password')
        response = self.client.get(
            reverse('invoices:invoice_change_status_paid', args=(self.invoice_1.id,)))
        self.assertEqual(response.status_code, 403)

        self.client.login(email='janeDoeInvoice@example.com',
                          password='password')
        response = self.client.get(
            reverse('invoices:invoice_change_status_paid', args=(self.invoice_1.id,)))
        self.assertEqual(response.status_code, 302)


class InvoiceChangeStatusCancelledTestCase(InvoiceCreateTest, TestCase):

    def test_invoices_change_status_to_cancelled(self):

        self.client.login(email='joeInvoice@example.com',
                          password='password')
        response = self.client.get(
            reverse('invoices:invoice_change_status_cancelled', args=(self.invoice_1.id,)))
        self.assertEqual(response.status_code, 403)

        self.client.login(email='janeDoeInvoice@example.com',
                          password='password')
        response = self.client.get(
            reverse('invoices:invoice_change_status_cancelled', args=(self.invoice_1.id,)))
        self.assertEqual(response.status_code, 302)


class InvoiceDownloadTestCase(InvoiceCreateTest, TestCase):

    def test_invoices_download(self):

        self.client.login(email='joeInvoice@example.com',
                          password='password')
        response = self.client.get(
            reverse('invoices:invoice_download', args=(self.invoice.id,)))
        self.assertEqual(response.status_code, 403)

        # self.client.login(email='johnDoeInvoice@example.com',
        #                   password='password')
        # response = self.client.get(
        #     reverse('invoices:invoice_download', args=(self.invoice_1.id,)))
        # self.assertEqual(response.status_code, 200)


class AddCommentTestCase(InvoiceCreateTest, TestCase):

    def test_invoice_add_comment(self):

        self.client.login(email='johnDoeInvoice@example.com', password='password')
        data = {
            'comment': '',
            'invoice_id': self.invoice.id,
        }
        response = self.client.post(
            reverse('invoices:add_comment'), data)
        self.assertEqual(response.status_code, 200)

        data = {
            'comment': 'test comment invoice',
            'invoice_id': self.invoice.id,
        }
        response = self.client.post(
            reverse('invoices:add_comment'), data)
        self.assertEqual(response.status_code, 200)

        self.client.login(email='janeDoeInvoice@example.com', password='password')
        response = self.client.post(
            reverse('invoices:add_comment'), data)
        self.assertEqual(response.status_code, 200)


class UpdateCommentTestCase(InvoiceCreateTest, TestCase):

    def test_invoice_update_comment(self):

        self.client.login(email='johnDoeInvoice@example.com', password='password')
        data = {
            'commentid': self.comment.id,
            'invoice_id': self.invoice.id,
            'comment': ''
        }
        response = self.client.post(
            reverse('invoices:edit_comment'), data)
        self.assertEqual(response.status_code, 200)

        data = {
            'comment': 'test comment',
            'commentid': self.comment.id,
            'invoice_id': self.invoice.id,
        }
        response = self.client.post(
            reverse('invoices:edit_comment'), data)
        self.assertEqual(response.status_code, 200)

        self.client.login(email='janeDoeInvoice@example.com', password='password')
        response = self.client.post(
            reverse('invoices:edit_comment'), data)
        self.assertEqual(response.status_code, 200)


class DeleteCommentTestCase(InvoiceCreateTest, TestCase):

    def test_invoice_delete_comment(self):

        data = {
            'comment_id': self.comment.id,
        }
        self.client.login(email='janeDoeInvoice@example.com', password='password')
        response = self.client.post(
            reverse('invoices:remove_comment'), data)
        self.assertEqual(response.status_code, 200)

        self.client.login(email='johnDoeInvoice@example.com', password='password')
        response = self.client.post(
            reverse('invoices:remove_comment'), data)
        self.assertEqual(response.status_code, 200)


class AddAttachmentTestCase(InvoiceCreateTest, TestCase):

    def test_invoice_add_attachment(self):

        data = {
            'attachment': SimpleUploadedFile('file_name.txt', bytes('file contents.', 'utf-8')),
            'invoice_id': self.invoice.id
        }
        self.client.login(email='johnDoeInvoice@example.com', password='password')
        response = self.client.post(
            reverse('invoices:add_attachment'), data)
        self.assertEqual(response.status_code, 200)

        self.client.login(email='janeDoeInvoice@example.com', password='password')
        response = self.client.post(
            reverse('invoices:add_attachment'), data)
        self.assertEqual(response.status_code, 200)

        data = {
            'attachment': '',
            'invoice_id': self.invoice.id
        }
        self.client.login(email='johnDoeInvoice@example.com', password='password')
        response = self.client.post(
            reverse('invoices:add_attachment'), data)
        self.assertEqual(response.status_code, 200)


class DeleteAttachmentTestCase(InvoiceCreateTest, TestCase):

    def test_invoice_delete_attachment(self):

        data = {
            'attachment_id': self.attachment.id,
        }
        self.client.login(email='janeDoeInvoice@example.com', password='password')
        response = self.client.post(
            reverse('invoices:remove_attachment'), data)
        self.assertEqual(response.status_code, 200)

        self.client.login(email='johnDoeInvoice@example.com', password='password')
        response = self.client.post(
            reverse('invoices:remove_attachment'), data)
        self.assertEqual(response.status_code, 200)


class InvoiceDeleteTestCase(InvoiceCreateTest, TestCase):

    def test_invoices_delete(self):

        self.client.login(email='joeInvoice@example.com',
                          password='password')
        response = self.client.get(
            reverse('invoices:invoice_delete', args=(self.invoice_1.id,)))
        self.assertEqual(response.status_code, 403)

        self.client.login(email='janeDoeInvoice@example.com',
                          password='password')
        response = self.client.get(
            reverse('invoices:invoice_delete', args=(self.invoice_1.id,)))
        self.assertEqual(response.status_code, 302)

        self.client.login(email='johnDoeInvoice@example.com',
                          password='password')
        self.invoice.status = 'Sent'
        self.invoice.is_email_sent = False
        self.invoice.save()
        self.assertEqual(self.invoice.is_sent(), True)
        self.invoice.status = 'Sent'
        self.invoice.is_email_sent = True
        self.invoice.save()
        self.assertEqual(self.invoice.is_resent(), True)
        self.assertEqual(self.invoice.is_draft(), False)
        self.invoice.status = 'Paid'
        self.invoice.save()
        self.assertEqual(self.invoice.is_paid_or_cancelled(), True)
        response = self.client.get(
            reverse('invoices:invoice_delete', args=(self.invoice.id,)) + '?view_account={}'.format(self.account.id,))
        self.assertEqual(response.status_code, 302)
