from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django.utils.encoding import force_text

from accounts.models import Account, Tags
from cases.models import Case
from common.models import APISettings, Attachments, Comment, User
from leads.forms import *
from leads.models import Lead
from leads.tasks import *
from teams.models import Teams


class TestLeadModel(object):

    def setUp(self):
        self.client = Client()

        self.user = User.objects.create(
            username='johnLead', email='johnLead@example.com', role="ADMIN")
        self.user.set_password('password')
        self.user.save()

        self.user1 = User.objects.create(
            first_name="janeLead1",
            username='janeLead1',
            email='janeLead1@example.com',
            role="USER")
        self.user1.set_password('password')
        self.user1.save()

        self.user2 = User.objects.create(
            first_name="janeLead2",
            username='janeLead2',
            email='janeLead2@example.com',
            role="USER",
            has_sales_access=True)
        self.user2.set_password('password')
        self.user2.save()

        self.user3 = User.objects.create(
            first_name="janeLead3",
            username='janeLead3',
            email='janeLead3@example.com',
            role="USER",
            has_sales_access=True)
        self.user3.set_password('password')
        self.user3.save()

        self.client.login(username='johnLead@example.com', password='password')

        self.account = Account.objects.create(name="account",
                                              email="account@example.com",
                                              phone="12345",
                                              billing_address_line="",
                                              billing_street="billing street",
                                              billing_city="city of billing",
                                              billing_state="state",
                                              billing_postcode="1234",
                                              billing_country="AD",
                                              website="www.example.com",
                                              industry="IT",
                                              description="account",
                                              created_by=self.user)

        self.lead = Lead.objects.create(title="john lead",
                                        first_name="jane doe",
                                        last_name="doe",
                                        email="janeDoe@example.com",
                                        address_line="address line",
                                        street="address street",
                                        city="city name",
                                        state="state name",
                                        postcode="2134",
                                        country="IN",
                                        website="www.example.com",
                                        status="assigned",
                                        source="call",
                                        opportunity_amount="700",
                                        description="lead description",
                                        created_by=self.user,
                                        account_name="account",
                                        phone="+91-123-456-7890",
                                        is_active=True)

        self.lead1 = Lead.objects.create(
            title="jane doe lead", created_by=self.user3)
        self.lead.assigned_to.add(self.user)
        self.lead.assigned_to.add(self.user2)
        self.lead.assigned_to.add(self.user3)
        self.case = Case.objects.create(
            name="john case", case_type="Problem",
            status="New",
            account=self.account,
            priority="Low", description="description",
            created_by=self.user, closed_on="2016-05-04")
        self.comment = Comment.objects.create(
            comment='comment text', case=self.case, commented_by=self.user)
        self.comment_mp = Comment.objects.create(
            comment='comment body', case=self.case, commented_by=self.user2)
        self.attachment = Attachments.objects.create(
            attachment='image.png',
            case=self.case, created_by=self.user,
            account=self.account, lead=self.lead)
        self.api_seetings = APISettings.objects.create(
            title="api", apikey="api", created_by=self.user)

        self.tag_1 = Tags.objects.create(name='tag1')
        self.tag_2 = Tags.objects.create(name='tag2')
        self.tag_3 = Tags.objects.create(name='tag3')
        self.lead.tags.add(self.tag_1, self.tag_2, self.tag_3)

        self.lead_1 = Lead.objects.create(title="john's lead",
                                          first_name="lead first name",
                                          last_name="lead last name",
                                          address_line="address line",
                                          street=" street",
                                          city="city",
                                          state="state name",
                                          postcode="1234",
                                          country="IN",
                                          website="www.example.com",
                                          status="assigned",
                                          source="call",
                                          opportunity_amount="700",
                                          description="Iam an Lead",
                                          created_by=self.user,
                                          phone="+91-123-456-7890")


class LeadsPostrequestTestCase(TestLeadModel, TestCase):

    def test_valid_postrequesttestcase_date(self):
        data = {'title': 'lead title', 'first_name': "john doe",
                'last_name': "doe", 'email': "johnDoeLeadtitle@example.com",
                'account': self.account,
                'address_line': "",
                'street': "street",
                'city': "city name",
                'state': "state",
                'postcode': "1234",
                'country': "IN",
                'website': "www.example.com", "status ": "assigned",
                "source": "call",
                'opportunity_amount': "700",
                'description': "Description of lead"}
        resp = self.client.post('/leads/create/', data)
        self.assertEqual(resp.status_code, 200)

    def test_leads_list(self):
        self.lead = Lead.objects.all()
        get_name = Lead.objects.get(first_name='jane doe')
        # print(get_name.first_name+get_name.last_name,str(get_name))
        self.assertEqual(get_name.title, str(get_name))
        response = self.client.get(reverse('leads:list'))
        self.assertEqual(response.status_code, 200)

    def test_leads_list_html(self):
        response = self.client.get(reverse('leads:list'))
        self.assertTemplateUsed(response, 'leads.html')


