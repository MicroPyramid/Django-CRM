from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Account, Tags, Email
from cases.models import Case
from common.models import Address, Attachments, Comment, User
from contacts.models import Contact
from leads.models import Lead
from teams.models import Teams


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
            role="USER",
            has_sales_access=True)
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
            first_name="john lead",last_name="doe",email="johnLead@example.com",
            address_line="",street="street name",city="city name",
            state="state",postcode="5079",country="IN",
            website="www.example.com",status="assigned",source="Call",
            opportunity_amount="700",description="lead description",created_by=self.user)
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

        self.contact_user1 = Contact.objects.create(
            first_name="contact",
            email="contactUser1@example.com",
            address=self.address,
            description="contact",
            created_by=self.user1)


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

class test_account_forms(AccountCreateTest, TestCase):

    def test_account_form(self):
        self.client.login(email='janeAccount@example.com', password='password')
        response = self.client.get(reverse('accounts:new_account'))
        self.assertEqual(200, response.status_code)

        response = self.client.get(reverse('accounts:create_mail') + '?account_id={}'.format(self.account.id))
        self.assertEqual(200, response.status_code)

        data = {
            'account_id': self.account.id,
            'message_body': 'message body {{email}}',
            'message_subject':'message subject',
            'recipients':[self.contact.id, self.contact_user1.id],
            'scheduled_date_time': timezone.now(),
        }

        response = self.client.post(reverse('accounts:create_mail'), data)
        self.assertEqual(200, response.status_code)

        data = {
            'account_id': self.account.id,
            'message_body': 'message body {{email}',
            'message_subject':'message subject',
            'recipients':[self.contact.id, self.contact_user1.id],
            'scheduled_date_time': '',
            'scheduled_later': 'true',
        }

        response = self.client.post(reverse('accounts:create_mail'), data)
        self.assertEqual(200, response.status_code)

        data = {
            'account_id': self.account.id,
            'message_body': 'message body {{email}}}',
            'message_subject':'message subject',
            'recipients':[self.contact.id, self.contact_user1.id],
            'scheduled_date_time': timezone.now().strftime('%Y-%m-%d %H:%M'),
        }

        response = self.client.post(reverse('accounts:create_mail'), data)
        self.assertEqual(200, response.status_code)

        data = {
            'account_id': self.account.id,
            'message_body': 'message body {{email}}',
            'message_subject':'message subject',
            'recipients':[self.contact.id, self.contact_user1.id],
            'scheduled_date_time': timezone.now().strftime('%Y-%m-%d %H:%M'),
            'scheduled_later':'true',
        }
        response = self.client.post(reverse('accounts:create_mail'), data)
        self.assertEqual(200, response.status_code)

        data = {
            'account_id': self.account.id,
            'message_body': 'message body {{email}}',
            'message_subject':'message subject',
            'recipients':[self.contact.id, self.contact_user1.id],
            'from_email': 'jane@doe.com',
            'timezone':'UTC',
        }
        response = self.client.post(reverse('accounts:create_mail'), data)
        self.assertEqual(200, response.status_code)

        data = {
            'account_id': 0,
            'message_body': 'message body {{email}}',
            'message_subject':'message subject',
            'recipients':[self.contact.id, self.contact_user1.id],
            'from_email': 'jane@doe.com',
            'timezone':'UTC',
        }
        response = self.client.post(reverse('accounts:create_mail'), data)
        self.assertEqual(200, response.status_code)

        data = {
            'account_id': self.account.id,
            'message_body': 'message body {{email}}',
            'message_subject':'message subject',
            'recipients':[self.contact.id, self.contact_user1.id],
            'from_email': 'jane@doe.com',
            'timezone':'UTC',
            'scheduled_later': 'true',
            'scheduled_date_time': timezone.now().strftime('%Y-%m-%d %H:%M'),
        }
        response = self.client.post(reverse('accounts:create_mail'), data)
        self.assertEqual(200, response.status_code)


