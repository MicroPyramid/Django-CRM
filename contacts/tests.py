from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django.utils.encoding import force_text

from accounts.models import Account
from cases.models import Case
from common.models import Address, Attachments, Comment, User
from contacts.forms import ContactAttachmentForm
from contacts.models import Contact
from teams.models import Teams


class ContactObjectsCreation(object):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(
            first_name="johnContact",
            username='johnDoeContact',
            email="johnContact@example.com",
            role="ADMIN")
        self.user.set_password('password')
        self.user.save()
        self.address = Address.objects.create(
            street="street",
            city="city name",
            state="state name",
            postcode=12345, country="IN")

        self.contact = Contact.objects.create(
            first_name="contact",
            email="contact@example.com",
            phone="12345",
            address=self.address,
            description="contact",
            created_by=self.user)
        self.contact.assigned_to.add(self.user)
        self.case = Case.objects.create(
            name="jane doe case",
            case_type="Problem",
            status="New",
            priority="Low",
            description="description for case",
            created_by=self.user,
            closed_on="2016-05-04")
        self.comment = Comment.objects.create(
            comment='test comment', case=self.case,
            commented_by=self.user
        )
        self.attachment = Attachments.objects.create(
            attachment='image.png', case=self.case,
            created_by=self.user
        )

        self.user_contacts_mp = User.objects.create(
            first_name="janeUser@example.com",
            username='janeUserContact',
            email="janeUser@example.com",
            role="USER",
            has_sales_access=True)
        self.user_contacts_mp.set_password('password')
        self.user_contacts_mp.save()

        self.client.login(username='johnContact@example.com', password='password')


class ContactObjectsCreation_Count(ContactObjectsCreation, TestCase):

    def test_contact_object_creation(self):
        c = Contact.objects.count()
        con = Contact.objects.filter(id=self.contact.id)
        # print(self.contact.first_name)
        self.assertEqual(str(con.last()), self.contact.first_name)
        self.assertEqual(c, 1)

    def test_address_object_creation(self):
        c = Address.objects.count()
        self.assertEqual(c, 1)


