from django.test import TestCase
from ..djcrm.models import *
from .models import LeadAccount
from django.contrib.auth.models import User


# Create your tests here.


class AccountCreateTest(object):
    def setUp(self):
        self.country = Country.objects.create(
            iso_3166_1_a2="IN", iso_3166_1_a3="IND", iso_3166_1_numeric="01", printable_name="INDIA", name="INDIA", is_shipping_country="True")
        self.address = Address.objects.create(
            street="KPHB", city="HYDERABAD", state="ANDHRA PRADESH", postcode="500073", country=Country.objects.get(pk=1))
        self.account = LeadAccount.objects.create(
            name="Uday", email="udayteja@micropyramid.com", phone="8333855552", billing_address=self.address,
            shipping_address=self.address, website="www.uday.com", account_type="PARTNER",
            sis_code="UDAYMP2016", industry="SOFTWARE", description="Yes.. Testing Done")
        self.user = User.objects.create(username='uday')
        self.user.set_password('uday2293')
        self.user.save()
        self.client.login(username='uday', password='uday2293')


class AccountsCreateUrlTestCase(AccountCreateTest, TestCase):
    def test_account_create_url(self):
        response = self.client.get('/accounts/create/', {
            'name': "Uday", 'email': "udayteja@micropyramid.com", 'phone': "", 'billing_address': self.address,
            'shipping_address': self.address, 'website': "www.uday.com", 'account_type': "PARTNER",
            'sis_code': "UDAYMP2016", 'industry': "SOFTWARE", 'description': "Yes.. Testing Done"})
        self.assertEqual(response.status_code, 200)

    def test_account_create_html(self):
        response = self.client.get('/accounts/create/', {
            'name': "Uday", 'email': "udayteja@micropyramid.com", 'phone': "", 'billing_address': self.address,
            'shipping_address': self.address, 'website': "www.uday.com", 'account_type': "PARTNER",
            'sis_code': "UDAYMP2016", 'industry': "SOFTWARE", 'description': "Yes.. Testing Done"})
        self.assertTemplateUsed(response, 'accounts/create_account.html')


class AccountCreateTestCase(AccountCreateTest, TestCase):
    def test_account_create(self):
        self.assertEqual(self.account.id, 1)


class AccountsListTestCase(AccountCreateTest, TestCase):
    def test_accounts_list(self):
        self.accounts = LeadAccount.objects.all()
        response = self.client.get('/accounts/list/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/accounts.html')


class AccountsCountTestCase(AccountCreateTest, TestCase):
    def test_accounts_list_count(self):
        count = LeadAccount.objects.all().count()
        self.assertEqual(count, 1)


class AccountsViewTestCase(AccountCreateTest, TestCase):
    def test_accounts_view(self):
        self.accounts = LeadAccount.objects.all()
        response = self.client.get('/accounts/1/view/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['ac'].id, 1)
        self.assertTemplateUsed(response, 'accounts/view_account.html')


class AccountsRemoveTestCase(AccountCreateTest, TestCase):
    def test_accounts_remove(self):
        # self.account_del = LeadAccount.objects.filter(id=1).delete()
        response = self.client.get('/accounts/1/delete/')
        self.assertEqual(response['location'], '/accounts/list/')

    def test_accounts_remove_status(self):
        LeadAccount.objects.filter(id=self.account.id).delete()
        response = self.client.get('/accounts/list/')
        self.assertEqual(response.status_code, 200)


class AccountsUpdateUrlTestCase(AccountCreateTest, TestCase):
    def test_accounts_update(self):
        response = self.client.get('/accounts/1/edit/', {
            'name': "Uday", 'email': "udayteja@micropyramid.com", 'phone': "8333855552", 'billing_address': self.address,
            'shipping_address': self.address, 'website': "www.uday.com", 'account_type': "PARTNER",
            'sis_code': "UDAYMP2016", 'industry': "SOFTWARE", 'description': "Yes.. Testing Done"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/create_account.html')

    def test_accounts_update_status(self):
        response = self.client.get('/accounts/1/edit/')
        self.assertEqual(response.status_code, 200)

    def tst_accounts_update_html(self):
        response = self.client.get('/accounts/1/edit/')
        self.assertTemplateUsed(response, 'accounts/create_account.html')


class AccountCreateEmptyFormTestCase(AccountCreateTest, TestCase):

    def test_account_creation_invalid_data(self):
        data = {'name': "", 'email': "", 'phone': "", 'billing_address': self.address, 'shipping_address': self.address,
                'website': "", 'account_type': "", 'sis_code': "", 'industry': "", 'description': ""}
        response = self.client.post('/accounts/create/', data)
        self.assertEqual(response.status_code, 200)
