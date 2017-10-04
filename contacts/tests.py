from django.test import TestCase
from contacts.models import Contact
from accounts.models import Account
from common.models import Address
from common.models import User
from django.test import Client
from django.core.urlresolvers import reverse


class ContactObjectsCreation(object):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_superuser('user@micropyramid.com', 'username', 'password')
        user_login = self.client.login(username='user@micropyramid.com',
                     password='password')

        self.address = Address.objects.create(street="kphb 5th phase",  city="hyd",  state="telanagana",  postcode=502279, country='IN')
        self.account = Account.objects.create(name="account", email="account@gmail.com", phone="12345", billing_address=Address.objects.get(pk=1), shipping_address=Address.objects.get(pk=1), website="account.com", industry="IT", description="account", created_by=self.user)
        self.contact = Contact.objects.create(first_name="contact", email="contact@gmail.com", phone="12345", account=Account.objects.get(pk=1), address=Address.objects.get(pk=1), description="contact", created_by=self.user)


class ContactObjectsCreation_Count(ContactObjectsCreation, TestCase):
    def test_contact_object_creation(self):
        c = Contact.objects.count()
        self.assertEqual(c, 1)

    def test_account_object_creation(self):
        c = Account.objects.count()
        self.assertEqual(c, 1)

    def test_address_object_creation(self):
        c = Address.objects.count()
        self.assertEqual(c, 1)


class ContactObjectsCreation_id(ContactObjectsCreation, TestCase):

    def test_create_contacts(self):
        self.assertEqual(self.contact.id, 1)

    def test_create_accounts(self):
        self.assertEqual(self.account.id, 1)

    def test_create_address(self):
        self.assertEqual(self.address.id, 1)


class ContactViewsTestCase(ContactObjectsCreation, TestCase):

    def test_contacts_list_page(self):
        response = self.client.get('/contacts/list/')
        self.assertEqual(response.status_code, 200)
        if response.status_code == 200:
            self.contacts = Contact.objects.all()
            self.assertEqual(response.context['contacts'][0].id, self.contact.id)
            self.assertTrue(response.context['contacts'])

    def test_contacts_list_html(self):
        response = self.client.get('/contacts/list/')
        self.assertTemplateUsed(response, 'contacts/contacts.html')

    def test_contacts_create(self):
        response = self.client.post('/contacts/create/', {
            'name': 'contact', 'email': 'contact@gmail.com', 'phone': '12345',
            'account': self.account.id, 'address': self.address, 'description': 'contact'})
        self.assertEqual(response.status_code, 200)

    def test_contacts_create_html(self):
        response = self.client.post('/contacts/create/', {
            'name': 'contact', 'email': 'contact@gmail.com', 'phone': '12345',
            'account': self.account.id, 'address': self.address, 'description': 'contact'})
        self.assertTemplateUsed(response, 'contacts/create_contact.html')

    def test_contacts_delete(self):
        Contact.objects.filter(id=self.contact.id).delete()
        response = self.client.get(reverse("contacts:list"))
        self.assertEqual(response.status_code, 200)

    def test_contacts_delete_location_checking(self):
        response = self.client.post('/contacts/1/delete/')
        self.assertEqual(response['location'], '/contacts/list/')

    def test_contacts_edit(self):
        response = self.client.post('/contacts/1/edit/', {
            'name': 'priya', 'email': 'contact@gmail.com', 'phone': '12345',
            'pk': 1, 'account': self.account.id, 'address': self.address.id})
        self.assertEqual(response.status_code, 200)

    def test_contacts_edit_html(self):
        response = self.client.post('/contacts/1/edit/', {
            'name': 'priya', 'email': 'contact@gmail.com', 'phone': '12345',
            'pk': 1, 'account': self.account.id, 'address': self.address.id})
        self.assertTemplateUsed(response, 'contacts/create_contact.html')

    def test_contacts_view(self):
        self.contacts = Contact.objects.all()
        response = self.client.get('/contacts/1/view/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['con'].id, 1)

    def test_contacts_view_html(self):
        response = self.client.get('/contacts/1/view/')
        self.assertTemplateUsed(response, 'contacts/view_contact.html')
