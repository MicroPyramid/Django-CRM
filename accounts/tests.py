from django.test import TestCase
from cases.models import Case
from accounts.models import Account, Tags
from common.models import User, Comment, Attachments, Address
from django.urls import reverse
from leads.models import Lead
from contacts.models import Contact
from django.core.files.uploadedfile import SimpleUploadedFile


class AccountCreateTest(object):

    def setUp(self):
        self.user = User.objects.create(
            first_name="johnAccount", username='johnDoeAccount', email='johnAccount@example.com', role='ADMIN')
        self.user.set_password('password')
        self.user.save()

        self.user1 = User.objects.create(
            first_name="jane",
            username='janeAccount',
            email='janeAccount@example.com',
            role="USER")
        self.user1.set_password('password')
        self.user1.save()

        self.account = Account.objects.create(
            name="john doe", email="johndoe@example.com", phone="123456789",
            billing_address_line="", billing_street="street name",
            billing_city="city name",
            billing_state="state", billing_postcode="1234",
            billing_country="US",
            website="www.example.como", created_by=self.user, status="open",
            industry="SOFTWARE", description="Testing")
        self.case = Case.objects.create(
            name="Jane doe", case_type="Problem",
            status="New", account=self.account,
            priority="Low", description="case description",
            created_by=self.user, closed_on="2016-05-04")
        self.comment = Comment.objects.create(
            comment='test comment', case=self.case,
            commented_by=self.user
        )
        self.attachment = Attachments.objects.create(
            attachment='image.png', case=self.case,
            created_by=self.user, account=self.account
        )
        self.client.login(email='johnAccount@example.com', password='password')
        self.lead = Lead.objects.create(title="LeadCreation",
                                        first_name="john lead",
                                        last_name="doe",
                                        email="johnLead@example.com",
                                        address_line="",
                                        street="street name",
                                        city="city name",
                                        state="state",
                                        postcode="5079",
                                        country="IN",
                                        website="www.example.com",
                                        status="assigned",
                                        source="Call",
                                        opportunity_amount="700",
                                        description="lead description",
                                        created_by=self.user)
        self.lead.assigned_to.add(self.user)
        self.address = Address.objects.create(
            street="street number",
            city="city",
            state="state",
            postcode=12346, country="IN")

        self.contact = Contact.objects.create(
            first_name="contact",
            email="contact@example.com",
            phone="12345",
            address=self.address,
            description="contact",
            created_by=self.user)


class AccountsCreateTestCase(AccountCreateTest, TestCase):

    def test_account_create_url(self):
        response = self.client.get('/accounts/create/', {
            'name': "account", 'email': "johndoe@example.com",
            'phone': "1234567891",
            'billing_address_line': "address line",
            'billing_street': "billing street",
            'billing_city': "billing city",
            'billing_state': "state",
            'billing_postcode': "1234",
            'billing_country': "IN",
            'website': "www.example.com",
            'industry': "SOFTWARE", 'description': "Testing"})
        self.assertEqual(response.status_code, 200)

    def test_account_create_html(self):
        response = self.client.get('/accounts/create/', {
            'name': "account", 'email': "accountEmail@example.com", 'phone': "",
            'billing_address_line': "",
            'billing_street': "",
            'billing_city': "city",
            'billing_state': "state",
            'billing_postcode': "1234",
            'billing_country': "IN",
            'website': "www.example.com",
            'industry': "SOFTWARE", 'description': "Testing Done"})
        self.assertTemplateUsed(response, 'create_account.html')