class LeadsCreateUrlTestCase(TestLeadModel, TestCase):

    def test_leads_create_url(self):
        response = self.client.post('/leads/create/', {
                                    'title': 'LeadCreation',
                                    'first_name': "john doe",
                                    'email': "johnDoeLeadCreation@example.com",
                                    'account': self.account,
                                    'address_line': "",
                                    'street': "street",
                                    'city': "new town",
                                    'state': "state",
                                    'postcode': "1234",
                                    'country': "IN",
                                    'website': "www.example.com",
                                    "status": "assigned",
                                    "source": "call",
                                    'opportunity_amount': "700",
                                    'description': "Lead object creaton description",
                                    'created_by': self.user,
                                    'tags': 'tag1, tag4, tag5'})
        self.assertEqual(response.status_code, 200)

    def test_leads_create_html(self):
        response = self.client.post('/leads/create/', {
            'title': 'LeadCreation title', 'name': "john doe",
            'email': "johnDoeLeadCreation@example.com", 'account': self.account,
            'address_line': "",
            'street': "street", 'city': "city name",
            'state': "state name", 'postcode': "1234", 'country': "AD",
            'website': "www.example.com", 'status': "assigned",
            "source": "call", 'opportunity_amount': "700",
            'description': "lead description", 'created_by': self.user})
        # self.assertTemplateUsed(response, 'create_lead.html')
        self.assertEqual(response.status_code, 200)

    def test_leads_create_with_status_converted(self):
        response = self.client.post('/leads/create/', {
            'title': 'LeadCreation title', 'name': "john doe",
            'email': "johnDoeLeadCreation@example.com", 'account': self.account,
            'address_line': "", 'account_name': 'account1',
            'street': "", 'city': "city name",
            'state': "state name", 'postcode': "1234", 'country': "IN",
            'website': "www.example.com", 'status': "converted",
            "source": "call", 'opportunity_amount': "700",
            'description': "Lead description", 'created_by': self.user})
        self.assertEqual(response.status_code, 200)


class LeadsEditUrlTestCase(TestLeadModel, TestCase):

    def test_leads_editurl(self):
        response = self.client.get('/leads/' + str(self.lead.id) + '/edit/')
        self.assertEqual(response.status_code, 200)


class LeadsViewTestCase(TestLeadModel, TestCase):

    def test_leads_view(self):
        response = self.client.get('/leads/' + str(self.lead.id) + '/view/')
        self.assertEqual(response.status_code, 200)


