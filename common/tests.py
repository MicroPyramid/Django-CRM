from django.test import TestCase
from django.test import Client
from django.urls import reverse
from common.models import User, Document, Attachments
from common.forms import *
from django.core.files.uploadedfile import SimpleUploadedFile
from leads.models import Lead
from teams.models import Teams
from django.utils.encoding import force_text
import json
import datetime


class ObjectsCreation(object):

    def setUp(self):
        self.client = Client()
        # self.user = User.objects.create(first_name="admin",
        #                                 username='admin',
        #                                 email='admin@micropyramid.com',
        #                                 is_staff=True,
        #                                 is_admin=True,
        #                                 is_superuser=True, is_active=True)

        self.user_admin = User.objects.create(first_name="john",
                                              username='johndoeAdmin',
                                              email='johndoe@admin.com',
                                              is_staff=True,
                                              is_admin=True,
                                              is_superuser=True,
                                              is_active=True, role='ADMIN')

        self.user_admin.set_password('password')
        self.user_admin.save()
        self.user = User.objects.create(first_name="jane",
                                        username='janedoe',
                                        email='janedoe@admin.com',
                                        is_staff=True, is_admin=True,
                                        is_superuser=True, is_active=False)
        self.user.set_password('password')
        self.user.save()
        self.user1 = User.objects.create(
            first_name="johnDoeCommon",
            username='johnDoeCommon',
            email='johnDoeCommon@user.com',
            role="USER",
            has_sales_access=True)
        self.user1.set_password('password')
        self.user1.save()
        # self.user
        self.client.login(
            username='johndoe@admin.com', password='password')
        self.document = Document.objects.create(
            title="abc", document_file="1.png", created_by=self.user)

        self.document_edit = Document.objects.create(
            title="edit title", document_file="1.png", created_by=self.user)

        self.comment = Comment.objects.create(
            comment='comment', user=self.user,
            commented_by=self.user
        )

        self.user2 = User.objects.create(
            first_name="janeDoeCommon",
            username='janeDoeCommon',
            email='janeDoeCommon@user.com',
            role="USER",
            has_sales_access=True)
        self.user2.set_password('password')
        self.user2.save()


class TestHomePage(ObjectsCreation, TestCase):

    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        if response.status_code == 200:
            self.assertIn("Micro", str(response.content))

    def test_home_page1(self):
        self.client.login(
            username='mp@micropyramid.com', password='mp')
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
            'email': 'john@doe.com',
            'first_name': '',
            'last_name': '',
            'username': '',
            'role': 'ADMIN', })
        self.assertEqual(response.status_code, 200)


class PasswordChangeTestCase(ObjectsCreation, TestCase):

    def test_password_change(self):
        self.client.login(username="johndoe@admin.com",
                          password="password")
        url = "/change-password/"
        data = {'CurrentPassword': "password",
                'Newpassword': "strongpassword", 'confirm': 'strongpassword'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

    def test_password_invalid(self):
        self.client.login(username="johndoe@admin.com",
                          password="password")
        url = "/change-password/"
        data = {'CurrentPassword': " ",
                'Newpassword': "test123", 'confirm': " "}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)

    def change_passsword_by_admin(self):
        response = self.client.post('/change-password-by-admin//', {
            'useer_id': self.user.id,
            'new_passwoord': "password"
        })
        self.assertEqual(response.status_code, 302)


class ForgotPasswordViewTestCase(ObjectsCreation, TestCase):

    def test_forgot_password(self):
        url = "/forgot-password/"
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'forgot_password.html')


