from django.test import TestCase
from contacts.models import Contact
from common.models import Address, User, Comment, Attachments
from cases.models import Case
from django.test import Client
from django.urls import reverse


class ContactObjectsCreation(object):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(
            first_name="navaneetha",
            username='navaneetha',
            email="n@mp.com",
            role="ADMIN")
        self.user.set_password('navi123')
        self.user.save()
        self.address = Address.objects.create(
            street="kphb 5th phase",
            city="hyd",
            state="telanagana",
            postcode=502279, country="AD")

        self.contact = Contact.objects.create(
            first_name="contact",
            email="contact@gmail.com",
            phone="12345",
            address=self.address,
            description="contact",
            created_by=self.user)
        self.contact.assigned_to.add(self.user)
        self.case = Case.objects.create(
            name="raghu",
            case_type="Problem",
            status="New",
            priority="Low",
            description="something",
            created_by=self.user,
            closed_on="2016-05-04")
        self.comment = Comment.objects.create(
            comment='testikd', case=self.case,
            commented_by=self.user
        )
        self.attachment = Attachments.objects.create(
            attachment='image.png', case=self.case,
            created_by=self.user
        )
        self.client.login(username='n@mp.com', password='navi123')


class ContactObjectsCreation_Count(ContactObjectsCreation, TestCase):
    def test_contact_object_creation(self):
        c = Contact.objects.count()
        self.assertEqual(c, 1)

    def test_address_object_creation(self):
        c = Address.objects.count()
        self.assertEqual(c, 1)


class ContactViewsTestCase(ContactObjectsCreation, TestCase):

    def test_contacts_list_page(self):
        response = self.client.get('/contacts/list/')
        self.assertEqual(response.status_code, 200)
        if response.status_code == 200:
            self.assertEqual(
                response.context['contact_obj_list'][0].id, self.contact.id)
            self.assertTrue(response.context['contact_obj_list'])

    def test_contacts_list_html(self):
        response = self.client.get('/contacts/list/')
        self.assertTemplateUsed(response, 'contacts.html')

    def test_contacts_create(self):
        response = self.client.post('/contacts/create/', {
            'first_name': 'contact',
            'last_name': 'reddy',
            'email': 'meg@gmail.com',
            'phone': '+917898901234',
            'address': self.address.id,
            'description': 'contact',
            'created_by': self.user})
        self.assertEqual(response.status_code, 302)

    def test_contacts_create_html(self):
        response = self.client.post('/contacts/create/', {
            'name': 'contact', 'email': 'contact@gmail.com', 'phone': '12345',
            'address': self.address,
            'description': 'contact'})
        self.assertTemplateUsed(response, 'create_contact.html')

    def test_contacts_delete(self):
        Contact.objects.filter(id=self.contact.id).delete()
        response = self.client.get(reverse("contacts:list"))
        self.assertEqual(response.status_code, 200)

    def test_contacts_delete_location_checking(self):
        response = self.client.post(
            '/contacts/' + str(self.contact.id) + '/delete/')
        self.assertEqual(response['location'], '/contacts/list/')

    def test_contacts_edit(self):
        response = self.client.post(
            '/contacts/' + str(self.contact.id) + '/edit/', {
                'name': 'priya',
                'email': 'contact@gmail.com',
                'phone': '12345',
                'pk': self.contact.id,
                'address': self.address.id})
        self.assertEqual(response.status_code, 200)

    def test_contacts_edit_html(self):
        response = self.client.post(
            '/contacts/' + str(self.contact.id) + '/edit/', {
                'name': 'priya',
                'email': 'contact@gmail.com',
                'phone': '12345',
                'pk': self.contact.id,
                'address': self.address.id})
        self.assertTemplateUsed(response, 'create_contact.html')

    def test_contacts_view(self):
        response = self.client.get(
            '/contacts/' + str(self.contact.id) + '/view/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['contact_record'].id, self.contact.id)

    def test_contacts_view_html(self):
        response = self.client.get(
            '/contacts/' + str(self.contact.id) + '/view/')
        self.assertTemplateUsed(response, 'view_contact.html')

    def test_contacts_edit_post(self):
        response = self.client.get(
            '/contacts/' + str(self.contact.id) + '/edit/')
        self.assertEqual(response.status_code, 200)


class ContactsListTestCase(ContactObjectsCreation, TestCase):

    def test_contacts_list(self):
        self.contacts = Contact.objects.all()
        response = self.client.get('/contacts/list/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'contacts.html')

    def test_contacts_list_queryset(self):
        data = {'fist_name': 'contact',
                'city': "hyd", 'phone': '12345', 'email': "contact@gmail.com"}
        response = self.client.post('/contacts/list/', data)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'contacts.html')


class CommentTestCase(ContactObjectsCreation, TestCase):
    def test_comment_add(self):
        response = self.client.post(
            '/contacts/comment/add/', {'contactid': self.contact.id})
        self.assertEqual(response.status_code, 200)

    def test_comment_edit(self):
        response = self.client.post(
            '/contacts/comment/edit/', {'commentid': self.comment.id})
        self.assertEqual(response.status_code, 200)

    def test_comment_delete(self):
        response = self.client.post(
            '/contacts/comment/remove/', {'comment_id': self.comment.id})
        self.assertEqual(response.status_code, 200)


class AttachmentTestCase(ContactObjectsCreation, TestCase):
    def test_attachment_add(self):
        response = self.client.post(
            '/contacts/attachment/add/', {'contactid': self.contact.id})
        self.assertEqual(response.status_code, 200)

    def test_attachment_valid(self):
        response = self.client.post(
            '/contacts/attachment/add/', {'contactid': self.contact.id})
        self.assertEqual(response.status_code, 200)

    def test_attachment_delete(self):
        response = self.client.post(
            '/contacts/attachment/remove/',
            {'attachment_id': self.attachment.id})
        self.assertEqual(response.status_code, 200)
