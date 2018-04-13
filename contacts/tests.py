from django.test import TestCase
from contacts.models import Contact
from accounts.models import Account
from common.models import Address, User
from django.test import Client
from django.urls import reverse


class ContactObjectsCreation(object):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(first_name="navaneetha", username='navaneetha', email="n@mp.com", role="ADMIN")
        self.user.set_password('navi123')
        self.user.save()
        self.address = Address.objects.create(street="kphb 5th phase", city="hyd", state="telanagana", postcode=502279, country="AD")
        self.account = Account.objects.create(
            name="account", email="account@gmail.com", phone="12345", billing_address=self.address,
            shipping_address=self.address, website="account.com", industry="IT", description="account", created_by=self.user)
        self.contact = Contact.objects.create(
            first_name="contact", email="contact@gmail.com", phone="12345", account=self.account,
            address=self.address, description="contact", created_by=self.user)
        self.client.login(username='n@mp.com', password='navi123')


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


class ContactViewsTestCase(ContactObjectsCreation, TestCase):

    def test_contacts_list_page(self):
        response = self.client.get('/contacts/list/')
        self.assertEqual(response.status_code, 200)
        if response.status_code == 200:
            self.assertEqual(response.context['contact_obj_list'][0].id, self.contact.id)
            self.assertTrue(response.context['contact_obj_list'])

    def test_contacts_list_html(self):
        response = self.client.get('/contacts/list/')
        self.assertTemplateUsed(response, 'contacts.html')

    def test_contacts_create(self):
        response = self.client.post('/contacts/create/', {
            'first_name': 'contact', 'email': 'contact@gmail.com', 'phone': '12345',
            'account': self.account.id, 'address': self.address, 'description': 'contact', 'created_by': self.user})
        self.assertEqual(response.status_code, 200)

    def test_contacts_create_html(self):
        response = self.client.post('/contacts/create/', {
            'name': 'contact', 'email': 'contact@gmail.com', 'phone': '12345',
            'account': self.account.id, 'address': self.address, 'description': 'contact'})
        self.assertTemplateUsed(response, 'create_contact.html')

    def test_contacts_delete(self):
        Contact.objects.filter(id=self.contact.id).delete()
        response = self.client.get(reverse("contacts:list"))
        self.assertEqual(response.status_code, 200)

    def test_contacts_delete_location_checking(self):
        response = self.client.post('/contacts/'+ str(self.contact.id) +'/delete/')
        self.assertEqual(response['location'], '/contacts/list/')

    def test_contacts_edit(self):
        response = self.client.post('/contacts/'+ str(self.contact.id) +'/edit/', {
            'name': 'priya', 'email': 'contact@gmail.com', 'phone': '12345',
            'pk': self.contact.id, 'account': self.account.id, 'address': self.address.id})
        self.assertEqual(response.status_code, 200)

    def test_contacts_edit_html(self):
        response = self.client.post('/contacts/'+ str(self.contact.id) +'/edit/', {
            'name': 'priya', 'email': 'contact@gmail.com', 'phone': '12345',
            'pk': self.contact.id, 'account': self.account.id, 'address': self.address.id})
        self.assertTemplateUsed(response, 'create_contact.html')

    def test_contacts_view(self):
        response = self.client.get('/contacts/'+ str(self.contact.id) +'/view/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['contact_record'].id, self.contact.id)

    def test_contacts_view_html(self):
        response = self.client.get('/contacts/'+ str(self.contact.id) +'/view/')
        self.assertTemplateUsed(response, 'view_contact.html')