class ContactViewsTestCase(ContactObjectsCreation, TestCase):

    def test_contacts_list_page(self):
        response = self.client.get(reverse('contacts:list'))
        self.assertEqual(response.status_code, 200)
        if response.status_code == 200:
            self.assertEqual(
                response.context['contact_obj_list'][0].id, self.contact.id)
            self.assertTrue(response.context['contact_obj_list'])

    def test_contacts_list_html(self):
        response = self.client.get(reverse('contacts:list'))
        self.assertTemplateUsed(response, 'contacts.html')

    def test_contacts_create(self):
        upload_file = open('static/images/user.png', 'rb')
        response = self.client.post('/contacts/create/', {
            'first_name': 'john contact',
            'last_name': 'doe',
            'email': 'johnDoeContact@example.com',
            'phone': '+911234567892',
            'address': self.address.id,
            'description': 'contact',
            'created_by': self.user,
            'assigned_to': str(self.user.id),
            'contact_attachment': SimpleUploadedFile(
                upload_file.name, upload_file.read())
        })
        self.assertEqual(response.status_code, 302)

    def test_contact_create(self):
        upload_file = open('static/images/user.png', 'rb')
        response = self.client.post('/contacts/create/', {
            'first_name': 'janeDoe',
            'last_name': 'contact doe',
            'email': 'janeDoeContact@example.com',
            'phone': '+911234567892',
            'address': self.address.id,
            'description': 'contact',
            'created_by': self.user,
            'assigned_to': str(self.user.id),
            'contact_attachment': SimpleUploadedFile(
                upload_file.name, upload_file.read())
        })
        self.assertEqual(response.status_code, 302)

    def test_update_contact(self):
        upload_file = open('static/images/user.png', 'rb')
        url = '/contacts/' + str(self.contact.id) + '/edit/'
        data = {
            'first_name': 'john Contact',
            'last_name': 'doe',
            'email': 'johnDoeContact@example.com',
            'phone': '+911234561255',
            'address': self.address.id,
            'description': 'contact',
            'created_by': self.user,
            'assigned_to': str(self.user.id),
            'contact_attachment': SimpleUploadedFile(
                upload_file.name, upload_file.read())
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

    def test_contacts_create_html(self):
        response = self.client.post('/contacts/create/', {
            'name': 'contact', 'email': 'contact@example.com', 'phone': '12345',
            'address': self.address,
            'description': 'contact'})
        self.assertTemplateUsed(response, 'create_contact.html')

    def test_contacts_delete(self):
        Contact.objects.filter(id=self.contact.id).delete()
        response = self.client.get(reverse("contacts:list"))
        self.assertEqual(response.status_code, 200)

    def test_contacts_delete_get(self):
        response = self.client.get(
            '/contacts/' + str(self.contact.id) + '/delete/')
        self.assertEqual(response.status_code, 302)

    def test_contacts_delete_location_checking(self):
        response = self.client.post(
            '/contacts/' + str(self.contact.id) + '/delete/')
        self.assertEqual(response['location'], '/contacts/')

    def test_contacts_edit(self):
        response = self.client.post(
            '/contacts/' + str(self.contact.id) + '/edit/', {
                'name': 'contact name',
                'email': 'contact@example.com',
                'phone': '12345',
                'pk': self.contact.id,
                'address': self.address.id})
        self.assertEqual(response.status_code, 200)

    def test_contacts_edit_html(self):
        response = self.client.post(
            '/contacts/' + str(self.contact.id) + '/edit/', {
                'name': 'contact Name',
                'email': 'contact@example.com',
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
        response = self.client.get(reverse('contacts:list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'contacts.html')

    def test_contacts_list_queryset(self):
        data = {'fist_name': 'jane contact',
                'city': "city name", 'phone': '12345',
                'email': "contact@example.com", 'assigned_to': str(self.user.id)}
        response = self.client.post(reverse('contacts:list'), data)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'contacts.html')

    def test_contacts_list_user_role(self):
        self.client.login(username='janeUser@example.com', password='password')
        self.contact = Contact.objects.create(
            first_name="jane contact",
            email="janecontact@example.com",
            created_by=self.user_contacts_mp)
        response = self.client.get(reverse('contacts:list'))
        self.assertEqual(response.status_code, 200)
        self.contact.delete()

        response = self.client.post(
            reverse('contacts:list'), {'first_name': 'john contact', 'assigned_to': str(self.user.id)})
        self.assertEqual(response.status_code, 200)


class CommentTestCase(ContactObjectsCreation, TestCase):

    def test_comment_add(self):
        response = self.client.post(
            '/contacts/comment/add/', {'contactid': self.contact.id})
        self.assertEqual(response.status_code, 200)

    # def test_GetContactsView(self):
    #     response = self.client.get('/get/list/')
    #     # self.assertEqual(response.status_code, 200)
        # self.assertIsNone(response.context['contacts'])

    def test_comment_edit(self):
        response = self.client.post(
            '/contacts/comment/edit/', {'commentid': self.comment.id})
        self.assertEqual(response.status_code, 200)
        resp = self.client.post(
            '/contacts/comment/edit/',
            {'commentid': self.comment.id, 'comment': 'test comment'})
        self.assertEqual(resp.status_code, 200)

    def test_comment_delete(self):
        response = self.client.post(
            '/contacts/comment/remove/', {'comment_id': self.comment.id})
        self.assertEqual(response.status_code, 200)

    def test_form_valid(self):
        response = self.client.post(
            '/contacts/comment/add/', {'contactid': self.contact.id,
                                       'comment': 'test comment'})
        # print(response , "response")
        self.assertEqual(response.status_code, 200)


class AttachmentTestCase(ContactObjectsCreation, TestCase):

    def test_attachment_add(self):
        response = self.client.post(
            '/contacts/attachment/add/', {'contactid': self.contact.id})
        self.assertEqual(response.status_code, 200)

    def test_attachment_valid(self):
        upload_file = open('static/images/user.png', 'rb')
        response = self.client.post(
            '/contacts/attachment/add/', {'contactid': self.contact.id,
                                          'attachment': SimpleUploadedFile(
                                              upload_file.name, upload_file.read())})
        self.assertEqual(response.status_code, 200)

    def test_attachment_delete(self):
        response = self.client.post(
            '/contacts/attachment/remove/',
            {'attachment_id': self.attachment.id})
        self.assertEqual(response.status_code, 200)


class TestContactCreateContact(ContactObjectsCreation, TestCase):

    def test_create_new_contact(self):
        upload_file = open('static/images/user.png', 'rb')
        response = self.client.post('/contacts/create/', {
            'first_name': 'john doe contact',
            'last_name': 'doe',
            'email': 'johnDContact@example.com',
            'phone': '+911234561256',
            'address': self.address.id,
            'description': 'contact',
            'created_by': self.user,
            'assigned_to': str(self.user.id),
            'savenewform': True,
            'address_line': 'address line'
        })
        self.assertEqual(response.status_code, 302)

    def test_contact_detail_view_error(self):
        self.client.login(username='janeUser@example.com', password='password')
        self.contact = Contact.objects.create(created_by=self.user)

    def test_contact_update_view(self):
        self.client.login(username='johnContact@example.com', password='password')
        response = self.client.post(reverse('contacts:edit_contact', args=(self.contact.id,)), {
            'first_name': 'first name',
            'last_name': 'last name',
            'phone': '232323',
            'email': 'email@email.com',
            'assigned_to': str(self.user.id)
        })
        self.assertEqual(200, response.status_code)

    def test_contact_update_view_assigned_Users(self):
        self.client.login(username='johnContact@example.com', password='password')
        response = self.client.post(reverse('contacts:edit_contact', args=(self.contact.id,)), {
            'first_name': 'first name',
            'last_name': 'last name',
            'phone': '232323',
            'email': 'email@email.com',
            'assigned_to': str(self.user_contacts_mp.id)
        })
        self.assertEqual(200, response.status_code)

        response = self.client.post(reverse('contacts:edit_contact', args=(self.contact.id,)), {
            'first_name': 'first name',
            'last_name': 'last name',
            'phone': '232323',
            'email': 'email@email.com'
        })
        self.assertEqual(200, response.status_code)

    def test_contact_update_view_error(self):
        self.usermp1 = User.objects.create(
            first_name="janeDoe@example.com",
            username='janeDoe',
            email="janeDoe@example.com",
            role="USER",
            is_active=True,
            has_sales_access=True)
        self.usermp1.set_password('password')
        self.usermp1.save()
        self.contact = Contact.objects.create(
            first_name="jane doe contact",
            email="contactJaneDoe@example.com",
            created_by=self.user_contacts_mp)
        self.client.login(username='janeDoe@example.com', password='password')
        response = self.client.get(
            reverse('contacts:edit_contact', args=(self.contact.id,)), {})
        self.assertEqual(403, response.status_code)

        response = self.client.post(reverse('contacts:remove_contact', args=(
            self.contact.id,)), {'pk': self.contact.id})
        self.assertEqual(403, response.status_code)
        self.contact.delete()

        self.contact = Contact.objects.create(created_by=self.user)
        response = self.client.post(
            '/contacts/comment/add/', {'contactid': self.contact.id})
        self.assertJSONEqual(force_text(response.content), {
                             'error': "You don't have permission to comment."})

        response = self.client.post(
            '/contacts/comment/edit/', {'commentid': self.comment.id})
        self.assertJSONEqual(force_text(response.content), {
                             'error': "You don't have permission to edit this comment."})

        response = self.client.post(
            '/contacts/comment/remove/', {'comment_id': self.comment.id})
        self.assertJSONEqual(force_text(response.content), {
                             'error': "You don't have permission to delete this comment."})

        response = self.client.post(
            '/contacts/attachment/add/', {'contactid': self.contact.id})
        self.assertJSONEqual(force_text(response.content), {
                             'error': "You don't have permission to add attachment."})

        self.attachment = Attachments.objects.create(
            attachment='image.png', case=self.case,
            created_by=self.user
        )
        response = self.client.post(
            '/contacts/attachment/remove/', {'attachment_id': self.attachment.id})
        self.assertJSONEqual(force_text(response.content), {
                             'error': "You don't have permission to delete this attachment."})


class TestContactViews(ContactObjectsCreation, TestCase):

    def test_create_contact(self):
        self.client.logout()
        self.client.login(username='janeUser@example.com', password='password')
        response = self.client.get(reverse('contacts:list'),{})
        self.assertEqual(200, response.status_code)

        self.client.logout()
        self.client.login(username='johnContact@example.com', password='password')
        self.account_by_user = Account.objects.create(
            name="account edit", email="johndoe@example.com", phone="123456789",
            billing_address_line="", billing_street="street name",
            billing_city="city name",
            billing_state="state", billing_postcode="1234",
            billing_country="US",
            website="www.example.como", created_by=self.user, status="open",
            industry="SOFTWARE", description="Testing")
        self.teams_contacts = Teams.objects.create(name='teams contacts')
        self.teams_contacts.users.add(self.user)
        data = {
            'first_name':'first name',
            'last_name':'last name',
            'phone':'+91-123-456-7854',
            'email':'example@user.com',
            'teams':[self.teams_contacts.id,]
        }
        response = self.client.post(reverse('contacts:add_contact') + '?view_account={}&address_form='.format(self.account_by_user.id), data)
        self.assertEqual(302, response.status_code)

        data = {
            'first_name':'first name',
            'last_name':'last name',
            'phone':'+91-123-456-7858',
            'email':'example@mail.com',
            'teams':[self.teams_contacts.id,]
        }
        response = self.client.post(reverse('contacts:add_contact') + '?view_account={}'.format(self.account_by_user.id), data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(200, response.status_code)

        data = {
            'first_name':'first name',
            'last_name':'last name',
            'phone':'+91-123-456-7854',
            'email':'example@user',
            'teams':[self.teams_contacts.id,]
        }
        response = self.client.post(reverse('contacts:add_contact') + '?view_account={}'.format(self.account_by_user.id), data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(200, response.status_code)
        response = self.client.get(reverse('contacts:add_contact') + '?address_form=')
        self.assertEqual(200, response.status_code)

        response = self.client.post(reverse('contacts:edit_contact', args=(self.contact.id,)),{
            'first_name':'contact',
            'last_name':'contact@example.com',
            'phone':'+91-123-456-7856',
            'email':'contact@example.com',
            'teams':[self.teams_contacts.id,]
        })
        self.assertEqual(302, response.status_code)

        self.user_contacts_mp = User.objects.create(
            first_name="joeUser@contact.com",
            username='joeUser@contact.com',
            email="joeUser@contact.com",
            role="USER",
            has_sales_access=True)
        self.user_contacts_mp.set_password('password')
        self.user_contacts_mp.save()

        self.client.logout()
        self.client.login(username='joeUser@contact.com', password='password')
        response = self.client.get(reverse('contacts:view_contact', args=(self.contact.id,)))
        self.assertEqual(403, response.status_code)

        self.client.logout()
        self.client.login(username='janeUser@example.com', password='password')
        response = self.client.get(reverse('contacts:view_contact', args=(self.contact.id,)))
        # self.assertEqual(403, response.status_code)

        self.client.logout()
        self.client.login(username='johnContact@example.com', password='password')
        self.teams_contacts.users.add(self.user)
        data = {
            'first_name':'contact',
            'last_name':'contact',
            'phone':'+91-123-456-7852',
            'email':'contact@example.com',
            'teams':[self.teams_contacts.id,]
        }
        response = self.client.post(reverse('contacts:edit_contact', args=(self.contact.id,)) + '?from_account={}'.format(self.account_by_user.id), data)
        self.assertEqual(302, response.status_code)
        response = self.client.post(reverse('contacts:edit_contact', args=(self.contact.id,)) + '?from_account={}&address_form='.format(self.account_by_user.id), data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(200, response.status_code)

        data = {
            'first_name':'contact',
            'last_name':'contact',
            'phone':'+91-123-456',
            'email':'contact@example',
            'teams':[self.teams_contacts.id,]
        }
        response = self.client.post(reverse('contacts:edit_contact', args=(self.contact.id,)) + '?from_account={}'.format(self.account_by_user.id), data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(200, response.status_code)

        response = self.client.post(reverse('contacts:edit_contact', args=(self.contact.id,)) + '?from_account={}'.format(self.account_by_user.id), data,)
        self.assertEqual(200, response.status_code)

        self.client.logout()
        self.client.login(username='johnContact@example.com', password='password')
        self.contact_delete = Contact.objects.create(
            first_name="contact",
            email="contact_delete@example.com",
            phone="12345",
            address=self.address,
            description="contact",
            created_by=self.user)
        response = self.client.post(reverse('contacts:remove_contact', args=(self.contact_delete.id,)), {'pk': self.contact_delete.id},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(200, response.status_code)

        self.contact_edit = Contact.objects.create(
            first_name="contact",
            email="contact_edit@example.com",
            phone="12345",
            description="contact",
            created_by=self.user_contacts_mp)

        self.client.logout()
        self.client.login(username='joeUser@contact.com', password='password')
        response = self.client.get(reverse('contacts:view_contact', args=(self.contact_edit.id,)), {'pk': self.contact_edit.id},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(200, response.status_code)
        response = self.client.get(reverse('contacts:add_contact'))
        self.assertEqual(200, response.status_code)