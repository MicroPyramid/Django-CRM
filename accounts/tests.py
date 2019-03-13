from django.test import TestCase
from cases.models import Case
from accounts.models import Account
from common.models import User, Comment, Attachments


class AccountCreateTest(object):
    def setUp(self):
        self.user = User.objects.create(
            first_name="mike", username='mike', email='u@mp.com', role='ADMIN')
        self.user.set_password('mike2293')
        self.user.save()

        self.account = Account.objects.create(
            name="mike", email="mike@micropyramid.com", phone="8333855552",
            billing_address_line="", billing_street="KPHB",
            billing_city="New York",
            billing_state="usa", billing_postcode="500073",
            billing_country="IN",
            website="www.mike.com", created_by=self.user,
            industry="SOFTWARE", description="Yes.. Testing Done")
        self.case = Case.objects.create(
            name="raghu", case_type="Problem",
            status="New", account=self.account,
            priority="Low", description="something",
            created_by=self.user, closed_on="2016-05-04")
        self.comment = Comment.objects.create(
            comment='testikd', case=self.case,
            commented_by=self.user
        )
        self.attachment = Attachments.objects.create(
            attachment='image.png', case=self.case,
            created_by=self.user, account=self.account
        )
        self.client.login(email='u@mp.com', password='mike2293')


class AccountsCreateTestCase(AccountCreateTest, TestCase):
    def test_account_create_url(self):
        response = self.client.get('/accounts/create/', {
            'name': "mike", 'email': "mike@micropyramid.com",
            'phone': "",
            'billing_address_line': "",
            'billing_street': "KPHB",
            'billing_city': "New York",
            'billing_state': "usa",
            'billing_postcode': "500073",
            'billing_country': "IN",
            'website': "www.mike.com",
            'industry': "SOFTWARE", 'description': "Yes.. Testing Done"})
        self.assertEqual(response.status_code, 200)

    def test_account_create_html(self):
        response = self.client.get('/accounts/create/', {
            'name': "mike", 'email': "mike@micropyramid.com", 'phone': "",
            'billing_address_line': "",
            'billing_street': "KPHB",
            'billing_city': "New York",
            'billing_state': "usa",
            'billing_postcode': "500073",
            'billing_country': "IN",
            'website': "www.mike.com",
            'industry': "SOFTWARE", 'description': "Yes.. Testing Done"})
        self.assertTemplateUsed(response, 'create_account.html')


class AccountsListTestCase(AccountCreateTest, TestCase):

    def test_accounts_list(self):
        self.accounts = Account.objects.all()
        response = self.client.get('/accounts/list/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts.html')

    def test_accounts_list_queryset(self):
        self.account = Account.objects.all()
        data = {'name': 'name', 'city': 'city',
                'billing_address_line': "billing_address_line",
                'billing_street': "billing_street",
                'billing_city': "billing_city",
                'billing_state': "billing_state",
                'billing_postcode': "billing_postcode",
                'billing_country': "billing_country"}
        response = self.client.post('/accounts/list/', data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts.html')


class AccountsCountTestCase(AccountCreateTest, TestCase):
    def test_accounts_list_count(self):
        count = Account.objects.all().count()
        self.assertEqual(count, 1)


class AccountsViewTestCase(AccountCreateTest, TestCase):
    def test_accounts_view(self):
        self.accounts = Account.objects.all()
        response = self.client.get(
            '/accounts/' + str(self.account.id) + '/view/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'view_account.html')


class AccountsRemoveTestCase(AccountCreateTest, TestCase):
    def test_accounts_remove(self):
        response = self.client.get(
            '/accounts/' + str(self.account.id) + '/delete/')
        self.assertEqual(response['location'], '/accounts/list/')

    # def test_accounts_remove_status(self):
    #     Account.objects.filter(id=self.account.id).delete()
    #     response = self.client.get('/accounts/list/')
    #     self.assertEqual(response.status_code, 200)


class AccountsUpdateUrlTestCase(AccountCreateTest, TestCase):
    def test_accounts_update(self):
        response = self.client.get(
            '/accounts/' + str(self.account.id) + '/edit/', {
                'name': "mike",
                'email': "mike@micropyramid.com", 'phone': "8333855552",
                'billing_address_line': "",
                'billing_street': "KPHB",
                'billing_city': "New York",
                'billing_state': "usa",
                'billing_postcode': "500073",
                'billing_country': "IN",
                'website': "www.mike.com",
                'industry': "SOFTWARE",
                'description': "Yes.. Testing Done"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create_account.html')

    def test_accounts_update_post(self):
        response = self.client.post(
            '/accounts/' + str(self.account.id) + '/edit/',
            {
                'name': "dolly", 'email': "dolly@micropyramid.com",
                'phone': "9555333123",
                'billing_address_line': "",
                'billing_street': "KPHB",
                'billing_city': "New York",
                'billing_state': "usa",
                'billing_postcode': "500073",
                'billing_country': "IN",
                'website': "www.dolly.com",
                'industry': "SOFTWARE", 'description': "Yes.. Testing Done"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create_account.html')

    def test_accounts_update_status(self):
        response = self.client.get(
            '/accounts/' + str(self.account.id) + '/edit/')
        self.assertEqual(response.status_code, 200)

    def test_accounts_update_html(self):
        response = self.client.get(
            '/accounts/' + str(self.account.id) + '/edit/')
        self.assertTemplateUsed(response, 'create_account.html')


class AccountCreateEmptyFormTestCase(AccountCreateTest, TestCase):

    def test_account_creation_invalid_data(self):
        data = {'name': "", 'email': "", 'phone': "",
                'website': "", 'industry': "",
                'description': "",
                'billing_address_line': "",
                'billing_street': "KPHB",
                'billing_city': "New York",
                'billing_state': "usa",
                'billing_postcode': "500073",
                'billing_country': "IN"}
        response = self.client.post('/accounts/create/', data)
        self.assertEqual(response.status_code, 200)


class AccountModelTest(AccountCreateTest, TestCase):

    def test_string_representation(self):
        account = Account(name="My entry title", )
        self.assertEqual(str(account), account.name)

    def setUp(self):
        self.user = User.objects.create(
            username='username', email='email@email.com')


class CommentTestCase(AccountCreateTest, TestCase):
    def test_comment_add(self):
        response = self.client.post(
            '/accounts/comment/add/', {'accountid': self.account.id})
        self.assertEqual(response.status_code, 200)

    def test_comment_edit(self):
        response = self.client.post(
            '/accounts/comment/edit/', {'commentid': self.comment.id})
        self.assertEqual(response.status_code, 200)

    # def test_comment_valid(self):
    #     url = "/accounts/comment/add/"
    #     data = {"comment": "hai", "commented_by": self.user,
    #             "account": self.account}
    #     response = self.client.post(url, data)
    #     print(url,response)
    #     self.assertEqual(response.status_code, 200)

    def test_comment_delete(self):
        response = self.client.post(
            '/accounts/comment/remove/', {'comment_id': self.comment.id})
        self.assertEqual(response.status_code, 200)


class AttachmentTestCase(AccountCreateTest, TestCase):
    def test_attachment_add(self):
        response = self.client.post(
            '/accounts/attachment/add/', {'accountid': self.account.id})
        self.assertEqual(response.status_code, 200)

    def test_attachment_valid(self):
        response = self.client.post(
            '/accounts/attachment/add/', {'accountid': self.account.id})
        self.assertEqual(response.status_code, 200)

    def test_attachment_delete(self):
        response = self.client.post(
            '/accounts/attachment/remove/',
            {'attachment_id': self.attachment.id})
        self.assertEqual(response.status_code, 200)