class LeadListTestCase(TestLeadModel, TestCase):

    def test_leads_list(self):
        self.lead = Lead.objects.all()
        response = self.client.get(reverse('leads:list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'leads.html')

    def test_leads_list_queryset(self):
        self.lead = Lead.objects.all()
        data = {'fist_name': "john doe lead", 'last_name': "lead last name",
                'city': "", 'email': "johnlead@example.com",
                'status': "Assigned"}
        response = self.client.post(reverse('leads:list'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'leads.html')


class GetLeadsViewTestCase(TestLeadModel, TestCase):

    def test_get_lead(self):
        url = '/leads/get/list/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class LeadsRemoveTestCase(TestLeadModel, TestCase):

    def test_leads_remove(self):
        response = self.client.get('/leads/' + str(self.lead.id) + '/delete/')
        self.assertEqual(response['location'], '/leads/')

    def test_leads_remove_status(self):
        self.client.login(username='janeLead1@example.com', password='password')
        response = self.client.get(reverse('leads:remove_lead', args=(self.lead.id,)))
        self.assertEqual(response.status_code, 403)
        self.client.logout()

        # Lead.objects.filter(id=self.lead.id).delete()
        response = self.client.get(reverse('leads:remove_lead', args=(self.lead.id,)))
        self.assertEqual(response.status_code, 302)

class UpdateLeadTestCase(TestLeadModel, TestCase):

    def test_update_lead(self):
        url = '/leads/' + str(self.lead.id) + '/edit/'
        data = {
            'title': "Creation", 'first_name': "update first", 'last_name': "update last name",
            'email': "janeDoeLead@example.com", 'account': self.account,
            'address_line': "",
            'street': "street", 'city': "city name",
            'state': "state name",
            'postcode': "213", 'country': "IN",
            'phone': "+911234567892",
            'website': "www.example.com", 'status': '',
            'source': "", 'opportunity_amount': "700",
            'description': "lead description", 'created_by': self.user}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)


class LeadDetailTestCase(TestLeadModel, TestCase):

    def test_lead_detail(self):
        url = '/leads/' + str(self.lead.id) + '/view/'
        response = self.client.get(url, {'status': ''})
        self.assertEqual(response.status_code, 200)


class CommentTestCase(TestLeadModel, TestCase):

    def test_comment_add(self):
        self.client.login(email='janeLead1@example.com', password='password')
        response = self.client.post(
            '/leads/comment/add/', {'leadid': self.lead.id})
        self.assertEqual(response.status_code, 200)


    def test_comment_create(self):
        response = self.client.post(
            '/leads/comment/add/', {'leadid': self.lead.id, 'comment': "comment"})
        self.assertEqual(response.status_code, 200)

    def test_comment_edit(self):
        response = self.client.post(
            '/leads/comment/edit/', {'commentid': self.comment.id, 'comment': "comment"})
        self.assertEqual(response.status_code, 200)

    def test_comment_update(self):
        self.client.login(email='janeLead1@example.com', password='password')
        response = self.client.post(
            '/leads/comment/edit/', {'commentid': self.comment.id})
        self.assertEqual(response.status_code, 200)

    def test_comment_delete(self):
        response = self.client.post(
            '/leads/comment/remove/', {'comment_id': self.comment.id})
        self.assertEqual(response.status_code, 200)

    def test_comment_deletion(self):
        self.client.login(email='janeLead1@example.com', password='password')
        response = self.client.post(
            '/leads/comment/remove/', {'comment_id': self.comment.id})
        self.assertEqual(response.status_code, 200)


class AttachmentTestCase(TestLeadModel, TestCase):

    def test_attachment_add(self):
        self.client.login(email='janeLead1@example.com', password='password')
        response = self.client.post(
            '/leads/attachment/add/', {'leadid': self.lead.id})
        self.assertEqual(response.status_code, 200)

    def test_attachment_delete(self):
        response = self.client.post(
            '/leads/attachment/remove/', {'attachment_id': self.attachment.id})
        self.assertEqual(response.status_code, 200)

    def test_attachment_deletion(self):
        self.client.login(email='janeLead1@example.com', password='password')
        response = self.client.post(
            '/leads/attachment/remove/', {'attachment_id': self.attachment.id})
        self.assertEqual(response.status_code, 200)

    def test_attachment_valid(self):
        upload_file = open('static/images/user.png', 'rb')
        response = self.client.post(
            '/leads/attachment/add/', {'leadid': self.lead.id,
                                       'attachment': SimpleUploadedFile(
                                           upload_file.name, upload_file.read())})
        self.assertEqual(response.status_code, 200)


class TestTemplates(TestLeadModel, TestCase):

    def test_lead_list_view(self):
        resp = self.client.post(reverse('leads:list'), {'name': 'search filter',
                                                 'tag': "123",
                                                 'source': "call",
                                                 'assigned_to': '1',
                                                 'tab_status': 'Open'})
        self.assertEqual(resp.status_code, 200)
        # print(resp.name)
        # self.assertTrue(resp.name)

    # def test_lead_from_site(self):
    #     resp = self.client.get()


class TestConvertLeadView(TestLeadModel, TestCase):

    def test_get_fun(self):
        resp = self.client.get('/leads/' + str(self.lead.id) + '/convert/')
        self.assertEqual(resp.status_code, 302)


class TestCreateLeadPostView(TestLeadModel, TestCase):

    def test_create_lead_post_status(self):
        upload_file = open('static/images/user.png', 'rb')
        response = self.client.post('/leads/create/',
                                    {'first_name': 'jane doe',
                                     'last_name': 'doe lead',
                                     'title': 'lead',
                                     'status': 'converted',
                                     'description': 'lead descriptoin',
                                     'website': 'www.example.com',
                                     'phone': '+91-123-456-7890',
                                     'email': 'janedoeLead@example.com',
                                     'account_name': 'account',
                                     'address_line': self.lead.address_line,
                                     'street': self.lead.street,
                                     'city': self.lead.city,
                                     'state': self.lead.state,
                                     'postcode': self.lead.postcode,
                                     'country': self.lead.country,
                                     'lead_attachment': SimpleUploadedFile(
                                         upload_file.name, upload_file.read()),
                                     'assigned_to': str(self.user.id),
                                     'tags': 'tag'
                                     })
        self.assertEqual(response.status_code, 200)

    def test_create_lead_get_request(self):
        response = self.client.get(reverse('leads:add_lead'))
        self.assertEqual(response.status_code, 200)

    def test_update_lead_post_status(self):
        upload_file = open('static/images/user.png', 'rb')
        response = self.client.post('/leads/' + str(self.lead.id) + '/edit/',
                                    {'first_name': 'jane doe lead',
                                     'last_name': 'lead last name',
                                     'title': 'jane doe',
                                     "created_by": self.user,
                                     'status': 'converted',
                                     'description': 'description',
                                     'website': 'www.example.com',
                                     'phone': '+91-123-456-7890',
                                     'email': 'janedoeLead@example.com',
                                     'account_name': 'account',
                                     'address_line': self.lead.address_line,
                                     'street': self.lead.street,
                                     'city': self.lead.city,
                                     'state': self.lead.state,
                                     'postcode': self.lead.postcode,
                                     'country': self.lead.country,
                                     'lead_attachment': SimpleUploadedFile(
                                         upload_file.name, upload_file.read()),
                                     'assigned_to': str(self.user.id),
                                     'tags': 'tag'
                                     })
        self.assertEqual(response.status_code, 200)

    def test_lead_convert(self):
        response = self.client.get('/leads/' + str(self.lead.id) + '/convert/')
        self.assertEqual(response.status_code, 302)


class TestLeadDetailView(TestLeadModel, TestCase):

    def test_lead_detail_view(self):
        response = self.client.get(
            reverse('leads:view_lead', kwargs={'pk': self.lead.id}))
        self.assertEqual(response.status_code, 200)


class TestLeadFromSite(TestLeadModel, TestCase):

    def create_lead_from_site(self):
        response = self.client.post(
            '/leads/create/from-site/', {'apikey': self.api_seetings.apikey})
        self.assertEqual(response.status_code, 200)


class TestLeadListView(TestCase):

    def setUp(self):
        self.client = Client()

        self.user = User.objects.create(
            username='johnDoeG@lead.com', email='johnDoeG@lead.com', has_sales_access=True)
        self.user.set_password('password')
        self.user.save()

        self.client.login(username='johnDoeG@lead.com', password='password')

    def test_lead_list_view(self):
        response = self.client.get(reverse('leads:list'))
        self.assertEqual(response.status_code, 200)

        # response = self.client.post('/leads/create/',{})
        # self.assertEqual(force_text(response.content), {"errors": {"title": ["This field is required."]}, "error": True})


class TestUpdateLeadView(TestLeadModel, TestCase):

    def test_lead_update_view(self):
        response = self.client.post(reverse('leads:edit_lead', args=(self.lead.id,)),
                        {'status': 'converted', 'country':'AD', 'title':'update_title'})
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('leads:edit_lead', args=(self.lead.id,)),
                        {'status': 'assigned', 'country':'AD', 'title':'update_title'})
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('leads:edit_lead', args=(self.lead.id,)),
                        {'status': 'assigned', 'country':'AD', 'title':'update_title',
                        'tags':'tag3, tag4'})
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('leads:edit_lead', args=(self.lead.id,)),
                        {'status': 'assigned', 'country':'AD', 'title':'update_title',
                        'assigned_to':str(self.user.id)})
        self.assertEqual(response.status_code, 200)

        self.client.login(username='janeLead2@example.com', password='password')
        response = self.client.get(reverse('leads:edit_lead', args=(self.lead.id,)),
                        {'status': 'assigned', 'country':'AD', 'title':'update_title'})
        self.assertEqual(response.status_code, 403)
        self.client.logout()


