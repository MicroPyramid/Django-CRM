from django.test import TestCase
from django.test import Client

from common.models import User, Document
from common.forms import *


class ObjectsCreation(object):
    def setUp(self):
        self.client = Client()
        # self.user = User.objects.create(first_name="admin",
        #                                 username='admin',
        #                                 email='admin@micropyramid.com',
        #                                 is_staff=True,
        #                                 is_admin=True,
        #                                 is_superuser=True, is_active=True)

        self.user = User.objects.create(first_name="admin",
                                        username='admin',
                                        email='admin@micropyramid.com',
                                        is_staff=True,
                                        is_admin=True,
                                        is_superuser=True,
                                        is_active=True, role='ADMIN')

        self.user.set_password('admin123')
        self.user.save()
        self.user = User.objects.create(first_name="paul",
                                        username='paul',
                                        email='paul@micropyramid.com',
                                        is_staff=True, is_admin=True,
                                        is_superuser=True, is_active=False)
        self.user.set_password('paul123')
        self.user.save()
        # self.user
        user_login = self.client.login(
            username='admin@micropyramid.com', password='admin123')
        self.document = Document.objects.create(
            title="abc", document_file="1.png", created_by=self.user)


class TestHomePage(ObjectsCreation, TestCase):
    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        if response.status_code == 200:
            self.assertIn("Micro", str(response.content))

    # def test_404_page(self):
    #     # print("34792837471239407123742374")
    #     response = self.client.get('/sldkf')
    #     # print(response)
    #     self.assertEqual(response.status_code, 404)


class CommonModelTest(ObjectsCreation, TestCase):

    def test_string_representation_user(self):
        user = self.user
        self.assertEqual(str(user.get_short_name()), user.username)


class UserCreateTestCase(ObjectsCreation, TestCase):

    # def test_user_create_url(self):
    #     url = '/users/create/'
    #     data = {'email': 'abc@micropyramid.com', 'username': 'user', 'role': 'USER'}
    #     response = self.client.post(url,data)
    #     self.assertEqual(response.status_code,200)

    def test_user_create_invalid(self):
        response = self.client.post('/users/create/', {
            'email': 'admin@micropyramid.com',
            'first_name': '',
            'last_name': '',
            'username': '',
            'role': 'r',
            'profile_pic': None})
        self.assertEqual(response.status_code, 200)


class PasswordChangeTestCase(ObjectsCreation, TestCase):
    def test_password_change(self):
        self.client.login(username="admin@micropyramid.com",
                          password="admin123")
        url = "/change-password/"
        data = {'CurrentPassword': "admin123",
                'Newpassword': "test123", 'confirm': 'test123'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

    def test_password_invalid(self):
        self.client.login(username="admin@micropyramid.com",
                          password="admin123")
        url = "/change-password/"
        data = {'CurrentPassword': " ",
                'Newpassword': "test123", 'confirm': " "}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)


class ForgotPasswordViewTestCase(ObjectsCreation, TestCase):

    def test_forgot_password(self):
        url = "/forgot-password/"
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'forgot_password.html')


class LoginViewTestCase(ObjectsCreation, TestCase):
    # user2 = User.objects.create(first_name="paul", username='paul', email='paul@micropyramid.com',
    #                                     is_staff=True, is_admin=True, is_superuser=True, is_active=False)
    def test_login_post(self):
        self.client.logout()
        data = {"email": "admin@micropyramid.com", "password": "admin123"}
        response = self.client.post('/login/', data)
        self.assertEqual(response.status_code, 302)

    def test_login_post_invalid(self):
        self.client.logout()
        data = {"email": "admin@micropyramid.com", "password": "test123"}
        response = self.client.post('/login/', data)
        self.assertEqual(response.status_code, 200)

    def test_login_inactive(self):
        self.client.logout()
        data = {
            "email": "admin@micropyramid.com",
            "password": "admin123",
            'is_active': False
        }
        response = self.client.post('/login/', data)
        self.assertEqual(response.status_code, 302)

    def test_login_invalid(self):
        self.client.logout()
        data = {"email": "abc@abc.com", "password": "123"}
        response = self.client.post('/login/', data)
        self.assertEqual(response.status_code, 200)

    def test_logout(self):
        self.client = Client()
        self.client.login(username="admin@micropyramid.com",
                          password="admin123")
        response = self.client.get("/logout/")
        self.assertEqual(response.status_code, 302)


