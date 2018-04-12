from django.test import TestCase
from common.models import *
from accounts.models import Account
from common.models import User


# Create your tests here.


class AccountCreateTest(object):
    def setUp(self):
        self.user = User.objects.create(first_name="uday", username='uday', email='u@mp.com', role='ADMIN')
        self.user.set_password('uday2293')
        self.user.save()

        self.address = Address.objects.create(
            street="KPHB", city="HYDERABAD", state="ANDHRA PRADESH", postcode="500073", country='IN')
        self.account = Account.objects.create(
            name="Uday", email="udayteja@micropyramid.com", phone="8333855552", billing_address=self.address,
            shipping_address=self.address, website="www.uday.com", created_by=self.user,
            industry="SOFTWARE", description="Yes.. Testing Done")
        self.client.login(email='u@mp.com', password='uday2293')


class AccountsCreateTestCase(AccountCreateTest, TestCase):
    def test_account_create_url(self):
        response = self.client.get('/accounts/create/', {
            'name': "Uday", 'email': "udayteja@micropyramid.com", 'phone': "", 'billing_address': self.address,
            'shipping_address': self.address, 'website': "www.uday.com",
            'industry': "SOFTWARE", 'description': "Yes.. Testing Done"})
        self.assertEqual(response.status_code, 200)

    def test_account_create_html(self):
        response = self.client.get('/accounts/create/', {
            'name': "Uday", 'email': "udayteja@micropyramid.com", 'phone': "", 'billing_address': self.address,
            'shipping_address': self.address, 'website': "www.uday.com",
            'industry': "SOFTWARE", 'description': "Yes.. Testing Done"})
        self.assertTemplateUsed(response, 'accounts/create_account.html')


class AccountsListTestCase(AccountCreateTest, TestCase):
    def test_accounts_list(self):
        self.accounts = Account.objects.all()
        response = self.client.get('/accounts/list/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/accounts.html')


class AccountsCountTestCase(AccountCreateTest, TestCase):
    def test_accounts_list_count(self):
        count = Account.objects.all().count()
        self.assertEqual(count, 1)


class AccountsViewTestCase(AccountCreateTest, TestCase):
    def test_accounts_view(self):
        self.accounts = Account.objects.all()
        response = self.client.get('/accounts/'+ str(self.account.id) +'/view/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/view_account.html')


class AccountsRemoveTestCase(AccountCreateTest, TestCase):
    def test_accounts_remove(self):
        response = self.client.get('/accounts/'+ str(self.account.id) +'/delete/')
        self.assertEqual(response['location'], '/accounts/list/')

    def test_accounts_remove_status(self):
        Account.objects.filter(id=self.account.id).delete()
        response = self.client.get('/accounts/list/')
        self.assertEqual(response.status_code, 200)


class AccountsUpdateUrlTestCase(AccountCreateTest, TestCase):
    def test_accounts_update(self):
        response = self.client.get('/accounts/'+ str(self.account.id) +'/edit/', {
            'name': "Uday", 'email': "udayteja@micropyramid.com", 'phone': "8333855552", 'billing_address': self.address,
            'shipping_address': self.address, 'website': "www.uday.com",
            'industry': "SOFTWARE", 'description': "Yes.. Testing Done"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/create_account.html')

    def test_accounts_update_status(self):
        response = self.client.get('/accounts/'+ str(self.account.id) +'/edit/')
        self.assertEqual(response.status_code, 200)

    def tst_accounts_update_html(self):
        response = self.client.get('/accounts/'+ str(self.account.id) +'/edit/')
        self.assertTemplateUsed(response, 'accounts/create_account.html')


class AccountCreateEmptyFormTestCase(AccountCreateTest, TestCase):

    def test_account_creation_invalid_data(self):
        data = {'name': "", 'email': "", 'phone': "", 'billing_address': self.address,
        'shipping_address': self.address, 'website': "", 'industry': "", 'description': ""}
        response = self.client.post('/accounts/create/', data)
        self.assertEqual(response.status_code, 200)