class TestConvertLeadView1(TestLeadModel, TestCase):

    def test_convert_lead_view(self):
        resp = self.client.get('/leads/' + str(self.lead.id) + '/convert/')
        self.assertEqual(resp.status_code, 302)


class TestLeadDetailView1(TestLeadModel, TestCase):

    def test_lead_detail_view(self):
        self.client.login(username='janeLead2@example.com', password='password')
        resp = self.client.get(reverse('leads:view_lead', args=(self.lead.id,)))
        self.assertEqual(resp.status_code, 200)
        self.client.logout()


class TestCommentAddResponse(TestLeadModel, TestCase):

    def test_comment_add_response(self):
        self.client.login(username='janeLead3@example.com', password='password')
        response = self.client.post(
            '/leads/comment/add/', {'leadid': self.lead.id})
        self.assertJSONEqual(force_text(response.content), {"error": ["This field is required."]})

        self.comment_mp = Comment.objects.create(
            comment='testikd', case=self.case, commented_by=self.user3)
        response = self.client.post(
            '/leads/comment/edit/', {'commentid': self.comment_mp.id})
        self.assertJSONEqual(force_text(response.content), {"error": ["This field is required."]})

        response = self.client.post(
            '/leads/attachment/add/', {'leadid': self.lead1.id})
        self.assertJSONEqual(force_text(response.content), {"error": ["This field is required."]})


    def test_file_upload_for_leads(self):
        self.client.logout()
        self.client.login(email='johnLead@example.com', password="password")

        file_content = [
            'title,first name,last name,website,phone,email,address\n',
            'lead1,john,doe,www.example.com,911234567890,user1@email.com,address for lead1\n',
            'lead2,jane,doe,www.website.com,911234567891,user2@email.com,address for lead2\n',
            'lead3,joe,doe,www.test.com,911234567892,user3@email.com,address for lead3\n',
            'lead4,john,doe,www.sample.com,911234567893,user4@email.com,address for lead4\n',
        ]
        file_content = bytes(''.join(file_content), 'utf-8')
        data = {'leads_file': SimpleUploadedFile('file name', file_content)}
        response = self.client.post(reverse('leads:upload_lead_csv_file'), data)
        self.assertEqual(201, response.status_code)

        file_content_missing_headers = [
            ',first name,last name,website,phone,,address\n',
            'lead1,john,doe,www.example.com,911234567890,user1@email.com,address for lead1\n',
            'lead2,jane,doe,www.website.com,911234567891,user2@email.com,address for lead2\n',
            'lead3,joe,doe,www.test.com,911234567892,user3@email.com,address for lead3\n',
            'lead4,john,doe,www.sample.com,911234567893,user4@email.com,address for lead4\n',
        ]
        file_content_missing_headers = bytes(''.join(file_content_missing_headers), 'utf-8')
        data = {'leads_file': SimpleUploadedFile('file name', file_content_missing_headers)}
        response = self.client.post(reverse('leads:upload_lead_csv_file'), data)

        # for invalid lead titles
        file_content = [
            'title,first name,last name,website,phone,email,address\n',
            ',john,doe,www.example.com,911234567890,user1@email.com,address for lead1\n',
            ',jane,doe,www.website.com,911234567891,user2@email.com,address for lead2\n',
            ',joe,doe,www.test.com,911234567892,user3@email.com,address for lead3\n',
            ',john,doe,www.sample.com,911234567893,user4@email.com,address for lead4\n',
        ]
        file_content = bytes(''.join(file_content), 'utf-8')
        data = {'leads_file': SimpleUploadedFile('file name', file_content)}
        response = self.client.post(reverse('leads:upload_lead_csv_file'), data)
        self.assertEqual(200, response.status_code)

        # for invalid email
        file_content = [
            'title,first name,last name,website,phone,email,address\n',
            'lead1,john,doe,www.example.com,911234567890,user1@email.com,address for lead1\n',
            'lead2,jane,doe,www.website.com,911234567891,user2@email.com,address for lead2\n',
            'lead3,joe,doe,www.test.com,911234567892,useremail.com,address for lead3\n',
            'lead4,john,doe,www.sample.com,911234567893,user4@email,address for lead4\n',
        ]
        file_content = bytes(''.join(file_content), 'utf-8')
        data = {'leads_file': SimpleUploadedFile('file name', file_content)}
        response = self.client.post(reverse('leads:upload_lead_csv_file'), data)
        self.assertEqual(201, response.status_code)

        # for invalid file type
        data = {'leads_file': b''}
        response = self.client.post(reverse('leads:upload_lead_csv_file'), data)
        self.assertEqual(200, response.status_code)

        file_content_missing_headers = [
            ',first name,last name,website,phone,,address\n',
            'lead1,john,doe,www.example.com,911234567890,user1@email,address for lead1\n',
            'lead2,jane,doe,www.website.com,911234567891,user2@email.com,address for lead2\n',
            'lead3,joe,doe,www.test.com,911234567892,user3@email.com,address for lead3\n',
            'lead4,john,doe,www.sample.com,911234567893,user4@email,address for lead4\n',
        ]
        file_content_missing_headers = bytes(''.join(file_content_missing_headers), 'utf-8')
        data = {'leads_file': SimpleUploadedFile('file name', file_content_missing_headers)}
        response = self.client.post(reverse('leads:upload_lead_csv_file'), data)

        response = self.client.post(reverse('leads:list') + '?tag=0', {'city': 'city'})
        self.assertEqual(response.status_code, 200)

        self.teams_leads = Teams.objects.create(name='teams leads')
        self.teams_leads.users.add(self.user1)
        response = self.client.post(reverse('leads:add_lead'), {'title': 'new lead title', 'teams': [self.teams_leads.id, ],
            'savenewform':'true'})
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('leads:add_lead'), {'title': ''})
        self.assertEqual(response.status_code, 200)

        self.client.logout()
        self.client.login(email='janeLead3@example.com', password="password")

        response = self.client.get(reverse('leads:view_lead', args=(self.lead_1.id,)))
        self.assertEqual(response.status_code, 403)

        response = self.client.get(reverse('leads:view_lead', args=(self.lead1.id,)))
        self.assertEqual(response.status_code, 200)

        self.client.logout()
        self.client.login(email='janeLead2@example.com', password="password")
        self.lead_user = Lead.objects.create(title="jane doe lead 2", created_by=self.user2)
        response = self.client.get(reverse('leads:view_lead', args=(self.lead_user.id,)))
        self.assertEqual(response.status_code, 200)

        self.client.logout()
        self.client.login(email='johnLead@example.com', password="password")
        response = self.client.get(reverse('leads:edit_lead', args=(self.lead_1.id,)) + '?status=converted')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('leads:edit_lead', args=(self.lead_1.id,)) + '?status=c')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('leads:edit_lead', args=(self.lead_1.id,)) + '?status=converted')
        self.assertEqual(response.status_code, 200)

        self.teams_leads.users.add(self.user3)
        data = {
            'title': self.lead_1.title,
            'teams': [self.teams_leads.id, ],
            'status':'converted',
            'account_name': 'lead_conversion',
            'email':'account@lead.com'
        }
        comment = Comment.objects.create(comment='comment text lead', lead=self.lead_1, commented_by=self.user)
        response = self.client.post(reverse('leads:edit_lead', args=(self.lead_1.id,)) + '?status=converted', data)
        self.assertEqual(response.status_code, 200)

        self.client.logout()
        self.client.login(email='janeLead3@example.com', password="password")

        response = self.client.get(reverse('leads:remove_lead', args=(self.lead_1.id,)))
        self.assertEqual(response.status_code, 403)

        self.client.logout()
        self.client.login(email='johnLead@example.com', password="password")
        self.lead.email = None
        self.lead.save()
        response = self.client.get(reverse('leads:leads_convert', args=(self.lead.id,)) + '?status=converted')
        self.assertEqual(response.status_code, 302)

        self.tag_for_lead = Tags.objects.create(name='tag for lead')
        data = {
            'tags':'tag1 lead,tag2 lead,tag for lead'
        }
        response = self.client.post(reverse('leads:update_lead_tags', args=(self.lead.id,)), data)
        self.assertEqual(response.status_code, 302)

        self.client.logout()
        self.client.login(email='janeLead3@example.com', password="password")
        response = self.client.post(reverse('leads:update_lead_tags', args=(self.lead.id,)), data)
        self.assertEqual(response.status_code, 403)

        self.client.logout()
        self.client.login(email='johnLead@example.com', password="password")
        data = {
            'lead': self.lead.id,
            'tag': self.tag_for_lead.id
        }
        response = self.client.post(reverse('leads:remove_lead_tag'), data)
        self.assertEqual(response.status_code, 200)

        self.client.logout()
        self.client.login(email='janeLead3@example.com', password="password")
        response = self.client.post(reverse('leads:remove_lead_tag'), data)
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('leads:sample_lead_file'))
        sample_data = [
        'title,first name,last name,website,phone,email,address\n',
        'lead1,john,doe,www.example.com,+91-123-456-7890,user1@email.com,address for lead1\n',
        'lead2,jane,doe,www.website.com,+91-123-456-7891,user2@email.com,address for lead2\n',
        'lead3,joe,doe,www.test.com,+91-123-456-7892,user3@email.com,address for lead3\n',
        'lead4,john,doe,www.sample.com,+91-123-456-7893,user4@email.com,address for lead4\n',
        ]
        content = bytes(''.join(sample_data), 'utf-8')
        self.assertEqual(response.content, content)