class AccountsListTestCase(AccountCreateTest, TestCase):

    def test_accounts_list(self):
        self.accounts = Account.objects.all()
        response = self.client.get(reverse('accounts:list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts.html')

    def test_accounts_list_queryset(self):
        self.account = Account.objects.all()
        data = {'name': 'name', 'city': 'city',
                'billing_address_line': "billing_address_line",
                'billing_street': "billing_street",
                'billing_city': "billing_city",
                'billing_state': "billing_state",
                'billing_postcode': "billing_postcode",
                'billing_country': "billing_country"}
        response = self.client.post(reverse('accounts:list'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts.html')


class AccountsCountTestCase(AccountCreateTest, TestCase):

    def test_accounts_list_count(self):
        count = Account.objects.all().count()
        self.assertEqual(count, 1)


class AccountsViewTestCase(AccountCreateTest, TestCase):

    def test_accounts_view(self):
        self.accounts = Account.objects.all()
        response = self.client.get(
            '/accounts/' + str(self.account.id) + '/view/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'view_account.html')


class AccountsRemoveTestCase(AccountCreateTest, TestCase):

    def test_accounts_remove(self):
        response = self.client.get(
            '/accounts/' + str(self.account.id) + '/delete/')
        self.assertEqual(response['location'], '/accounts/')

    # def test_accounts_remove_status(self):
    #     Account.objects.filter(id=self.account.id).delete()
    #     response = self.client.get('/accounts/list/')
    #     self.assertEqual(response.status_code, 200)


class AccountsUpdateUrlTestCase(AccountCreateTest, TestCase):

    def test_accounts_update(self):
        response = self.client.get(
            '/accounts/' + str(self.account.id) + '/edit/', {
                'name': "janedoe",
                'email': "janeDoe@example.com", 'phone': "1234567891",
                'billing_address_line': "",
                'billing_street': "street",
                'billing_city': "city",
                'billing_state': "state",
                'billing_postcode': "1234",
                'billing_country': "IN",
                'website': "www.example.com",
                'industry': "SOFTWARE",
                'description': "Test description"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create_account.html')

    def test_accounts_update_post(self):
        response = self.client.post(
            '/accounts/' + str(self.account.id) + '/edit/',
            {
                'name': "janeDoe", 'email': "janeDoe@example.com",
                'phone': "1234567891",
                'billing_address_line': "",
                'billing_street': "Stree",
                'billing_city': "city",
                'billing_state': "state",
                'billing_postcode': "1234",
                'billing_country': "IN",
                'website': "www.example.com",
                'industry': "SOFTWARE", 'description': "Testing Description"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create_account.html')

    def test_accounts_update_status(self):
        response = self.client.get(
            '/accounts/' + str(self.account.id) + '/edit/')
        self.assertEqual(response.status_code, 200)

    def test_accounts_update_html(self):
        response = self.client.get(
            '/accounts/' + str(self.account.id) + '/edit/')
        self.assertTemplateUsed(response, 'create_account.html')


class AccountCreateEmptyFormTestCase(AccountCreateTest, TestCase):

    def test_account_creation_invalid_data(self):
        data = {'name': "", 'email': "", 'phone': "",
                'website': "", 'industry': "",
                'description': "",
                'billing_address_line': "",
                'billing_street': "",
                'billing_city': "city",
                'billing_state': "state",
                'billing_postcode': "1234567897",
                'billing_country': "IN"}
        response = self.client.post('/accounts/create/', data)
        self.assertEqual(response.status_code, 200)


class AccountModelTest(AccountCreateTest, TestCase):

    def test_string_representation(self):
        account = Account(name="Account name", )
        self.assertEqual(str(account), account.name)

    def setUp(self):
        self.user = User.objects.create(
            username='username', email='email@email.com')


class CommentTestCase(AccountCreateTest, TestCase):

    def test_comment_add(self):
        response = self.client.post(
            '/accounts/comment/add/', {'accountid': self.account.id})
        self.assertEqual(response.status_code, 200)

    def test_comment_create(self):
        response = self.client.post(
            '/accounts/comment/add/', {'accountid': self.account.id,
                                       'comment': self.comment.id})
        self.assertEqual(response.status_code, 200)

    def test_comment_creation(self):
        self.client.login(email='mp@micropyramid.com', password='mp')
        response = self.client.post(
            '/accounts/comment/add/', {'accountid': self.account.id,
                                       'comment': 'comment'})
        self.assertEqual(response.status_code, 200)

    def test_comment_edit(self):
        self.client.login(email='mp@micropyramid.com', password='mp')
        response = self.client.post(
            '/accounts/comment/edit/', {'commentid': self.comment.id,
                                        'comment': 'comment'})
        self.assertEqual(response.status_code, 200)

    def test_comment_update(self):
        response = self.client.post(
            '/accounts/comment/edit/', {'commentid': self.comment.id,
                                        'comment': 'comment'})
        self.assertEqual(response.status_code, 200)

    # def test_comment_valid(self):
    #     url = "/accounts/comment/add/"
    #     data = {"comment": "hai", "commented_by": self.user,
    #             "account": self.account}
    #     response = self.client.post(url, data)
    #     print(url,response)
    #     self.assertEqual(response.status_code, 200)

    def test_comment_delete(self):
        response = self.client.post(
            '/accounts/comment/remove/', {'comment_id': self.comment.id})
        self.assertEqual(response.status_code, 200)

    def test_comment_deletion(self):
        self.client.login(email='mp@micropyramid.com', password='mp')
        response = self.client.post(
            '/accounts/comment/remove/', {'comment_id': self.comment.id})
        self.assertEqual(response.status_code, 200)


class AttachmentTestCase(AccountCreateTest, TestCase):

    def test_attachment_add(self):
        self.client.login(email='janeAccount@example.com', password='password')
        response = self.client.post(
            '/accounts/attachment/add/', {'accountid': self.account.id})
        self.assertEqual(response.status_code, 200)

    def test_attachment_valid(self):
        upload_file = open('static/images/user.png', 'rb')
        response = self.client.post(
            '/accounts/attachment/add/', {'accountid': self.account.id,
                                          'attachment': SimpleUploadedFile(
                                              upload_file.name, upload_file.read())})
        self.assertEqual(response.status_code, 200)

    def test_attachment_delete(self):
        response = self.client.post(
            '/accounts/attachment/remove/',
            {'attachment_id': self.attachment.id})
        self.assertEqual(response.status_code, 200)

    def test_attachment_deletion(self):
        self.client.login(email='janeAccount@example.com', password='password')
        response = self.client.post(
            '/accounts/attachment/remove/',
            {'attachment_id': self.attachment.id})
        self.assertEqual(response.status_code, 200)


class TagCreateTest(object):

    def setUp(self):
        self.tag = Tags.objects.create(
            name="tag", slug="tag1")


class TagModelTest(TagCreateTest, TestCase):

    def test_string_representation(self):
        tag = Tags(name="tag", slug="tag1")
        self.assertEqual(str(self.tag.name), tag.name)


class TestCreateLeadPostView(AccountCreateTest, TestCase):

    def test_create_lead_post_status(self):
        upload_file = open('static/images/user.png', 'rb')
        response = self.client.post(reverse(
            'accounts:new_account'), {"name": "janeLead",
                                      "email": "janeLead@example.com",
                                      "phone": "+911234567891",
                                      "billing_address_line": "address line",
                                      "billing_street": "street name",
                                      "billing_city": "city name",
                                      "billing_state": "usa",
                                      "billing_postcode": "1234",
                                      "billing_country": "IN",
                                      "website": "www.example.com",
                                      "created_by": self.user,
                                      "status": "open",
                                      "industry": "SOFTWARE",
                                      "description": "Test description",
                                      "lead": str(self.lead.id),
                                      'contacts': str(self.contact.id),
                                      'tags': 'tag1',
                                      'account_attachment': SimpleUploadedFile(
                                          upload_file.name, upload_file.read())
                                      },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_update_lead_post_status(self):
        upload_file = open('static/images/user.png', 'rb')
        response = self.client.post(reverse(
            'accounts:edit_account', kwargs={'pk': self.account.id}),
            {"name": "janedoeLead",
             "email": "janelead@example.com",
             "phone": "91123456789",
             "billing_address_line": "",
             "billing_street": "stree",
             "billing_city": "city",
             "billing_state": "state name",
             "billing_postcode": "123456",
             "billing_country": "IN",
             "website": "www.example.com",
             "created_by": self.user,
             "status": "open",
             "industry": "SOFTWARE",
             "description": "Testing Description",
             "lead": str(self.lead.id),
             'contacts': str(self.contact.id),
             'tags': 'tag1',
             'account_attachment': SimpleUploadedFile(
                 upload_file.name, upload_file.read())
             })
        self.assertEqual(response.status_code, 200)