class test_account_models(AccountCreateTest, TestCase):

    def test_account_model(self):
        self.account.billing_address_line = 'billing address line'
        self.account.save()
        self.assertEqual('billing address line, street name, city name, state, 1234, United States',
            self.account.get_complete_address())
        self.account.billing_street = 'billing street'
        self.account.save()
        self.assertEqual('billing address line, billing street, city name, state, 1234, United States',
            self.account.get_complete_address())
        self.account.billing_city = None
        self.account.billing_address_line = None
        self.account.billing_street = None
        self.account.save()
        self.assertEqual('state, 1234, United States',
            self.account.get_complete_address())
        self.account.billing_state = None
        self.account.save()
        self.assertEqual('1234, United States',
            self.account.get_complete_address())
        self.account.billing_postcode = None
        self.account.save()
        self.assertEqual('United States',self.account.get_complete_address())
        self.account.billing_country = None
        self.account.save()
        self.assertEqual('', self.account.get_complete_address())
        self.account.billing_city = 'city'
        self.account.save()
        self.assertEqual('city', self.account.get_complete_address())
        self.assertEqual('' ,self.account.contact_values)

class test_account_views_list(AccountCreateTest, TestCase):

    def test_account_views(self):
        self.client.login(email='janeAccount@example.com', password='password')
        response = self.client.get(reverse('accounts:list'))
        self.assertEqual(200, response.status_code)
        response = self.client.get(reverse('accounts:list')+'?tag=1')
        self.assertEqual(200, response.status_code)
        response = self.client.post(reverse('accounts:list'), {'industry': 'industry',
            'tag': [1, ], 'tab_status': 'true'})
        self.assertEqual(200, response.status_code)
        self.tag_name = Tags.objects.create(name='tag name')
        self.team_account = Teams.objects.create(name='dev team')
        self.team_account.users.add(self.user1.id)
        self.client.logout()
        self.client.login(email='johnAccount@example.com', password='password')
        response = self.client.post(reverse('accounts:new_account'), {
            'name': "account", 'email': "johndoe@example.com",
            'phone': "+91-123-456-7894",
            'billing_address_line': "address line",
            'billing_street': "billing street",
            'billing_city': "billing city",
            'billing_state': "state",
            'billing_postcode': "1234",
            'billing_country': "IN",
            'website': "www.example.com",
            'industry': "SOFTWARE", 'description': "Testing",
            'contacts':[self.contact_user1.id,],
            'tags': self.tag_name.name,
            'assigned_to' : [self.user.id, ],
            'teams': [self.team_account.id,]},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        response = self.client.post(reverse('accounts:new_account'), {
            'name': "account", 'email': "johndoe@example.com",
            'phone': "+91-123-456-7894",
            'billing_address_line': "address line",
            'billing_street': "billing street",
            'billing_city': "billing city",
            'billing_state': "state",
            'billing_postcode': "1234",
            'billing_country': "IN",
            'website': "www.example.com",
            'industry': "SOFTWARE", 'description': "Testing",
            'contacts':[self.contact_user1.id,],
            'tags': self.tag_name.name,
            'assigned_to' : [self.user.id, ],
            'teams': [self.team_account.id,]})
        self.assertEqual(response.status_code, 302)

        response = self.client.post(reverse('accounts:new_account'), {
            'name': "account", 'email': "johndoe@example.com",
            'phone': "+91-123-456-7894",
            'billing_address_line': "address line",
            'billing_street': "billing street",
            'billing_city': "billing city",
            'billing_state': "state",
            'billing_postcode': "1234",
            'billing_country': "IN",
            'website': "www.example.com",
            'industry': "SOFTWARE", 'description': "Testing",
            'contacts':[self.contact_user1.id,],
            'tags': self.tag_name.name,
            'assigned_to' : [self.user.id, ],
            'teams': [self.team_account.id,],
            'savenewform': 'true'})
        self.assertEqual(response.status_code, 302)

        response = self.client.post(reverse('accounts:new_account'), {
            'name': "account", 'email': "johndoe@example.com",
            'phone': "+91-123-456-789",
            'billing_address_line': "address line",
            'billing_street': "billing street",
            'billing_city': "billing city",
            'billing_state': "state",
            'billing_postcode': "1234",
            'billing_country': "IN",
            'website': "www.example.com",
            'industry': "SOFTWARE", 'description': "Testing",
            'tags': self.tag_name.name,
            'assigned_to' : [0, ],
            'teams': [0,],},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        self.client.logout()
        self.client.login(email='janeAccount@example.com', password='password')
        response = self.client.get(reverse('accounts:view_account', args=(self.account.id,)))
        self.assertEqual(403, response.status_code)

        self.client.logout()
        self.client.login(email='johnAccount@example.com', password='password')
        response = self.client.post(reverse('accounts:new_account'), {
            'name': "account", 'email': "johndoe@example.com",
            'phone': "+91-123-456-789",
            'billing_address_line': "address line",
            'billing_street': "billing street",
            'billing_city': "billing city",
            'billing_state': "state",
            'billing_postcode': "1234",
            'billing_country': "IN",
            'website': "www.example.com",
            'industry': "SOFTWARE", 'description': "Testing",
            'contacts':[self.contact_user1.id,],
            'tags': self.tag_name.name,
            'assigned_to' : [self.user.id, ],
            'teams': [self.team_account.id,]},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(200, response.status_code)

        self.account_edit = Account.objects.create(
            name="account edit", email="johndoe@example.com", phone="123456789",
            billing_address_line="", billing_street="street name",
            billing_city="city name",
            billing_state="state", billing_postcode="1234",
            billing_country="US",
            website="www.example.como", created_by=self.user, status="open",
            industry="SOFTWARE", description="Testing")
        self.account_by_user = Account.objects.create(
            name="account edit", email="johndoe@example.com", phone="123456789",
            billing_address_line="", billing_street="street name",
            billing_city="city name",
            billing_state="state", billing_postcode="1234",
            billing_country="US",
            website="www.example.como", created_by=self.user, status="open",
            industry="SOFTWARE", description="Testing")
        upload_file = open('static/images/user.png', 'rb')
        response = self.client.post(reverse('accounts:edit_account', args=(self.account_edit.id,)), {
            'name': "account", 'email': "johndoe@example.com",
            'phone': "+91-123-456-7894",
            'billing_address_line': "address line",
            'billing_street': "billing street",
            'billing_city': "billing city",
            'billing_state': "state",
            'billing_postcode': "1234",
            'billing_country': "IN",
            'website': "www.example.com",
            'industry': "SOFTWARE", 'description': "Testing",
            'contacts':[self.contact_user1.id,],
            'tags': self.tag_name.name + ', another tag edit',
            'assigned_to' : [self.user.id, ],
            'teams': [self.team_account.id,],
            'savenewform': 'true',
            'account_attachment': SimpleUploadedFile(
                 upload_file.name, upload_file.read())})
        self.assertEqual(response.status_code, 302)
        response = self.client.post(reverse('accounts:edit_account', args=(self.account_edit.id,)), {
            'name': "account", 'email': "johndoe@example.com",
            'phone': "+91-123-456-7894",
            'billing_address_line': "address line",
            'billing_street': "billing street",
            'billing_city': "billing city",
            'billing_state': "state",
            'billing_postcode': "1234",
            'billing_country': "IN",
            'website': "www.example.com",
            'industry': "SOFTWARE", 'description': "Testing",
            'contacts':[self.contact_user1.id,],
            'tags': self.tag_name.name + ', another tag edit',
            'teams': [self.team_account.id,],
            'savenewform': 'true',},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('accounts:edit_account', args=(self.account_edit.id,)), {
            'name': "account", 'email': "johndoe@example.com",
            'phone': "+91-123-456   ",
            'billing_address_line': "address line",
            'billing_street': "billing street",
            'billing_city': "billing city",
            'billing_state': "state",
            'billing_postcode': "1234",
            'billing_country': "IN",
            'website': "www.example.com",
            'industry': "SOFTWARE", 'description': "Testing",
            'contacts':[self.contact_user1.id,],
            'tags': self.tag_name.name + ', another tag edit',
            'teams': [self.team_account.id,],
            'savenewform': 'true',},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        self.client.logout()
        self.client.login(email='janeAccount@example.com', password='password')
        response = self.client.get(reverse('accounts:edit_account', args=(self.account_by_user.id,)), {})
        self.assertEqual(403, response.status_code)
        self.account_by_user1 = Account.objects.create(
            name="account edit", email="johndoe@example.com", phone="123456789",
            billing_address_line="", billing_street="street name",
            billing_city="city name",
            billing_state="state", billing_postcode="1234",
            billing_country="US",
            website="www.example.como", created_by=self.user1, status="open",
            industry="SOFTWARE", description="Testing")
        response = self.client.get(reverse('accounts:edit_account', args=(self.account_by_user1.id,)), {})
        self.assertEqual(200, response.status_code)
        response = self.client.get(reverse('accounts:remove_account', args=(self.account_by_user.id,)), {})
        self.assertEqual(403, response.status_code)

        response = self.client.post(reverse('accounts:add_comment'), {'accountid':self.account_by_user.id})
        self.assertEqual(200, response.status_code)

        response = self.client.post(reverse('accounts:edit_comment'), {'commentid':self.comment.id})
        self.assertEqual(200, response.status_code)

        self.client.logout()
        self.client.login(email='johnAccount@example.com', password='password')

        response = self.client.post(reverse('accounts:edit_comment'), {'commentid':self.comment.id, 'comment':''})
        self.assertEqual(200, response.status_code)

        self.client.logout()
        self.client.login(email='janeAccount@example.com', password='password')
        response = self.client.post(reverse('accounts:remove_comment'), {'comment_id':self.comment.id, 'comment':''})
        self.assertEqual(200, response.status_code)

        self.client.logout()
        self.client.login(email='johnAccount@example.com', password='password')

        response = self.client.post(reverse('accounts:add_attachment'), {'accountid':self.account.id, 'comment':''})
        self.assertEqual(200, response.status_code)

        email_str = Email.objects.create(message_subject='message subject', message_body='message body')
        self.assertEqual(str(email_str), 'message subject')

        response = self.client.post(reverse('accounts:get_contacts_for_account'), {
            'account_id':self.account.id
        })
        self.assertEqual(200, response.status_code)

        self.account.contacts.add(self.contact.id, self.contact_user1.id)

        response = self.client.post(reverse('accounts:get_contacts_for_account'), {
            'account_id':self.account.id
        })
        self.assertEqual(200, response.status_code)

        response = self.client.get(reverse('accounts:get_contacts_for_account'), {
            'account_id':self.account.id
        })
        self.assertEqual(200, response.status_code)

        response = self.client.post(reverse('accounts:get_email_data_for_account'), {
            'email_account_id':email_str.id
        })
        self.assertEqual(200, response.status_code)

        response = self.client.get(reverse('accounts:get_email_data_for_account'), {
            'email_account_id':email_str.id
        })
        self.assertEqual(200, response.status_code)


class TestAccountUserMentions(AccountCreateTest, TestCase):

    def test_account_views(self):
        self.user_created_by = User.objects.create(
            first_name="jane",
            username='janeAccountCreatedBy',
            email='janeAccountCreatedBy@example.com',
            role="USER",
            has_sales_access=True)
        self.user_created_by.set_password('password')
        self.user_created_by.save()

        self.user_assigned_to = User.objects.create(
            first_name="jane",
            username='janeAccountUserAssigned',
            email='janeAccountUserAssigned@example.com',
            role="USER",
            has_sales_access=True)
        self.user_assigned_to.set_password('password')
        self.user_assigned_to.save()

        self.account = Account.objects.create(
            name="john doe acc created by", email="johndoe@example.com", phone="123456789",
            billing_address_line="", billing_street="street name",
            billing_city="city name",
            billing_state="state", billing_postcode="1234",
            billing_country="US",
            website="www.example.como", created_by=self.user_created_by, status="open",
            industry="SOFTWARE", description="Testing")

        self.account.assigned_to.add(self.user_assigned_to.id)
        self.client.logout()
        self.client.login(email='janeAccountCreatedBy@example.com', password='password')
        response = self.client.get(reverse('accounts:view_account', args=(self.account.id,)))
        self.assertEqual(200, response.status_code)

        self.client.logout()
        self.client.login(email='janeAccountUserAssigned@example.com', password='password')
        response = self.client.get(reverse('accounts:view_account', args=(self.account.id,)))
        self.assertEqual(200, response.status_code)
