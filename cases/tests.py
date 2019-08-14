from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils.encoding import force_text

from accounts.models import Account
from cases.models import Case
from common.models import Address, Attachments, Comment, User
from contacts.models import Contact
from planner.models import Event, Reminder
from teams.models import Teams


class CaseCreation(object):

    def setUp(self):
        self.address = Address.objects.create(
            street="street name",
            city="city name",
            postcode="1234",
            country='US')

        self.user = User.objects.create(
            first_name="john",
            username='johnDoeCase',
            email='johnDoeCase@example.com',
            role="ADMIN")
        self.user.set_password('password')
        self.user.save()
        self.user1 = User.objects.create(
            first_name="jane",
            username='janeDoeCase',
            email='janeDoeCase@example.com',
            role="USER")
        self.user1.set_password('password')
        self.user1.save()
        self.client.login(email='johnDoeCase@example.com', password='password')

        self.account = Account.objects.create(
            name="account name",
            email="account@example.com", phone="12345",
            billing_address_line="",
            billing_street="street",
            billing_city="city",
            billing_postcode="1234",
            billing_country='US',
            website="www.example.com", description="account",
            created_by=self.user)

        self.contacts = Contact.objects.create(
            first_name="john doe", email="johnD@example.com", phone="12345",
            description="contact",
            created_by=self.user,
            address=self.address
        )

        self.case = Case.objects.create(
            name="case name", case_type="Problem", status="New",
            account=self.account,
            priority="Low", description="something",
            created_by=self.user, closed_on="2016-05-04")
        self.comment = Comment.objects.create(
            comment='sample comment', case=self.case,
            commented_by=self.user
        )
        self.attachment = Attachments.objects.create(
            attachment='image.png', case=self.case,
            created_by=self.user, account=self.account
        )
        self.content_type = ContentType.objects.create(
            app_label="cases1", model="case")


