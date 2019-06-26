from django.test import TestCase
from cases.models import Case
from contacts.models import Contact
from accounts.models import Account
from common.models import Address, Comment, Attachments
from common.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from planner.models import Event, Reminder
from django.urls import reverse
from django.utils.encoding import force_text


class CaseCreation(object):

    def setUp(self):
        self.address = Address.objects.create(
            street="6th phase",
            city="LosVegas",
            postcode="506344",
            country='US')

        self.user = User.objects.create(
            first_name="robert",
            username='robert',
            email='r@mp.com',
            role="ADMIN")
        self.user.set_password('robert')
        self.user.save()
        self.user1 = User.objects.create(
            first_name="mp",
            username='mp',
            email='mp@micropyramid.com',
            role="USER")
        self.user1.set_password('mp')
        self.user1.save()
        self.client.login(email='r@mp.com', password='robert')

        self.client.login(email='r@mp.com', password='robert')

        self.account = Account.objects.create(
            name="account",
            email="account@gmail.com", phone="12345",
            billing_address_line="",
            billing_street="6th phase",
            billing_city="LosVegas",
            billing_postcode="506344",
            billing_country='US',
            website="www.account.com", description="account",
            created_by=self.user)

        self.contacts = Contact.objects.create(
            first_name="contact", email="contact@gmail.com", phone="12345",
            description="contact",
            created_by=self.user,
            address=self.address
        )

        self.case = Case.objects.create(
            name="robert", case_type="Problem", status="New",
            account=self.account,
            priority="Low", description="something",
            created_by=self.user, closed_on="2016-05-04")
        self.comment = Comment.objects.create(
            comment='testikd', case=self.case,
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
                                    {'name': 'robert',
                                     'case_type': 'type',
                                     'status': 'status',
                                     'account': self.account,
                                     'contacts': [self.contacts.id],
                                     'priority': 'priority',
                                     'description': 'testingskdjf'})
        self.assertEqual(response.status_code, 200)

    def test_case_create_valid(self):
        response = self.client.post('/cases/create/',
                                    {'name': 'name',
                                     'case_type': 'case',
                                     'status': 'status',
                                     'account': self.account,
                                     'contacts': [self.contacts.id],
                                     'priority': 'priotiy',
                                     'description': 'tejkskjdsa'
                                     })
        self.assertEqual(response.status_code, 200)

    def test_close_case(self):
        response = self.client.post(
            '/cases/close_case/', {'case_id': self.case.id})
        self.assertEqual(response.status_code, 200)

    def test_comment_add(self):
        self.client.login(email='mp@micropyramid.com', password='mp')
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
        self.client.login(email='mp@micropyramid.com', password='mp')
        response = self.client.post(
            '/cases/attachment/add/', {'caseid': self.case.id})
        self.assertEqual(response.status_code, 200)

    def test_attachment_delete(self):
        response = self.client.post(
            '/cases/attachment/remove/', {'attachment_id': self.attachment.id})
        self.assertEqual(response.status_code, 200)

    def test_attachment_deletion(self):
        self.client.login(email='mp@micropyramid.com', password='mp')
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
                        first_name="mpmp",
                        username='mpmp',
                        email='mpmp@micropyramid.com',
                        role="USER",
                        has_sales_access=True)
        self.usermp.set_password('mp')
        self.usermp.save()

        self.usermp1 = User.objects.create(
                        first_name="mpmp1",
                        username='mpmp1',
                        email='mpmp1@micropyramid.com',
                        role="USER")
        self.usermp1.set_password('mp')
        self.usermp1.save()

        self.comment_1 = Comment.objects.create(
            comment='test comment', case=self.case,
            commented_by=self.usermp
        )

        self.account_mp = Account.objects.create(
                            name="mike", email="mike@micropyramid.com", phone="8322855552",
                            billing_address_line="", billing_street="KPHB",
                            billing_city="New York",
                            billing_state="usa", billing_postcode="500073",
                            billing_country="IN",
                            website="www.mike.com", created_by=self.usermp, status="open",
                            industry="SOFTWARE", description="Yes.. Testing Done")
        self.case_user = Case.objects.create(
                            name="mp_case", case_type="Problem", status="New",
                            account=self.account_mp,
                            priority="Low", description="something",
                            created_by=self.usermp, closed_on="2016-05-04")
        self.client.login(email='mpmp@micropyramid.com', password='mp')
        response = self.client.get(reverse('cases:list'))
        self.assertEqual(response.status_code, 200)


        self.address = Address.objects.create(
                        street="5th phase",
                        city="Orlando",
                        state="Florida",
                        postcode=502279, country="AD")

        self.contact_mp = Contact.objects.create(
                            first_name="contact_mp",
                            email="contactmp1@gmail.com",
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
                        first_name="mpmp3",
                        username='mpmp3',
                        email='mpmp3@micropyramid.com',
                        role="USER")
        self.usermp1.set_password('mp')
        self.usermp1.save()
        self.client.login(email='mpmp3@micropyramid.com', password='mp')
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
                        first_name="mpmp6",
                        username='mpmp6',
                        email='mpmp6@micropyramid.com',
                        role="USER")
        self.user.set_password('mp')
        self.user.save()

        self.case_new = Case.objects.create(
            name="robert", case_type="Problem", status="New",
            priority="Low", description="something",
            created_by=self.user, closed_on="2016-05-04")

        self.usermp = User.objects.create(
                        first_name="mpmp7",
                        username='mpmp7',
                        email='mpmp7@micropyramid.com',
                        role="USER")
        self.usermp.set_password('mp')
        self.usermp.save()
        self.client.login(username='mpmp7@micropyramid.com', password='mp')
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


