from django.test import TestCase
from django.test import Client
from django.urls import reverse
from common.models import User, Document, Attachments
from common.forms import *
from django.core.files.uploadedfile import SimpleUploadedFile
from leads.models import Lead
from django.utils.encoding import force_text
import json


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
                'email': 'johndoe@admin.com'}
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
