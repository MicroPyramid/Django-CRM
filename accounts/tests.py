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
            first_name="mike", username='mike', email='u@mp.com', role='ADMIN')
        self.user.set_password('mike2293')
        self.user.save()

        self.user1 = User.objects.create(
            first_name="mp",
            username='mp',
            email='mp@micropyramid.com',
            role="USER")
        self.user1.set_password('mp')
        self.user1.save()

        self.account = Account.objects.create(
            name="mike", email="mike@micropyramid.com", phone="8333855552",
            billing_address_line="", billing_street="KPHB",
            billing_city="New York",
            billing_state="usa", billing_postcode="500073",
            billing_country="IN",
            website="www.mike.com", created_by=self.user, status="open",
            industry="SOFTWARE", description="Yes.. Testing Done")
        self.case = Case.objects.create(
            name="raghu", case_type="Problem",
            status="New", account=self.account,
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
        self.client.login(email='u@mp.com', password='mike2293')
        self.lead = Lead.objects.create(title="LeadCreation",
                                        first_name="Alisa",
                                        last_name="k",
                                        email="Alisak1993@gmail.com",
                                        address_line="",
                                        street="Arcade enclave colony",
                                        city="NewTown",
                                        state="California",
                                        postcode="5079",
                                        country="AD",
                                        website="www.gmail.com",
                                        status="assigned",
                                        source="Call",
                                        opportunity_amount="700",
                                        description="Iam an Lead",
                                        created_by=self.user)
        self.lead.assigned_to.add(self.user)
        self.address = Address.objects.create(
            street="5th phase",
            city="Orlando",
            state="Florida",
            postcode=502279, country="AD")

        self.contact = Contact.objects.create(
            first_name="contact",
            email="contact@gmail.com",
            phone="12345",
            address=self.address,
            description="contact",
            created_by=self.user)


class AccountsCreateTestCase(AccountCreateTest, TestCase):

    def test_account_create_url(self):
        response = self.client.get('/accounts/create/', {
            'name': "mike", 'email': "mike@micropyramid.com",
            'phone': "",
            'billing_address_line': "",
            'billing_street': "KPHB",
            'billing_city': "New York",
            'billing_state': "usa",
            'billing_postcode': "500073",
            'billing_country': "IN",
            'website': "www.mike.com",
            'industry': "SOFTWARE", 'description': "Yes.. Testing Done"})
        self.assertEqual(response.status_code, 200)

    def test_account_create_html(self):
        response = self.client.get('/accounts/create/', {
            'name': "mike", 'email': "mike@micropyramid.com", 'phone': "",
            'billing_address_line': "",
            'billing_street': "KPHB",
            'billing_city': "New York",
            'billing_state': "usa",
            'billing_postcode': "500073",
            'billing_country': "IN",
            'website': "www.mike.com",
            'industry': "SOFTWARE", 'description': "Yes.. Testing Done"})
        self.assertTemplateUsed(response, 'create_account.html')


class AccountsListTestCase(AccountCreateTest, TestCase):

    def test_accounts_list(self):
        self.accounts = Account.objects.all()
        response = self.client.get('/accounts/list/')
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
        response = self.client.post('/accounts/list/', data)
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
        self.assertEqual(response['location'], '/accounts/list/')

    # def test_accounts_remove_status(self):
    #     Account.objects.filter(id=self.account.id).delete()
    #     response = self.client.get('/accounts/list/')
    #     self.assertEqual(response.status_code, 200)


class AccountsUpdateUrlTestCase(AccountCreateTest, TestCase):

    def test_accounts_update(self):
        response = self.client.get(
            '/accounts/' + str(self.account.id) + '/edit/', {
                'name': "mike",
                'email': "mike@micropyramid.com", 'phone': "8333855552",
                'billing_address_line': "",
                'billing_street': "KPHB",
                'billing_city': "New York",
                'billing_state': "usa",
                'billing_postcode': "500073",
                'billing_country': "IN",
                'website': "www.mike.com",
                'industry': "SOFTWARE",
                'description': "Yes.. Testing Done"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create_account.html')

    def test_accounts_update_post(self):
        response = self.client.post(
            '/accounts/' + str(self.account.id) + '/edit/',
            {
                'name': "dolly", 'email': "dolly@micropyramid.com",
                'phone': "9555333123",
                'billing_address_line': "",
                'billing_street': "KPHB",
                'billing_city': "New York",
                'billing_state': "usa",
                'billing_postcode': "500073",
                'billing_country': "IN",
                'website': "www.dolly.com",
                'industry': "SOFTWARE", 'description': "Yes.. Testing Done"})
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
                'billing_street': "KPHB",
                'billing_city': "New York",
                'billing_state': "usa",
                'billing_postcode': "500073",
                'billing_country': "IN"}
        response = self.client.post('/accounts/create/', data)
        self.assertEqual(response.status_code, 200)


class AccountModelTest(AccountCreateTest, TestCase):

    def test_string_representation(self):
        account = Account(name="My entry title", )
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
        self.client.login(email='mp@micropyramid.com', password='mp')
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
        self.client.login(email='mp@micropyramid.com', password='mp')
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
            'accounts:new_account'), {"name": "mike",
                                      "email": "mike@micropyramid.com",
                                      "phone": "+91-833-385-5552",
                                      "billing_address_line": "sddsv",
                                      "billing_street": "KPHB",
                                      "billing_city": "New York",
                                      "billing_state": "usa",
                                      "billing_postcode": "500073",
                                      "billing_country": "IN",
                                      "website": "www.mike.com",
                                      "created_by": self.user,
                                      "status": "open",
                                      "industry": "SOFTWARE",
                                      "description": "Yes.. Testing Done",
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
            {"name": "mike",
             "email": "mike@micropyramid.com",
             "phone": "+91-833-385-5552",
             "billing_address_line": "sddsv",
             "billing_street": "KPHB",
             "billing_city": "New York",
             "billing_state": "usa",
             "billing_postcode": "500073",
             "billing_country": "IN",
             "website": "www.mike.com",
             "created_by": self.user,
             "status": "open",
             "industry": "SOFTWARE",
             "description": "Yes.. Testing Done",
             "lead": str(self.lead.id),
             'contacts': str(self.contact.id),
             'tags': 'tag1',
             'account_attachment': SimpleUploadedFile(
                 upload_file.name, upload_file.read())
             })
        self.assertEqual(response.status_code, 302)