class LoginViewTestCase(ObjectsCreation, TestCase):
    # user2 = User.objects.create(first_name="paul", username='paul', email='paul@micropyramid.com',
    # is_staff=True, is_admin=True, is_superuser=True, is_active=False)

    def test_login_post(self):
        self.client.logout()
        data = {"email": "johndoe@admin.com", "password": "password"}
        response = self.client.post('/login/', data)
        self.assertEqual(response.status_code, 302)

    def test_login_get_request(self):
        data = {"email": "johndoe@admin.com", "password": "password"}
        response = self.client.post('/login/', data)
        self.assertEqual(response.status_code, 302)

    def test_login_post_invalid(self):
        self.client.logout()
        data = {"email": "johndoe@admin.com", "password": "test123"}
        response = self.client.post('/login/', data)
        self.assertEqual(response.status_code, 200)

    def test_login_inactive(self):
        self.client.logout()
        data = {
            "email": "johndoe@admin.com",
            "password": "password",
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
        self.client.login(username="johndoe@admin.com",
                          password="password")
        response = self.client.get("/logout/")
        self.assertEqual(response.status_code, 302)


class UserTestCase(ObjectsCreation, TestCase):

    def test_user_create_url(self):
        response = self.client.get('/users/create/', {
            'first_name': 'john',
            'last_name': "doe",
            'username': 'john doe c',
            'email': 'johnC@doe.com',
            'password': 'password',
            'role': 'USER'})
        self.assertEqual(response.status_code, 200)

    def test_user_create_html(self):
        response = self.client.get('/users/create/', {
            'first_name': 'jane',
            'last_name': "",
            'username': 'jane doe',
            'email': '',
            'password': 'password'})

        self.assertTemplateUsed(response, 'create.html')


class UserListTestCase(ObjectsCreation, TestCase):

    def test_users_list(self):
        self.users = User.objects.all()
        response = self.client.get('/users/list/')
        # get_img_url = self.users.filter()
        get_user = User.objects.get(email='johndoe@admin.com')
        self.assertEqual(get_user.email, get_user.__str__())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'list.html')

    def test_users_list_queryset(self):
        self.user = User.objects.all()
        data = {'first_name': 'john', 'username': 'johndoeAdmin',
                'email': 'johndoe@admin.com', 'role':'ADMIN', 'status':'True'}
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
            'first_name': "john",
            'user_name': 'johndoeAdmin',
            'email': "johndoe@admin.com"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create.html')

    def test_accounts_update_post(self):
        response = self.client.post('/users/' + str(self.user.id) + '/edit/',
                                    {'first_name': "john",
                                     'user_name': 'john doe search',
                                     'email': "johnDoe@search.com",
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
        user1 = User.objects.create(username='janedoeUser',
                                    first_name='jane',
                                    last_name='doe',
                                    email='janedoeUser@example.com',
                                    role='USER',
                                    profile_pic="",
                                    password='password')
        data = {'email': user1.email, 'first_name': user1.first_name,
                'last_name': user1.last_name,
                'username': user1.username, 'role': user1.role,
                'profile_pic': user1.profile_pic,
                'password': user1.password}
        form = UserForm(data=data, request_user=user1)
        userr = User.objects.get(username='janedoeUser')
        # print(userr)
        self.assertEqual(len(userr.password), 8)
        self.assertFalse(form.is_valid())
        # self.assertTrue(form.)


class CommentTestCase(ObjectsCreation, TestCase):

    def test_comment_add(self):
        response = self.client.post(
            '/comment/add/', {'userid': self.user.id})
        self.assertEqual(response.status_code, 200)

    def test_comment_edit(self):
        response = self.client.post(reverse('common:edit_comment',
                                            kwargs={'pk': self.comment.id}))
        self.assertEqual(response.status_code, 200)
        resp = self.client.post(reverse('common:edit_comment',
                                        kwargs={'pk': self.comment.id}), {'comment': 'hello123'})
        self.assertEqual(resp.status_code, 200)

    def test_comment_delete(self):
        response = self.client.post(
            '/comment/remove/', {'comment_id': self.comment.id})
        self.assertEqual(response.status_code, 200)

    def test_form_valid(self):
        response = self.client.post(
            '/comment/add/', {'userid': self.user.id,
                              'comment': 'hello'})
        self.assertEqual(response.status_code, 200)


class DocumentTestCase(ObjectsCreation, TestCase):

    def test_document_add(self):
        response = self.client.post(
            '/documents/create/')
        self.assertEqual(response.status_code, 200)

    def test_document_create(self):
        response = self.client.post(
            '/documents/create/')
        self.assertEqual(response.status_code, 200)

    def test_document_edit(self):
        upload_file = open('static/images/user.png', 'rb')
        data = {'title': "doc",
                'created_by': self.user,
                'document_file': SimpleUploadedFile(
                    upload_file.name, upload_file.read()),
                'status': 'active',
                'shared_to': str(self.user.id)}
        response = self.client.get(reverse('common:edit_doc',
                                           kwargs={'pk': self.document.id}), data)
        self.assertEqual(response.status_code, 200)

    def test_document_valid(self):
        upload_file = open('static/images/user.png', 'rb')
        response = self.client.post(
            '/documents/create/', {'title': "doc",
                                   'created_by': self.user,
                                   'document_file': SimpleUploadedFile(
                                       upload_file.name, upload_file.read()),
                                   'status': 'active',
                                   'shared_to': str(self.user.id)})
        self.assertEqual(response.status_code, 200)

    def test_document_delete(self):
        response = self.client.get(reverse('common:remove_doc',
                                           kwargs={'pk': self.document.id}))
        self.assertEqual(response.status_code, 302)

    def test_document_list_view(self):
        response = self.client.get(reverse('common:doc_list'))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('common:doc_list'), {
            'doc_name': 'doc',
            'status': 'active',
            "shared_to": str(self.user.id)
        })
        self.assertEqual(response.status_code, 200)


# class TestDownloadDocument(ObjectsCreation, TestCase):

#     def test_download_document(self):

#         self.document1 = Document.objects.create(
#             title="abcd", document_file="2.png", created_by=self.user)

#         response = self.client.get(reverse('common:download_document',
#             args=(self.document1.id,)))
#         self.assertEqual(response.status_code, 200)


class TestChangeUserStatus(ObjectsCreation, TestCase):

    def test_change_user_status(self):
        response = self.client.get(reverse('common:change_user_status',
                                           args=(self.user2.id,)))
        self.assertEqual(response.status_code, 302)


class TestDocumentListViewUser(ObjectsCreation, TestCase):

    def test_document_list_view_user(self):
        response = self.client.get(reverse('common:doc_list'))
        self.assertEqual(response.status_code, 200)


class TestViewApiSettings(ObjectsCreation, TestCase):

    def test_view_api_settings(self):

        self.api_settings = APISettings.objects.create(title='api key',
                                                       apikey='a45fds54fds54',
                                                       website='https://micropyramid.com')

        response = self.client.get(reverse('common:api_settings'))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            reverse('common:view_api_settings', args=(self.api_settings.id,)))
        self.assertEqual(response.status_code, 200)


class TestDocumentDetailViewPermissionDenied(ObjectsCreation, TestCase):

    def test_document_detail_view_permission(self):
        self.client.login(username='janeDoeCommon@user.com', password='password')
        response = self.client.get(
            reverse('common:view_doc', args=(self.document.id,)))
        self.assertEqual(response.status_code, 403)


class TestChangePasswordByAdmin(ObjectsCreation, TestCase):

    def test_change_password_by_admin(self):
        response = self.client.post(reverse('common:change_passsword_by_admin'),
                                    {'useer_id': self.user2.id, 'new_passwoord': 'new password'})
        self.assertEqual(response.status_code, 302)


class TestChangePasswordByAdminPermission(ObjectsCreation, TestCase):

    def test_change_password_by_admin_permission(self):
        self.client.login(username='janeDoeCommon@user.com', password='password')
        response = self.client.post(reverse('common:change_passsword_by_admin'),
                                    {'useer_id': self.user2.id, 'new_passwoord': 'new password'})
        self.assertEqual(response.status_code, 403)
        self.client.logout()


class TestDocumentCreateForm(ObjectsCreation, TestCase):

    def test_document_create_form(self):
        upload_file = open('static/images/user.png', 'rb')
        response = self.client.post(reverse('common:create_doc'),
                                    {'title': 'doc',
                                     'document_file': SimpleUploadedFile(upload_file.name, upload_file.read()),
                                     'shared_to': str(self.user1.id)})
        self.assertEqual(response.status_code, 200)