class UserTestCase(ObjectsCreation, TestCase):
    def test_user_create_url(self):
        response = self.client.get('/users/create/', {
            'first_name': 'micheal',
            'last_name': "clark",
            'username': 'micheal',
            'email': 'micheal@micropyramid.com',
            'password': 'micheal123'})
        self.assertEqual(response.status_code, 200)

    def test_user_create_html(self):
        response = self.client.get('/users/create/', {
            'first_name': 'micheal',
            'last_name': "",
            'username': 'micheal',
            'email': '',
            'password': 'micheal123'})

        self.assertTemplateUsed(response, 'create.html')


class UserListTestCase(ObjectsCreation, TestCase):

    def test_users_list(self):
        self.users = User.objects.all()
        response = self.client.get('/users/list/')
        # get_img_url = self.users.filter()
        get_user = User.objects.get(email='admin@micropyramid.com')
        self.assertEqual(get_user.email, get_user.__str__())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'list.html')

    def test_users_list_queryset(self):
        self.user = User.objects.all()
        data = {'first_name': 'admin', 'username': 'admin',
                'email': 'admin@micropyramid.com'}
        response = self.client.post('/users/list/', data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'list.html')


class UserRemoveTestCase(ObjectsCreation, TestCase):
    def test_users_remove(self):
        response = self.client.get('/users/' + str(self.user.id) + '/delete/')
        self.assertEqual(response['location'], '/users/list/')

    # def test_user_remove_status(self):
    #     User.objects.filter(id=self.user.id).delete()
    #     response = self.client.get('/users/list/')
    #     self.assertEqual(response.status_code, 302)


class UserUpdateTestCase(ObjectsCreation, TestCase):
    def test_users_update(self):
        response = self.client.get('/users/' + str(self.user.id) + '/edit/', {
            'first_name': "admin",
            'user_name': 'admin',
            'email': "admin@micropyramid"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create.html')

    def test_accounts_update_post(self):
        response = self.client.post('/users/' + str(self.user.id) + '/edit/',
                                    {'first_name': "micheal",
                                     'user_name': 'micheal',
                                     'email': "abc@micropyramid",
                                     'role': "USER",
                                     'is_superuser': False})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create.html')

    def test_accounts_update_status(self):
        response = self.client.get('/users/' + str(self.user.id) + '/edit/')
        self.assertEqual(response.status_code, 200)

    def test_accounts_update_html(self):
        response = self.client.get('/users/' + str(self.user.id) + '/edit/')
        self.assertTemplateUsed(response, 'create.html')

# class DocumentCreateViewTestCase(ObjectsCreation,TestCase):
#     def test_document_create(self):
#         url = '/documents/create/'
#         data = {'title':"xyz",'document_file':"2.png",'created_by':self.user}
#         response = self.client.post(url,data)
#         self.assertEqual(response.status_code,200)
#     def test_update_document(self):
#         url = "/documents/"+str(self.document.id)+"/edit/"
#         data = {'title':"meg",'document_file':"image.png",'created_by':self.user}
#         repsonse = self.client.post(url,data)
#         self.assertEqual(response.status_code,200)


class ProfileViewTestCase(ObjectsCreation, TestCase):
    def test_profile_view(self):
        url = "/profile/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    # def test_context_data(self):
    #     user_login = self.client.login(
    #         username='admin@micropyramid.com', password='admin123')
    #     url = "/profile/"
    #     response = self.client.get(url)
    #     print(response, "hello")
    #     self.assertContains(response,'admin@micropyramid.com')


class UserDetailView(ObjectsCreation, TestCase):
    def test_user_detail(self):
        url = "/users/" + str(self.user.id) + "/view/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class DocumentDetailView(ObjectsCreation, TestCase):
    def test_document_detail(self):
        url = "/documents/" + str(self.document.id) + "/view/"
        repsonse = self.client.get(url)
        get_title = Document.objects.get(title='abc')
        self.assertEqual(get_title.title, str(self.document))
        # print('-----------------',self.document.title)
        self.assertEqual(repsonse.status_code, 200)


class CreateCommentFile(TestCase):
    def test_invalid_user_form(self):
        fields = ['email',
                  'first_name',
                  'last_name',
                  'username', 'role',
                  'profile_pic']
        user1 = User.objects.create(username='robert',
                                    first_name='robert',
                                    last_name='clark',
                                    email='tr@mp.com',
                                    role='USER',
                                    profile_pic="",
                                    password='123')
        data = {'email': user1.email, 'first_name': user1.first_name,
                'last_name': user1.last_name,
                'username': user1.username, 'role': user1.role,
                'profile_pic': user1.profile_pic,
                'password': user1.password}
        form = UserForm(data=data)
        userr = User.objects.get(username='robert')
        # print(userr)
        self.assertEqual(len(userr.password), 3)
        self.assertFalse(form.is_valid())
        # self.assertTrue(form.)
