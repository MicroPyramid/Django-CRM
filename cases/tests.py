from django.test import TestCase
from cases.models import Case
from contacts.models import Contact
from accounts.models import Account
from common.models import Address
from common.models import User


class CaseCreation(object):
    def setUp(self):
        self.address = Address.objects.create(street="6th phase", city="hyderabad", postcode="506344",
                                              country='IN')

        self.user = User.objects.create(first_name="raghu", username='raghu', email='r@mp.com', role="ADMIN")
        self.user.set_password('raghu')
        self.user.save()
        self.client.login(email='r@mp.com', password='raghu')

        self.client.login(email='r@mp.com', password='raghu')

        self.account = Account.objects.create(
            name="account",
            email="account@gmail.com", phone="12345",
            billing_address=self.address, shipping_address=self.address,
            website="www.account.com", industry="IT", description="account",
            created_by=self.user)

        self.contacts = Contact.objects.create(
            first_name="contact", email="contact@gmail.com", phone="12345",
            account=self.account, description="contact", address=self.address, created_by=self.user)

        self.case = Case.objects.create(
            name="raghu", case_type="Problem", status="New", account=self.account,
            priority="Low", description="something",
            created_by=self.user, closed_on="2016-05-04")


class CaseViewTestCase(CaseCreation, TestCase):
    def test_list_cases(self):
        self.cases = Case.objects.all()
        response = self.client.get('/cases/list/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['cases'][0].id, self.case.id)
        self.assertTrue(response.context['cases'])
        self.assertTemplateUsed(response, 'cases.html')


class CaseCreationUrlTestCase(CaseCreation, TestCase):
    def test_create_cases(self):
        response = self.client.post('/cases/create/', {'name': 'new case', 'case_type': 'Problem', 'status': 'New',
                                                       'account': self.account, 'contacts': [self.contacts.id],
                                                       'priority': "Low",
                                                       'description': "something"})
        self.assertEqual(response.status_code, 200)

    def test_create_cases_html(self):
        response = self.client.post('/cases/create/', {'name': 'new case', 'case_type': 'Problem', 'status': 'New',
                                                       'account': self.account, 'contacts': [self.contacts.id],
                                                       'priority': "Low",
                                                       'description': "something"})
        self.assertTemplateUsed(response, 'create_cases.html')


class CaseShowTestCase(CaseCreation, TestCase):
    def test_show_case(self):
        response = self.client.get('/cases/' + str(self.case.id) + '/view/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['case_record'].id, self.case.id)

    def test_show_case_html(self):
        response = self.client.get('/cases/' + str(self.case.id) + '/view/')
        self.assertTemplateUsed(response, 'view_case.html')

    def test_show_case_invalid_data(self):
        response = self.client.get('/cases/' + str(self.case.id) + '/view/')
        self.assertEqual(response.status_code, 200)


class CaseRemoveTestCase(CaseCreation, TestCase):
    def test_case_deletion_show_case(self):
        response = self.client.get('/cases/' + str(self.case.id) + '/remove/')
        self.assertEqual(response['location'], '/cases/list/')


class CaseUpdateTestCase(CaseCreation, TestCase):
    def test_update_case_view(self):
        response = self.client.get('/cases/' + str(self.case.id) + '/edit_case/')
        self.assertEqual(response.status_code, 200)

    def test_case_update(self):
        response = self.client.post('/cases/' + str(self.case.id) + '/edit_case/', {'hiddenval': self.case.id})
        self.assertEqual(response.status_code, 200)

    def test_case_update_html(self):
        response = self.client.post('/cases/' + str(self.case.id) + '/edit_case/', {'hiddenval': self.case.id})
        self.assertTemplateUsed(response, 'create_cases.html')