class TestCommentDelete(ObjectsCreation, TestCase):

    def test_comment_delete_form(self):
        self.lead = Lead.objects.create(title="Sample lead title",
                                        first_name="jan doe",
                                        last_name="doe",
                                        email="janeDoe@email.com",
                                        address_line="",
                                        street="street name",
                                        city="city name",
                                        state="state name",
                                        postcode="1234",
                                        country="AD",
                                        website="www.example.com",
                                        status="assigned",
                                        source="Call",
                                        opportunity_amount="700",
                                        description="description lead",
                                        created_by=self.user_admin)
        self.comment_user = Comment.objects.create(comment='test comment',
                                                   commented_by=self.user_admin, lead=self.lead)
        response = self.client.post(reverse('common:remove_comment'),
                                    {'comment_id': self.comment_user.id})
        self.assertJSONEqual(force_text(response.content), {
                             "cid": str(self.comment_user.id)})


class TestCommentEditErrors(ObjectsCreation, TestCase):

    def test_comment_edit_form(self):
        self.lead = Lead.objects.create(title="Sample lead title",
                                        first_name="jan doe",
                                        last_name="doe",
                                        email="janeDoe@email.com",
                                        address_line="",
                                        street="street name",
                                        city="city name",
                                        state="state name",
                                        postcode="1234",
                                        country="AD",
                                        website="www.example.com",
                                        status="assigned",
                                        source="Call",
                                        opportunity_amount="700",
                                        description="description lead",
                                        created_by=self.user_admin)
        self.comment_user = Comment.objects.create(comment='comment test',
                                                   commented_by=self.user_admin, lead=self.lead)
        response = self.client.post(reverse('common:edit_comment', args=(self.comment_user.id,)),
                                    {'pk': self.comment_user.id, 'comment': ''})
        self.assertJSONEqual(force_text(response.content), {
                             "error": ['This field is required.']})

        response = self.client.post(reverse('common:edit_comment', args=(self.comment_user.id,)),
                                    {'pk': self.comment_user.id, 'comment': 'comment'})

        self.assertJSONEqual(force_text(response.content), {
                             "comment_id": self.comment_user.id, "comment": 'comment'})


class TestDocumentListUser(ObjectsCreation, TestCase):

    def test_doc_list_user(self):
        self.client.login(username='janeDoeCommon@user.com', password='password')
        response = self.client.get(reverse('common:doc_list'))
        self.assertEqual(response.status_code, 200)


class TestDocumentDelete(ObjectsCreation, TestCase):

    def test_document_delete(self):
        self.client.login(username='janeDoeCommon@user.com', password='password')
        response = self.client.get(
            reverse('common:remove_doc', args=(self.document.id,)))
        self.assertEqual(response.status_code, 403)


class TestDocumentUpdate(ObjectsCreation, TestCase):

    def test_document_update(self):
        response = self.client.get(
            reverse('common:edit_doc', args=(self.document.id,)), {'title': "title name"})
        self.assertEqual(response.status_code, 200)