class CaseViewTestCase(CaseCreation, TestCase):

    def test_list_cases(self):
        self.cases = Case.objects.all()
        response = self.client.get(reverse('cases:list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['cases'][0].id, self.case.id)
        self.assertTrue(response.context['cases'])
        self.assertTemplateUsed(response, 'cases.html')

    def test_list_cases_post(self):
        self.cases = Case.objects.all()
        data = {'name': 'name',
                'status': 'status',
                'priority': 'prioty',
                'account': int(self.account.id)}
        response = self.client.post(reverse('cases:list'), data)
        self.assertEqual(response.status_code, 200)


class CaseCreationUrlTestCase(CaseCreation, TestCase):

    def test_create_cases(self):
        upload_file = open('static/images/user.png', 'rb')
        response = self.client.post('/cases/create/', {
            'name': 'new case', 'closed_on': '2019-03-14',
            'status': 'New', 'priority': "Low",
            'created_by': self.user, "assigned_to": str(self.user.id),
            'contacts': str(self.contacts.id),
            'case_attachment': SimpleUploadedFile(
                upload_file.name, upload_file.read())
        })
        self.assertEqual(response.status_code, 200)

    def test_create_cases_html(self):
        response = self.client.post('/cases/create/', {
            'name': 'new case',
            'case_type': 'Problem',
            'status': 'New',
            'account': self.account,
            'contacts': [self.contacts.id],
            'priority': "Low",
            'description': "something"})
        # self.assertTemplateUsed(response, 'create_cases.html')
        self.assertEqual(response.status_code, 200)

    def test_create_case_get_request(self):
        response = self.client.get('/cases/create/')
        self.assertEqual(response.status_code, 200)


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
        self.assertEqual(response['location'], '/cases/')

    def test_case_delete(self):
        response = self.client.post(
            '/cases/' + str(self.case.id) + '/remove/',
            {'case_id': self.case.id})
        self.assertEqual(response.status_code, 200)


class CaseUpdateTestCase(CaseCreation, TestCase):

    def test_update_case_view(self):
        response = self.client.get(
            '/cases/' + str(self.case.id) + '/edit_case/')
        self.assertEqual(response.status_code, 200)

    def test_case_update(self):
        upload_file = open('static/images/user.png', 'rb')
        response = self.client.post('/cases/' + str(self.case.id) + '/edit_case/', {
            'name': 'new case', 'closed_on': '2019-03-14',
            'status': 'New', 'priority': "Low",
            'created_by': self.user, "assigned_to": str(self.user.id),
            'contacts': str(self.contacts.id),
            'case_attachment': SimpleUploadedFile(
                upload_file.name, upload_file.read())
        })
        self.assertEqual(response.status_code, 200)

    def test_case_update_html(self):
        response = self.client.post(
            '/cases/' + str(self.case.id) + '/edit_case/',
            {'hiddenval': self.case.id})
        # self.assertTemplateUsed(response, 'create_cases.html')
        self.assertEqual(response.status_code, 200)


class CaseModelTestCase(CaseCreation, TestCase):

    def test_string_representation(self):
        case = Case(name='name', )
        self.assertEqual(str(case), case.name)


class CaseFormTestCase(CaseCreation, TestCase):

    def test_case_creation_same_name(self):
        response = self.client.post('/cases/create/',
                                    {'name': 'john doe',
                                     'case_type': 'type',
                                     'status': 'status',
                                     'account': self.account,
                                     'contacts': [self.contacts.id],
                                     'priority': 'priority',
                                     'description': 'description content'})
        self.assertEqual(response.status_code, 200)

    def test_case_create_valid(self):
        response = self.client.post('/cases/create/',
                                    {'name': 'john doe',
                                     'case_type': 'case',
                                     'status': 'status',
                                     'account': self.account,
                                     'contacts': [self.contacts.id],
                                     'priority': 'priotiy',
                                     'description': 'description content'
                                     })
        self.assertEqual(response.status_code, 200)

    def test_close_case(self):
        response = self.client.post(
            '/cases/close_case/', {'case_id': self.case.id})
        self.assertEqual(response.status_code, 200)

    def test_comment_add(self):
        self.client.login(email='janeDoeCase@example.com', password='password')
        response = self.client.post(
            '/cases/comment/add/', {'caseid': self.case.id})
        self.assertEqual(response.status_code, 200)

    def test_comment_form_valid(self):
        response = self.client.post(
            '/cases/comment/add/', {'caseid': self.case.id, 'comment': 'comment'})
        self.assertEqual(response.status_code, 200)


    def test_comment_edit(self):
        response = self.client.post(
            '/cases/comment/edit/', {'commentid': self.comment.id})
        self.assertEqual(response.status_code, 200)

    def test_comment_delete(self):
        response = self.client.post(
            '/cases/comment/remove/', {'comment_id': self.comment.id})
        self.assertEqual(response.status_code, 200)


class AttachmentTestCase(CaseCreation, TestCase):

    def test_attachment_add(self):
        upload_file = open('static/images/user.png', 'rb')
        response = self.client.post(
            '/cases/attachment/add/', {'caseid': self.case.id,
                                       'attachment': SimpleUploadedFile(
                                           upload_file.name, upload_file.read())
                                       })
        self.assertEqual(response.status_code, 200)

    def test_attachment_creation(self):
        self.client.login(email='janeDoeCase@example.com', password='password')
        response = self.client.post(
            '/cases/attachment/add/', {'caseid': self.case.id})
        self.assertEqual(response.status_code, 200)

    def test_attachment_delete(self):
        response = self.client.post(
            '/cases/attachment/remove/', {'attachment_id': self.attachment.id})
        self.assertEqual(response.status_code, 200)

    def test_attachment_deletion(self):
        self.client.login(email='janeDoeCase@example.com', password='password')
        response = self.client.post(
            '/cases/attachment/remove/', {'attachment_id': self.attachment.id})
        self.assertEqual(response.status_code, 200)


class SelectViewTestCase(CaseCreation, TestCase):

    def test_select_contact(self):
        response = self.client.get('/cases/select_contacts/')
        self.assertEqual(response.status_code, 200)


class TestCasesListViewForUser(CaseCreation, TestCase):

    def test_queryset_for_user(self):

        self.usermp = User.objects.create(
                        first_name="jane",
                        username='janeDoe@user.com',
                        email='janeDoe@user.com',
                        role="USER",
                        has_sales_access=True)
        self.usermp.set_password('password')
        self.usermp.save()

        self.usermp1 = User.objects.create(
                        first_name="john",
                        username='johnDoe@user.com',
                        email='johnDoe@user.com',
                        role="USER")
        self.usermp1.set_password('password')
        self.usermp1.save()

        self.comment_1 = Comment.objects.create(
            comment='test comment', case=self.case,
            commented_by=self.usermp
        )

        self.account_mp = Account.objects.create(
                            name="account name", email="johndoe@account.com", phone="911234567892",
                            billing_address_line="", billing_street="street name",
                            billing_city="city name",
                            billing_state="state name", billing_postcode="1234",
                            billing_country="IN",
                            website="www.example.com", created_by=self.usermp, status="open",
                            industry="SOFTWARE", description="test description")
        self.case_user = Case.objects.create(
                            name="case name", case_type="Problem", status="New",
                            account=self.account_mp,
                            priority="Low", description="something",
                            created_by=self.usermp, closed_on="2016-05-04")
        self.client.login(email='janeDoe@user.com', password='password')
        response = self.client.get(reverse('cases:list'))
        self.assertEqual(response.status_code, 200)


        self.address = Address.objects.create(
                        street="street name",
                        city="city",
                        state="state",
                        postcode=1234, country="AD")

        self.contact_mp = Contact.objects.create(
                            first_name="jane doe",
                            email="janeDoe@contact.com",
                            address=self.address,
                            description="contact",
                            created_by=self.usermp)
        self.contact_mp.assigned_to.add(self.usermp)

        response = self.client.get(reverse('cases:add_case'))
        self.assertEqual(response.status_code, 200)


    def test_create_case(self):
        upload_file = open('static/images/user.png', 'rb')
        response = self.client.post('/cases/create/', {
            'name': 'new case', 'closed_on': '2019-03-14',
            'status': 'New', 'priority': "Low",
            'created_by': self.user, "assigned_to": str(self.user.id),
            'contacts': str(self.contacts.id),
            'case_attachment': SimpleUploadedFile(
                upload_file.name, upload_file.read()),
            'savenewform':True
        })
        self.assertEqual(response.status_code, 200)

    def test_case_detail_view_error(self):
        self.usermp1 = User.objects.create(
                        first_name="joe doe",
                        username='joedoe',
                        email='joeDoeCase@user.com',
                        role="USER")
        self.usermp1.set_password('password')
        self.usermp1.save()
        self.client.login(email='joeDoeCase@user.com', password='password')
        response = self.client.get(reverse('cases:view_case', args=(self.case.id,)))
        self.assertEqual(response.status_code, 403)

    # def test_case_detail_view_assigned_users(self):
    #     self.usermp = User.objects.create(
    #                     first_name="mpmp6",
    #                     username='mpmp6',
    #                     email='mpmp6@micropyramid.com',
    #                     role="USER")
    #     self.usermp.set_password('mp')
    #     self.usermp.save()
    #     self.account_mp = Account.objects.create(
    #                         name="mike", email="mike@micropyramid.com", phone="8322855552",
    #                         billing_address_line="", billing_street="KPHB",
    #                         billing_city="New York",
    #                         billing_state="usa", billing_postcode="500073",
    #                         billing_country="IN",
    #                         website="www.mike.com", created_by=self.usermp, status="open",
    #                         industry="SOFTWARE", description="Yes.. Testing Done")
    #     self.case_2 = Case.objects.create(
    #                         name="mp_case_1", case_type="Problem", status="New",
    #                         account=self.account_mp,
    #                         priority="Low", description="something",
    #                         created_by=self.usermp, closed_on="2016-05-04", assigned_to=str(self.user.id))
    #     response = self.client.get(reverse('cases:view_case', args=(self.case_2.id,)))
    #     self.assertEqual(200, response.status_code)

    def test_case_update_test(self):

        response = self.client.post(reverse('cases:edit_case', args=(self.case.id,)), {
            'name':'some case',
            'status':'New',
            'priority':'Low',
            'closed_on':'2019-03-14'
            })
        self.assertEqual(response.status_code, 200)

    def test_permissions(self):

        self.user = User.objects.create(
                        first_name="joedoe",
                        username='joedoeCase6@user.com',
                        email='joedoeCase6@user.com',
                        role="USER")
        self.user.set_password('password')
        self.user.save()

        self.case_new = Case.objects.create(
            name="joe doe", case_type="Problem", status="New",
            priority="Low", description="something",
            created_by=self.user, closed_on="2016-05-04")

        self.usermp = User.objects.create(
                        first_name="joedoe",
                        username='joedoeCase7@user.com',
                        email='joedoeCase7@user.com',
                        role="USER")
        self.usermp.set_password('password')
        self.usermp.save()
        self.client.login(username='joedoeCase7@user.com', password='password')
        response = self.client.get(reverse('cases:edit_case', args=(self.case_new.id,)), {
            'name':'some case',
            'status':'New',
            'priority':'Low',
            'closed_on':'2019-03-14'
            })
        self.assertEqual(response.status_code, 403)

        response = self.client.get(reverse('cases:remove_case', args=(self.case.id,)))
        self.assertEqual(response.status_code, 403)

        response = self.client.post(reverse('cases:remove_case', args=(self.case.id,)),
            {'case_id':self.case_new.id})
        self.assertEqual(response.status_code, 403)

        response = self.client.post(reverse('cases:close_case'), {'case_id':self.case.id})
        self.assertEqual(response.status_code, 403)

        self.client.login(email='johnDoeCase@example.com', password='password')

        self.team_case = Teams.objects.create(name='dev team case')
        self.team_case.users.add(self.user1.id)

        response = self.client.post(reverse('cases:add_case') + '?view_account={}'.format(self.account.id), {
            'name':'team case',
            'status':'New',
            'priority':'Low',
            'closed_on':'2019-03-14',
            'teams':self.team_case.id,
            'from_account':self.account.id
            })
        self.assertEqual(200, response.status_code)

        response = self.client.get(reverse('cases:add_case') + '?view_account={}'.format(self.account.id))
        self.assertEqual(200, response.status_code)


        self.case_without_account = Case.objects.create(
            name="case_without_account", case_type="Problem", status="New",
            priority="Low", description="something",
            created_by=self.user, closed_on="2016-05-04")

        response = self.client.get(reverse('cases:view_case', args=(self.case_without_account.id,)))
        self.assertEqual(200, response.status_code)

        self.account_user = Account.objects.create(
            name="account name",
            email="account@example.com", phone="12345",
            billing_address_line="",
            billing_street="street",
            billing_city="city",
            billing_postcode="1234",
            billing_country='US',
            website="www.example.com", description="account",
            created_by=self.usermp)
        self.account_user.assigned_to.add(self.usermp.id)

        self.case_user = Case.objects.create(
            name="case user", case_type="Problem", status="New",
            priority="Low", description="something",
            account=self.account_user,
            created_by=self.usermp, closed_on="2016-05-04")

        self.usermp.has_sales_access = True
        self.usermp.save()
        self.client.logout()
        self.client.login(username='joedoeCase7@user.com', password='password')
        response = self.client.get(reverse('cases:view_case', args=(self.case_user.id,)))
        self.assertEqual(200, response.status_code)

        self.case_user_1 = Case.objects.create(
            name="case user authorization", case_type="Problem", status="New",
            priority="Low", description="something",
            created_by=self.user, closed_on="2016-05-04")

        self.case_user_1.assigned_to.add(self.user1, self.user)
        self.case_user_1.save()
        response = self.client.get(reverse('cases:view_case', args=(self.case_user_1.id,)))
        self.assertEqual(403, response.status_code)

        self.client.logout()
        self.client.login(username='joedoeCase7@user.com', password='password')
        response = self.client.get(reverse('cases:edit_case', args=(self.case_user.id,)))
        self.assertEqual(200, response.status_code)

        self.client.login(email='johnDoeCase@example.com', password='password')
        data = {
            'name':"case user", 'case_type':"Problem", 'status':"New",
            'priority':"Low", 'description':"something",
            'created_by':self.usermp, 'closed_on':"2016-05-04",
            'teams': self.team_case.id,
            'from_account':self.account.id,
        }
        response = self.client.post(reverse('cases:edit_case', args=(self.case_user.id,)), data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(200, response.status_code)

        response = self.client.get(reverse('cases:edit_case', args=(self.case_user.id,)) + '?view_account={}'.format(self.account.id))
        self.assertEqual(200, response.status_code)

        self.client.logout()
        self.client.login(username='joedoeCase7@user.com', password='password')
        response = self.client.get(reverse('cases:edit_case', args=(self.case.id,)))
        self.assertEqual(403, response.status_code)

        response = self.client.get(reverse('cases:remove_case', args=(self.case_user_1.id,)) + '?view_account={}'.format(self.account.id))
        self.assertEqual(403, response.status_code)

        self.client.logout()
        self.client.login(email='johnDoeCase@example.com', password='password')
        response = self.client.get(reverse('cases:remove_case', args=(self.case_user.id,)) + '?view_account={}'.format(self.account.id))
        self.assertEqual(302, response.status_code)

        self.case_user = Case.objects.create(
            name="case user", case_type="Problem", status="New",
            priority="Low", description="something",
            account=self.account_user,
            created_by=self.usermp, closed_on="2016-05-04")
        self.client.logout()
        self.client.login(email='johnDoeCase@example.com', password='password')
        response = self.client.post(reverse('cases:remove_case', args=(self.case_user.id,)) + '?view_account={}'.format(self.account.id),
            {'case_id': self.case_user.id}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(200, response.status_code)

        self.case_user = Case.objects.create(
            name="case user", case_type="Problem", status="New",
            priority="Low", description="something",
            account=self.account_user,
            created_by=self.usermp, closed_on="2016-05-04")

        self.client.logout()
        self.client.login(username='joedoeCase7@user.com', password='password')
        response = self.client.post(reverse('cases:remove_case', args=(self.case.id,)) + '?view_account={}'.format(self.account.id),
            {'case_id': self.case.id})
        self.assertEqual(403, response.status_code)

        data = {
            'comment':'comment update',
            'caseid': self.case.id,
            'commentid': self.comment.id
        }

        response = self.client.post(reverse('cases:edit_comment'), data)
        self.assertEqual(200, response.status_code)

        response = self.client.post(reverse('cases:close_case') + '?view_account={}'.format(self.account.id),
            {'case_id': self.case.id})
        self.assertEqual(403, response.status_code)
        data = {
            'caseid': self.case.id,
            'comment': ''
        }
        response = self.client.post(reverse('cases:add_comment'), data)
        self.assertEqual(200, response.status_code)

        self.client.logout()
        self.client.login(email='johnDoeCase@example.com', password='password')
        response = self.client.get(reverse('cases:select_contacts') + '?account={}'.format(self.account.id))
        self.assertEqual(200, response.status_code)

        data = {
            'caseid': self.case.id,
            'comment': ''
        }
        response = self.client.post(reverse('cases:add_comment'), data)
        self.assertEqual(200, response.status_code)


        data = {
            'comment':'comment update',
            'caseid': self.case.id,
            'commentid': self.comment.id
        }

        response = self.client.post(reverse('cases:edit_comment'), data)
        self.assertEqual(200, response.status_code)

        data = {
            'comment':'',
            'caseid': self.case.id,
            'commentid': self.comment.id
        }

        response = self.client.post(reverse('cases:edit_comment'), data)
        self.assertEqual(200, response.status_code)

        self.client.logout()
        self.client.login(username='joedoeCase7@user.com', password='password')
        data = {
            'comment_id': self.comment.id
        }
        response = self.client.post(reverse('cases:remove_comment'), data)
        self.assertEqual(200, response.status_code)


        self.client.logout()
        self.client.login(email='johnDoeCase@example.com', password='password')
        data = {
            'caseid': self.case.id,
            'attachment':'',
        }
        response = self.client.post(reverse('cases:add_attachment'), data)
        self.assertEqual(200, response.status_code)


    # def test_comment_add_error(self):
    #     self.client.login(email='mpmp@micropyramid.com', password='mp')
    #     response = self.client.post(reverse('cases:add_comment'), {})
    #     self.assertJSONEqual(force_text(response.content), {'error': ["This field is required."]})

    #     response = self.client.post(reverse('cases:edit_comment'), {})
    #     self.assertJSONEqual(force_text(response.content), {'error': ["This field is required."]})

    # def test_comment_edit_error(self):
    #     self.client.login(email='mpmp1@micropyramid.com', password='mp')
    #     response = self.client.post(reverse('cases:edit_comment'), {})
    #     self.assertJSONEqual(force_text(response.content), {'error': "You don't have permission to edit this comment."})