class TestUserUpdate(ObjectsCreation, TestCase):

    def test_user_update(self):
        response = self.client.post(
            reverse('common:edit_user', args=(self.user2.id,)), {})
        self.assertTrue('error' in str(response.content))
        response = self.client.post(reverse('common:edit_user', args=(self.user2.id,)), {
            'first_name': 'janeDoe',
            'last_name': '',
            'username': 'jane doe@common',
            'role': 'USER',
            'email': 'janeDoeCommon@user.com',
            'has_sales_access': 'true'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(force_text(response.content), json.dumps(
            {'success_url': reverse('common:users_list'), 'error': False}))

        response = self.client.post(reverse('common:edit_user', args=(self.user2.id,)), {},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertJSONEqual(force_text(response.content),
                             json.dumps({"error": True, "errors": {"email": ["This field is required."],
                                                                   "first_name": ["This field is required."], "username": ["This field is required."],
                                                                   "role": ["This field is required."],
                                                                   'has_sales_access': ['Select atleast one option.']}}))

    def test_user_update_permissions(self):
        self.user_obj = User.objects.create(
            first_name="joe",
            username='doe',
            email='joedoe@common.com',
            role="USER")
        self.user_obj.set_password('password')
        self.user_obj.save()
        self.client.login(username='janeDoeCommon@user.com', password='password')
        response = self.client.post(reverse('common:edit_user', args=(self.user_obj.id,)), {
            'first_name': 'joe',
            'last_name': 'doe',
            'username': 'joe d',
            'role': 'USER',
            'email': 'jodoe@common.com',
            'has_sales_access': 'true'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertJSONEqual(force_text(response.content),
                             json.dumps({"error_403": True, "error": True}))

        response = self.client.post(reverse('common:edit_user', args=(self.user2.id,)), {
            'first_name': 'janeDoeCommon',
            'last_name': 'jane doe',
            'username': 'janeDoeCommon',
            'role': 'USER',
            'email': 'janeDoeCommon@user.com',
            'has_sales_access': 'true'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertJSONEqual(force_text(response.content),
                             json.dumps({'success_url': reverse('common:profile'), 'error': False}))


class TestAPISettingsDelete(ObjectsCreation, TestCase):

    def test_api_settings_delete(self):
        self.api_settings = APISettings.objects.create(title='api key',
                                                       apikey='a45fds54fds54',
                                                       website='https://micropyramid.com')

        response = self.client.get(
            reverse('common:delete_api_settings', args=(self.api_settings.id,)))
        self.assertEqual(response.status_code, 302)

        response = self.client.get(
            reverse('common:delete_api_settings', args=(self.api_settings.id,)))
        self.assertEqual(response.status_code, 302)


class TestGetFullNameModel(ObjectsCreation, TestCase):

    def test_get_full_name(self):
        self.assertEqual('janeDoeCommon ', self.user2.get_full_name())

    def test_file_extensions(self):
        self.document_txt = Document.objects.create(
            title="txt", document_file="text.txt", created_by=self.user)

        self.document_csv = Document.objects.create(
            title="csv", document_file="sheet.csv", created_by=self.user)

        self.document_zip = Document.objects.create(
            title="zip", document_file="archive.zip", created_by=self.user)

        self.document_pdf = Document.objects.create(
            title="pdf", document_file="doc.pdf", created_by=self.user)

        self.document_other_format = Document.objects.create(
            title="file", document_file="doc_other_format", created_by=self.user)

        self.document_image = Document.objects.create(
            title="image", document_file="doc_other.png", created_by=self.user)

        self.document_video = Document.objects.create(
            title="video", document_file="doc.mp4", created_by=self.user)

        self.document_audio = Document.objects.create(
            title="audio", document_file="doc.mp3", created_by=self.user)

        self.document_code = Document.objects.create(
            title="code_file", document_file="doc.py", created_by=self.user)

        self.assertEqual(("text", "fa fa-file-alt"),
                         self.document_txt.file_type())
        self.assertEqual(("sheet", "fa fa-file-excel"),
                         self.document_csv.file_type())
        self.assertEqual(("zip", "fa fa-file-archive"),
                         self.document_zip.file_type())
        self.assertEqual(("pdf", "fa fa-file-pdf"),
                         self.document_pdf.file_type())
        self.assertEqual(("file", "fa fa-file"),
                         self.document_other_format.file_type())
        self.assertEqual(("image", "fa fa-file-image"),
                         self.document_image.file_type())
        self.assertEqual(("video", "fa fa-file-video"),
                         self.document_video.file_type())
        self.assertEqual(("audio", "fa fa-file-audio"),
                         self.document_audio.file_type())
        self.assertEqual(("code", "fa fa-file-code"),
                         self.document_code.file_type())


class TestUserCreationView(ObjectsCreation, TestCase):

    def test_user_creation_view(self):
        response = self.client.post(reverse('common:create_user'), {},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(force_text(response.content),
                         json.dumps({"error": True, "errors": {"email": ["This field is required."],
                                    "first_name": ["This field is required."],
                                    "username": ["This field is required."],
                                    "role": ["This field is required."],
                                    "has_sales_access": ["Select atleast one option."],
                                    "password": ["This field is required."]}}))

        response=self.client.post(reverse('common:create_user'), {
            'email': 'johndoe@commonUser.com',
            'first_name': 'first name',
            'username': 'joe',
            'role': 'USER',
            'password': 'testpassword',
            'has_sales_access':'true',
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(force_text(response.content), json.dumps(
            {"success_url": "/users/list/", "error": False}))

    def test_add_api_settings(self):
        response=self.client.post(reverse('common:add_api_settings'), {})
        self.assertTrue('error' in str(response.content))
        response=self.client.post(reverse('common:add_api_settings'), {
            'title': 'api title', 'lead_assigned_to': str(self.user2.id), 'website': 'https://micropyramid.com',
            'tags': 'api_tag, tag1'
        })
        self.assertJSONEqual(force_text(response.content),
                             json.dumps({'success_url': reverse("common:api_settings"), 'error': False}))

        response=self.client.post(reverse('common:add_api_settings'), {
            'title': 'api title', 'lead_assigned_to': str(self.user2.id), 'website': 'https://micropyramid.com',
            'tags': 'api_tag, tag1', 'savenewform': 'true'
        })
        self.assertJSONEqual(force_text(response.content),
                             json.dumps({'success_url': reverse("common:add_api_settings"), 'error': False}))

        response=self.client.post(reverse('common:add_api_settings'), {
            'title': '', 'lead_assigned_to': str(self.user2.id), 'website': 'micropyramid.com',
            'tags': 'api_tag, tag1', 'savenewform': 'true'
        })
        self.assertJSONEqual(force_text(response.content),
                             json.dumps({"error": True, "errors": {"title": ["This field is required."], "website": ["Please provide valid schema"]}}))

    def test_update_api_settings(self):
        self.api_settings_update=APISettings.objects.create(title='api key update',
                                                              apikey='asdfasd',
                                                              website='https://example.com')
        response=self.client.post(
            reverse('common:update_api_settings', args=(self.api_settings_update.id,)), {})
        self.assertTrue('error' in str(response.content))
        response=self.client.post(reverse('common:update_api_settings', args=(self.api_settings_update.id,)), {
            'title': 'api key update',
            'apikey': 'asdfasd',
            'website': 'http://example.com',
            'lead_assigned_to': str(self.user2.id),
            'tags': 'api_tag_new, tag1'
        })

        response=self.client.post(reverse('common:update_api_settings', args=(self.api_settings_update.id,)), {
            'title': 'api title', 'lead_assigned_to': str(self.user2.id), 'website': 'https://micropyramid.com',
            'tags': 'api_tag, tag1', 'savenewform': 'true'
        })
        self.assertJSONEqual(force_text(response.content),
                             json.dumps({'success_url': reverse("common:add_api_settings"), 'error': False}))

        response=self.client.post(reverse('common:update_api_settings', args=(self.api_settings_update.id,)), {
            'title': '', 'lead_assigned_to': str(self.user2.id), 'website': 'micropyramid.com',
            'tags': 'api_tag, tag1', 'savenewform': 'true'
        })
        self.assertJSONEqual(force_text(response.content),
                             json.dumps({"error": True, "errors": {"title": ["This field is required."], "website": ["Please provide valid schema"]}}))

    def test_document_list_user_view(self):
        self.client.login(username='janeDoeCommon@user.com', password='password')
        self.document=Document.objects.create(
            title="user 2 doc", document_file="1.png", created_by=self.user2)
        self.document.shared_to.add(self.user2.id)
        response=self.client.get(reverse('common:doc_list'))
        self.assertEqual(200, response.status_code)

        upload_file=open('static/images/user.png', 'rb')
        response=self.client.post(reverse('common:edit_doc', args=(self.document.id,)), {
            'title': 'user 2 doc',
            'document_file': SimpleUploadedFile(upload_file.name, upload_file.read()),
            'shared_to': str(self.user2.id)
        })
        self.assertEqual(200, response.status_code)
        # self.assertEqual(force_text(response.content),
        #     json.dumps({'success_url': reverse('common:doc_list'), 'error': False}))

        # response = self.client.get(reverse('common:download_document', args=(self.document.id,)))
        # self.assertEqual(200, response.status_code)

        self.attachment=Attachments.objects.create(
            attachment=SimpleUploadedFile(upload_file.name, upload_file.read()), created_by=self.user)
        response=self.client.get(
            reverse('common:download_attachment', kwargs=({'pk': self.attachment.id})))

    def test_document_update(self):
        self.client.login(username='johnDoeCommon@user.com', password='password')
        response=self.client.get(
            reverse('common:download_document', args=(self.document.id,)))
        self.assertEqual(403, response.status_code)

    def test_user_status(self):
        self.user_status=User.objects.create(
            first_name="joedoe",
            username='joedoe@commonUser',
            email='joedoe@commonUser.com',
            role="USER",
            is_active=False
        )
        self.user_status.set_password('password')
        self.user_status.save()
        response=self.client.get(
            reverse('common:change_user_status', kwargs={'pk': self.user_status.id}))
        self.assertEqual(302, response.status_code)



class TestUserAuthorization(ObjectsCreation, TestCase):

    def test_marketing_access_decorator(self):
        self.client.login(
            username='johnDoeCommon@user.com', password='password')
        response = self.client.get(reverse('marketing:dashboard'))
        self.assertEqual(403, response.status_code)


class TestUserFormValidation(ObjectsCreation, TestCase):

    def test_marketing_access_decorator(self):
        self.client.login(
            username='janedoe@admin.com', password='password')

        data = {'Newpassword': 'password', 'confirm': 'pas'}
        response = self.client.post(reverse('common:change_password'), data)
        self.assertEqual(200, response.status_code)

    def test_email_password_reset(self):
        self.client.logout()
        data = {'email': 'some@random.email'}
        response = self.client.post(reverse('common:password_reset'), data)
        self.assertEqual(200, response.status_code)

    def test_document_unique_title(self):
        self.client.login(username='janedoe@admin.com', password='password')
        data = {'title': 'edit title'}
        response = self.client.post(reverse('common:edit_doc', args=(self.document.id,)), data)
        json_response = {"error": True, "errors": {"title": ["Document with this Title already exists"]}}
        self.assertJSONEqual(force_text(response.content), json.dumps(json_response))

        data = {'title': 'edit title'}
        response = self.client.post(reverse('common:create_doc'), data)
        json_response = {"error": True, "errors": {"title": ["Document\u00a0with this Title\u00a0already exists"], "document_file": ["This field is required."]}}
        self.assertJSONEqual(force_text(response.content), json.dumps(json_response))

    def test_api_setting_form(self):
        data = {'website' : 'http://localhost:8000'}
        response = self.client.post(reverse('common:add_api_settings'), data)
        json_response = json.dumps({"error": True, "errors": {"title": ["This field is required."], "website": ["Please provide a valid URL with schema and without trailing slash - Example: http://google.com"]}})
        self.assertJSONEqual(force_text(response.content), json_response)

    def test_get_complete_address(self):

        Address_obj_street=Address.objects.create(street='street')
        Address_obj_city=Address.objects.create(city='city')
        Address_obj_address_line=Address.objects.create(address_line='address_line')
        Address_obj_state=Address.objects.create(state='state')
        Address_obj_postcode=Address.objects.create(postcode='postcode')
        Address_obj_country=Address.objects.create(country='IN')
        Address_obj_street_city=Address.objects.create(street='street',city='city')
        Address_obj_street_address_line=Address.objects.create(street='street',address_line='address_line')
        Address_obj_street_state=Address.objects.create(street='street',state='state')
        Address_obj_street_postcode=Address.objects.create(street='street',postcode='postcode')
        Address_obj_street_country=Address.objects.create(street='street',country='IN')
        Address_obj_city_address_line=Address.objects.create(city='city',address_line='address_line')
        Address_obj_city_state=Address.objects.create(city='city',state='state')
        Address_obj_city_postcode=Address.objects.create(city='city',postcode='postcode')
        Address_obj_city_country=Address.objects.create(city='city',country='IN')
        Address_obj_address_line_state=Address.objects.create(address_line='address_line',state='state')
        Address_obj_address_line_postcode=Address.objects.create(address_line='address_line',postcode='postcode')
        Address_obj_address_line_country=Address.objects.create(address_line='address_line',country='IN')
        Address_obj_state_postcode=Address.objects.create(state='state',postcode='postcode')
        Address_obj_state_country=Address.objects.create(state='state',country='IN')
        Address_obj_postcode_country=Address.objects.create(postcode='postcode',country='IN')
        Address_obj_street_city_address_line=Address.objects.create(street='street',city='city',address_line='address_line')
        Address_obj_street_city_state=Address.objects.create(street='street',city='city',state='state')
        Address_obj_street_city_postcode=Address.objects.create(street='street',city='city',postcode='postcode')
        Address_obj_street_city_country=Address.objects.create(street='street',city='city',country='IN')
        Address_obj_street_address_line_state=Address.objects.create(street='street',address_line='address_line',state='state')
        Address_obj_street_address_line_postcode=Address.objects.create(street='street',address_line='address_line',postcode='postcode')
        Address_obj_street_address_line_country=Address.objects.create(street='street',address_line='address_line',country='IN')
        Address_obj_street_state_postcode=Address.objects.create(street='street',state='state',postcode='postcode')
        Address_obj_street_state_country=Address.objects.create(street='street',state='state',country='IN')
        Address_obj_street_postcode_country=Address.objects.create(street='street',postcode='postcode',country='IN')
        Address_obj_city_address_line_state=Address.objects.create(city='city',address_line='address_line',state='state')
        Address_obj_city_address_line_postcode=Address.objects.create(city='city',address_line='address_line',postcode='postcode')
        Address_obj_city_address_line_country=Address.objects.create(city='city',address_line='address_line',country='IN')
        Address_obj_city_state_postcode=Address.objects.create(city='city',state='state',postcode='postcode')
        Address_obj_city_state_country=Address.objects.create(city='city',state='state',country='IN')
        Address_obj_city_postcode_country=Address.objects.create(city='city',postcode='postcode',country='IN')
        Address_obj_address_line_state_postcode=Address.objects.create(address_line='address_line',state='state',postcode='postcode')
        Address_obj_address_line_state_country=Address.objects.create(address_line='address_line',state='state',country='IN')
        Address_obj_address_line_postcode_country=Address.objects.create(address_line='address_line',postcode='postcode',country='IN')
        Address_obj_state_postcode_country=Address.objects.create(state='state',postcode='postcode',country='IN')
        Address_obj_street_city_address_line_state=Address.objects.create(street='street',city='city',address_line='address_line',state='state')
        Address_obj_street_city_address_line_postcode=Address.objects.create(street='street',city='city',address_line='address_line',postcode='postcode')
        Address_obj_street_city_address_line_country=Address.objects.create(street='street',city='city',address_line='address_line',country='IN')
        Address_obj_street_city_state_postcode=Address.objects.create(street='street',city='city',state='state',postcode='postcode')
        Address_obj_street_city_state_country=Address.objects.create(street='street',city='city',state='state',country='IN')
        Address_obj_street_city_postcode_country=Address.objects.create(street='street',city='city',postcode='postcode',country='IN')
        Address_obj_street_address_line_state_postcode=Address.objects.create(street='street',address_line='address_line',state='state',postcode='postcode')
        Address_obj_street_address_line_state_country=Address.objects.create(street='street',address_line='address_line',state='state',country='IN')
        Address_obj_street_address_line_postcode_country=Address.objects.create(street='street',address_line='address_line',postcode='postcode',country='IN')
        Address_obj_street_state_postcode_country=Address.objects.create(street='street',state='state',postcode='postcode',country='IN')
        Address_obj_city_address_line_state_postcode=Address.objects.create(city='city',address_line='address_line',state='state',postcode='postcode')
        Address_obj_city_address_line_state_country=Address.objects.create(city='city',address_line='address_line',state='state',country='IN')
        Address_obj_city_address_line_postcode_country=Address.objects.create(city='city',address_line='address_line',postcode='postcode',country='IN')
        Address_obj_city_state_postcode_country=Address.objects.create(city='city',state='state',postcode='postcode',country='IN')
        Address_obj_address_line_state_postcode_country=Address.objects.create(address_line='address_line',state='state',postcode='postcode',country='IN')
        Address_obj_street_city_address_line_state_postcode=Address.objects.create(street='street',city='city',address_line='address_line',state='state',postcode='postcode')
        Address_obj_street_city_address_line_state_country=Address.objects.create(street='street',city='city',address_line='address_line',state='state',country='IN')
        Address_obj_street_city_address_line_postcode_country=Address.objects.create(street='street',city='city',address_line='address_line',postcode='postcode',country='IN')
        Address_obj_street_city_state_postcode_country=Address.objects.create(street='street',city='city',state='state',postcode='postcode',country='IN')
        Address_obj_street_address_line_state_postcode_country=Address.objects.create(street='street',address_line='address_line',state='state',postcode='postcode',country='IN')
        Address_obj_city_address_line_state_postcode_country=Address.objects.create(city='city',address_line='address_line',state='state',postcode='postcode',country='IN')
        Address_obj_street_city_address_line_state_postcode_country=Address.objects.create(street='street',city='city',address_line='address_line',state='state',postcode='postcode',country='IN')

        self.assertEqual(Address_obj_street.get_complete_address(), "street")
        self.assertEqual(Address_obj_city.get_complete_address(), "city")
        self.assertEqual(Address_obj_address_line.get_complete_address(), "address_line")
        self.assertEqual(Address_obj_state.get_complete_address(), "state")
        self.assertEqual(Address_obj_postcode.get_complete_address(), "postcode")
        self.assertEqual(Address_obj_country.get_complete_address(), "India")
        self.assertEqual(Address_obj_street_city.get_complete_address(), "street, city")
        self.assertEqual(Address_obj_street_address_line.get_complete_address(), "address_line, street")
        self.assertEqual(Address_obj_street_state.get_complete_address(), "street, state")
        self.assertEqual(Address_obj_street_postcode.get_complete_address(), "street, postcode")
        self.assertEqual(Address_obj_street_country.get_complete_address(), "street, India")
        self.assertEqual(Address_obj_city_address_line.get_complete_address(), "address_line, city")
        self.assertEqual(Address_obj_city_state.get_complete_address(), "city, state")
        self.assertEqual(Address_obj_city_postcode.get_complete_address(), "city, postcode")
        self.assertEqual(Address_obj_city_country.get_complete_address(), "city, India")
        self.assertEqual(Address_obj_address_line_state.get_complete_address(), "address_line, state")
        self.assertEqual(Address_obj_address_line_postcode.get_complete_address(), "address_line, postcode")
        self.assertEqual(Address_obj_address_line_country.get_complete_address(), "address_line, India")
        self.assertEqual(Address_obj_state_postcode.get_complete_address(), "state, postcode")
        self.assertEqual(Address_obj_state_country.get_complete_address(), "state, India")
        self.assertEqual(Address_obj_postcode_country.get_complete_address(), "postcode, India")
        self.assertEqual(Address_obj_street_city_address_line.get_complete_address(), "address_line, street, city")
        self.assertEqual(Address_obj_street_city_state.get_complete_address(), "street, city, state")
        self.assertEqual(Address_obj_street_city_postcode.get_complete_address(), "street, city, postcode")
        self.assertEqual(Address_obj_street_city_country.get_complete_address(), "street, city, India")
        self.assertEqual(Address_obj_street_address_line_state.get_complete_address(), "address_line, street, state")
        self.assertEqual(Address_obj_street_address_line_postcode.get_complete_address(), "address_line, street, postcode")
        self.assertEqual(Address_obj_street_address_line_country.get_complete_address(), "address_line, street, India")
        self.assertEqual(Address_obj_street_state_postcode.get_complete_address(), "street, state, postcode")
        self.assertEqual(Address_obj_street_state_country.get_complete_address(), "street, state, India")
        self.assertEqual(Address_obj_street_postcode_country.get_complete_address(), "street, postcode, India")
        self.assertEqual(Address_obj_city_address_line_state.get_complete_address(), "address_line, city, state")
        self.assertEqual(Address_obj_city_address_line_postcode.get_complete_address(), "address_line, city, postcode")
        self.assertEqual(Address_obj_city_address_line_country.get_complete_address(), "address_line, city, India")
        self.assertEqual(Address_obj_city_state_postcode.get_complete_address(), "city, state, postcode")
        self.assertEqual(Address_obj_city_state_country.get_complete_address(), "city, state, India")
        self.assertEqual(Address_obj_city_postcode_country.get_complete_address(), "city, postcode, India")
        self.assertEqual(Address_obj_address_line_state_postcode.get_complete_address(), "address_line, state, postcode")
        self.assertEqual(Address_obj_address_line_state_country.get_complete_address(), "address_line, state, India")
        self.assertEqual(Address_obj_address_line_postcode_country.get_complete_address(), "address_line, postcode, India")
        self.assertEqual(Address_obj_state_postcode_country.get_complete_address(), "state, postcode, India")
        self.assertEqual(Address_obj_street_city_address_line_state.get_complete_address(), "address_line, street, city, state")
        self.assertEqual(Address_obj_street_city_address_line_postcode.get_complete_address(), "address_line, street, city, postcode")
        self.assertEqual(Address_obj_street_city_address_line_country.get_complete_address(), "address_line, street, city, India")
        self.assertEqual(Address_obj_street_city_state_postcode.get_complete_address(), "street, city, state, postcode")
        self.assertEqual(Address_obj_street_city_state_country.get_complete_address(), "street, city, state, India")
        self.assertEqual(Address_obj_street_city_postcode_country.get_complete_address(), "street, city, postcode, India")
        self.assertEqual(Address_obj_street_address_line_state_postcode.get_complete_address(), "address_line, street, state, postcode")
        self.assertEqual(Address_obj_street_address_line_state_country.get_complete_address(), "address_line, street, state, India")
        self.assertEqual(Address_obj_street_address_line_postcode_country.get_complete_address(), "address_line, street, postcode, India")
        self.assertEqual(Address_obj_street_state_postcode_country.get_complete_address(), "street, state, postcode, India")
        self.assertEqual(Address_obj_city_address_line_state_postcode.get_complete_address(), "address_line, city, state, postcode")
        self.assertEqual(Address_obj_city_address_line_state_country.get_complete_address(), "address_line, city, state, India")
        self.assertEqual(Address_obj_city_address_line_postcode_country.get_complete_address(), "address_line, city, postcode, India")
        self.assertEqual(Address_obj_city_state_postcode_country.get_complete_address(), "city, state, postcode, India")
        self.assertEqual(Address_obj_address_line_state_postcode_country.get_complete_address(), "address_line, state, postcode, India")
        self.assertEqual(Address_obj_street_city_address_line_state_postcode.get_complete_address(), "address_line, street, city, state, postcode")
        self.assertEqual(Address_obj_street_city_address_line_state_country.get_complete_address(), "address_line, street, city, state, India")
        self.assertEqual(Address_obj_street_city_address_line_postcode_country.get_complete_address(), "address_line, street, city, postcode, India")
        self.assertEqual(Address_obj_street_city_state_postcode_country.get_complete_address(), "street, city, state, postcode, India")
        self.assertEqual(Address_obj_street_address_line_state_postcode_country.get_complete_address(), "address_line, street, state, postcode, India")
        self.assertEqual(Address_obj_city_address_line_state_postcode_country.get_complete_address(), "address_line, city, state, postcode, India")
        self.assertEqual(Address_obj_street_city_address_line_state_postcode_country.get_complete_address(), "address_line, street, city, state, postcode, India")

        self.assertEqual(str(Address_obj_street), "")
        self.assertEqual(str(Address_obj_city), "city")

    def test_file_extensions_classes(self):
        doc_mp3=Attachments.objects.create(file_name="file_mp3",attachment="file.mp3")
        doc_mp4=Attachments.objects.create(file_name="file_mp4",attachment="file.mp4")
        doc_png=Attachments.objects.create(file_name="file_png",attachment="file.png")
        doc_pdf=Attachments.objects.create(file_name="file_pdf",attachment="file.pdf")
        doc_json=Attachments.objects.create(file_name="file_json",attachment="file.json")
        doc_txt=Attachments.objects.create(file_name="file_txt",attachment="file.txt")
        doc_csv=Attachments.objects.create(file_name="file_csv",attachment="file.csv")
        doc_zip=Attachments.objects.create(file_name="file_zip",attachment="file.zip")
        doc_unknown_extension=Attachments.objects.create(file_name="file_unknown_extension",attachment="file.unknown_extension")
        doc_without_extension=Attachments.objects.create(file_name="file_unknown_extension",attachment="file_without_extension")
        doc_without_attachment=Attachments.objects.create(file_name="file_unknown_extension")


        self.assertEqual(doc_mp3.file_type(), ('audio', 'fa fa-file-audio'))
        self.assertEqual(doc_mp4.file_type(), ('video', 'fa fa-file-video'))
        self.assertEqual(doc_png.file_type(), ('image', 'fa fa-file-image'))
        self.assertEqual(doc_pdf.file_type(), ('pdf', 'fa fa-file-pdf'))
        self.assertEqual(doc_json.file_type(), ('code', 'fa fa-file-code'))
        self.assertEqual(doc_txt.file_type(), ('text', 'fa fa-file-alt'))
        self.assertEqual(doc_csv.file_type(), ('sheet', 'fa fa-file-excel'))
        self.assertEqual(doc_zip.file_type(), ('zip', 'fa fa-file-archive'))
        self.assertEqual(doc_unknown_extension.file_type(), ('file', 'fa fa-file'))
        self.assertEqual(doc_without_extension.file_type(), ('file', 'fa fa-file'))

        self.assertEqual(doc_csv.get_file_type_display(), ('fa fa-file-excel'))
        self.assertEqual(doc_without_attachment.get_file_type_display(), None)
        self.assertTrue(doc_csv.created_on_arrow in ['just now', 'seconds ago'])
        self.assertTrue(self.document.created_on_arrow in ['just now', 'seconds ago'])

    def test_api_settings_str(self):
        api_obj = APISettings.objects.create(title='api setting')
        self.assertEqual('api setting', str(api_obj))

    def test_arrow_format(self):
        date = datetime.datetime.today() + datetime.timedelta(days=-2)
        self.comment = Comment.objects.create(
            comment='comment', user=self.user,
            commented_by=self.user, commented_on = date
        )
        self.assertTrue(self.comment.commented_on_arrow in ['just now', 'seconds ago'])


class TestViewFunctions(ObjectsCreation, TestCase):

    def test_404_handler(self):
        self.client.login(username='johndoe@admin.com', password='password')
        response = self.client.get('/not-existing-url')
        self.assertTemplateUsed(response, '404.html')

    def test_admin_mixin(self):
        self.client.login(username='janeDoeCommon@user.com', password='password')
        response = self.client.get(reverse('common:users_list'))
        self.assertEqual(403, response.status_code)
        response = self.client.get(reverse('common:home'))
        self.assertEqual(200, response.status_code)
        response = self.client.get(reverse('common:change_password'))
        self.assertEqual(200, response.status_code)


        self.client.logout()
        response = self.client.get(reverse('common:login'))
        self.assertEqual(200, response.status_code)

        data = {'email' : 'janeDoeCommon@user.com', 'password' : 'password'}
        response = self.client.post(reverse('common:login'), data)
        self.assertEqual(302, response.status_code)

        self.client.logout()
        self.user_marketing = User.objects.create(
            first_name="johnDoeCommonMarketing",
            username='johnDoeCommonMarketing',
            email='johnDoeCommonMarketing@user.com',
            role="USER",
            has_marketing_access=True, is_active=True)
        self.user_marketing.set_password('password')
        self.user_marketing.save()
        data = {'email': 'johnDoeCommonMarketing@user.com', 'password': 'password'}
        response = self.client.post(reverse('common:login'), data)
        self.assertEqual(302, response.status_code)

        self.user_marketing.is_active = False
        self.user_marketing.save()
        data = {'email' : 'johnDoeCommonMarketing@user.com', 'password' : 'password'}
        response = self.client.post(reverse('common:login'), data)
        self.assertEqual(200, response.status_code)

        data = {'email' : 'invalid@account.com', 'password' : 'password'}
        response = self.client.post(reverse('common:login'), data)
        self.assertEqual(200, response.status_code)

    def test_user_list(self):
        self.client.login(username='johndoe@admin.com', password='password')
        response = self.client.post(reverse('common:users_list'), data={'role':'USER'})
        self.assertEqual(200, response.status_code)

    def test_user_create_with_team(self):
        self.client.login(username='johndoe@admin.com', password='password')
        self.team_dev = Teams.objects.create(name='dev team')
        response = self.client.post('/users/create/', {
            'email': 'john@developer.com',
            'first_name': 'john',
            'last_name': 'dev',
            'username': 'john@developer.com',
            'password': 'password',
            'role': 'USER', 'teams':[self.team_dev.id,],
            'has_sales_access':'on'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        # response = self.client.post('/users/create/', {
        #     'email': 'jane@developer.com',
        #     'first_name': 'jane',
        #     'last_name': 'dev',
        #     'username': 'jane@developer.com',
        #     'password': 'password',
        #     'role': 'USER', 'teams':[self.team_dev.id,],
        #     'has_sales_access':'on'})
        # self.assertEqual(response.status_code, 302)
        # response = self.client.post('/users/create/', {
        #     'email': 'jane.com',
        #     'first_name': 'jane',
        #     'last_name': 'dev',
        #     'username': 'jane@developer.com',
        #     'password': 'password',
        #     'role': 'USER',
        #     'has_sales_access':'on'})
        # self.assertEqual(response.status_code, 200)
        user_id = User.objects.filter(email='john@developer.com').first().id
        user_edit_url = reverse('common:edit_user', args=(user_id,))
        self.team_test = Teams.objects.create(name='test team')
        response = self.client.post(user_edit_url, {
            'email': 'john@developer.com',
            'first_name': 'john',
            'last_name': 'dev',
            'username': 'john@developer.com',
            'password': 'password',
            'role': 'USER', 'teams':[self.team_test.id,],
            'has_sales_access':'on'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)


    def test_admin_profile_edit(self):
        self.client.login(username='johndoe@admin.com', password='password')
        user_edit_url = reverse('common:edit_user', args=(self.user_admin.id,))
        response = self.client.post(user_edit_url, {
        'email': 'johndoe@admin.com',
        'first_name': 'john',
        'username': 'johndoeAdmin',
        'role': 'ADMIN'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_doc_create(self):
        self.client.login(username='janeDoeCommon@user.com', password='password')
        response = self.client.post(reverse('common:create_doc'), {})
        self.assertEqual(response.status_code, 200)

        self.team_test = Teams.objects.create(name='test team 1')
        self.team_test.users.add(self.user1.id, self.user2.id)

        upload_file = open('static/images/user.png', 'rb')
        shared_user = User.objects.filter(email='johndoe@admin.com').first()
        data = {
            'title':"new doc", 'document_file': SimpleUploadedFile(upload_file.name, upload_file.read()),
            'teams':[self.team_test.id, ],
            'shared_to': [shared_user.id, ]
        }
        response = self.client.post(reverse('common:create_doc'), data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        upload_file = open('static/images/user.png', 'rb')
        data = {
            'title':"another new doc", 'document_file': SimpleUploadedFile(upload_file.name, upload_file.read()),
            'teams':[self.team_test.id, ],
            'shared_to': [shared_user.id, ]
        }
        response = self.client.post(reverse('common:edit_doc', args=(self.document.id,)), data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        self.client.login(username='johndoe@admin.com', password='password')
        response = self.client.get(reverse('common:download_document', args=(self.document.id,)))
        self.assertEqual(200, response.status_code)