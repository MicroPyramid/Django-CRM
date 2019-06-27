from django.test import TestCase, Client
from cases.models import Case
from leads.models import Lead
from common.models import User, Comment, Attachments, APISettings
from accounts.models import Account, Tags
from leads.tasks import *
from leads.forms import *
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.encoding import force_text


class TestLeadModel(object):

    def setUp(self):
        self.client = Client()

        self.user = User.objects.create(
            username='jorge', email='j@mp.com', role="ADMIN")
        self.user.set_password('jorge2293')
        self.user.save()

        self.user1 = User.objects.create(
            first_name="mp",
            username='mp',
            email='mp@micropyramid.com',
            role="USER")
        self.user1.set_password('mp')
        self.user1.save()

        self.user2 = User.objects.create(
            first_name="mp2",
            username='mp2',
            email='mp2@mp.com',
            role="USER")
        self.user2.set_password('mp')
        self.user2.save()

        self.user3 = User.objects.create(
            first_name="mp3",
            username='mp3',
            email='mp3@mp.com',
            role="USER")
        self.user3.set_password('mp')
        self.user3.save()

        self.client.login(username='j@mp.com', password='jorge2293')

        self.account = Account.objects.create(name="account",
                                              email="account@gmail.com",
                                              phone="12345",
                                              billing_address_line="",
                                              billing_street="Arcade enclave colony",
                                              billing_city="NewTown",
                                              billing_state="California",
                                              billing_postcode="5009",
                                              billing_country="AD",
                                              website="account.com",
                                              industry="IT",
                                              description="account",
                                              created_by=self.user)

        self.lead = Lead.objects.create(title="LeadCreation",
                                        first_name="Alisa",
                                        last_name="k",
                                        email="Alisak1993@gmail.com",
                                        address_line="hyd",
                                        street="Arcade enclave colony",
                                        city="NewTown",
                                        state="California",
                                        postcode="5079",
                                        country="AD",
                                        website="www.gmail.com",
                                        status="assigned",
                                        source="call",
                                        opportunity_amount="700",
                                        description="Iam an Lead",
                                        created_by=self.user,
                                        account_name="account",
                                        phone="+91-123-456-7890")

        self.lead1 = Lead.objects.create(title="LeadCreation1", created_by=self.user3)
        self.lead.assigned_to.add(self.user)
        self.lead.assigned_to.add(self.user3)
        self.case = Case.objects.create(
            name="Rose", case_type="Problem",
            status="New",
            account=self.account,
            priority="Low", description="something",
            created_by=self.user, closed_on="2016-05-04")
        self.comment = Comment.objects.create(
            comment='testikd', case=self.case, commented_by=self.user)
        self.comment_mp = Comment.objects.create(
            comment='testikd', case=self.case, commented_by=self.user2)
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

        self.lead_1 = Lead.objects.create(title="LeadCdreation",
                                        first_name="Alisa1",
                                        last_name="k1",
                                        address_line="hyd1",
                                        street="Arcade enc1lave colony",
                                        city="NewTown1",
                                        state="Califor1nia",
                                        postcode="50791",
                                        country="AD",
                                        website="www.gma1il.com",
                                        status="assigned",
                                        source="call",
                                        opportunity_amount="700",
                                        description="Iam an Lead",
                                        created_by=self.user,
                                        phone="+91-123-456-7890")



class LeadsPostrequestTestCase(TestLeadModel, TestCase):

    def test_valid_postrequesttestcase_date(self):
        data = {'title': 'LeadCreation', 'first_name': "micky",
                'last_name': "Alisa", 'email': "Alisamicky1993@gmail.com",
                'account': self.account,
                'address_line': "",
                'street': "Arcade enclave colony",
                'city': "NewTown",
                'state': "California",
                'postcode': "579",
                'country': "AD",
                'website': "www.gmail.com", "status ": "assigned",
                "source": "call",
                'opportunity_amount': "700",
                'description': "Iam an Lead"}
        resp = self.client.post('/leads/create/', data)
        self.assertEqual(resp.status_code, 200)

    def test_leads_list(self):
        self.lead = Lead.objects.all()
        get_name = Lead.objects.get(first_name='Alisa')
        # print(get_name.first_name+get_name.last_name,str(get_name))
        self.assertEqual(get_name.first_name +
                         get_name.last_name, str(get_name))
        response = self.client.get(reverse('leads:list'))
        self.assertEqual(response.status_code, 200)

    def test_leads_list_html(self):
        response = self.client.get(reverse('leads:list'))
        self.assertTemplateUsed(response, 'leads.html')


class LeadsCreateUrlTestCase(TestLeadModel, TestCase):

    def test_leads_create_url(self):
        response = self.client.post('/leads/create/', {
                                    'title': 'LeadCreation',
                                    'first_name': "micky",
                                    'email': "Alisamicky1993@gmail.com",
                                    'account': self.account,
                                    'address_line': "",
                                    'street': "Arcade enclave colony",
                                    'city': "NewTown",
                                    'state': "California",
                                    'postcode': "579",
                                    'country': "AD",
                                    'website': "www.gmail.com",
                                    "status": "assigned",
                                    "source": "call",
                                    'opportunity_amount': "700",
                                    'description': "Iam an Lead",
                                    'created_by': self.user,
                                    'tags':'tag1, tag4, tag5'})
        self.assertEqual(response.status_code, 200)

    def test_leads_create_html(self):
        response = self.client.post('/leads/create/', {
            'title': 'LeadCreation', 'name': "micky",
            'email': "Alisamicky1993@gmail.com", 'account': self.account,
            'address_line': "",
            'street': "Arcade enclave colony", 'city': "NewTown",
            'state': "California", 'postcode': "579", 'country': "AD",
            'website': "www.gmail.com", 'status': "assigned",
            "source": "call", 'opportunity_amount': "700",
            'description': "Iam an Lead", 'created_by': self.user})
        # self.assertTemplateUsed(response, 'create_lead.html')
        self.assertEqual(response.status_code, 200)

    def test_leads_create_with_status_converted(self):
        response = self.client.post('/leads/create/', {
            'title': 'LeadCreation', 'name': "micky",
            'email': "Alisamicky1993@gmail.com", 'account': self.account,
            'address_line': "", 'account_name': 'account1',
            'street': "Arcade enclave colony", 'city': "NewTown",
            'state': "California", 'postcode': "579", 'country': "AD",
            'website': "www.gmail.com", 'status': "converted",
            "source": "call", 'opportunity_amount': "700",
            'description': "Iam an Lead", 'created_by': self.user})
        self.assertEqual(response.status_code, 200)


class LeadsEditUrlTestCase(TestLeadModel, TestCase):

    def test_leads_editurl(self):
        response = self.client.get('/leads/' + str(self.lead.id) + '/edit/')
        self.assertEqual(response.status_code, 200)


class LeadsViewTestCase(TestLeadModel, TestCase):

    def test_leads_view(self):
        Lead.objects.create(title="LeadCreationbylead",
                            first_name="Alisa",
                            last_name="k",
                            email="Alisa@gmail.com",
                            address_line="",
                            street="Arcade enclave colony",
                            city="NewTown",
                            state="California",
                            postcode="579",
                            country="AD",
                            website="www.gmail.com",
                            status='converted',
                            source="call",
                            opportunity_amount="900",
                            description="Iam an Opportunity",
                            created_by=self.user)
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
        data = {'fist_name': "marphy", 'last_name': "racheal",
                'city': "hyd", 'email': "contact@gmail.com",
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
        self.client.login(username='mp@micropyramid.com', password='mp')
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
            'title': "Creation", 'first_name': "marphy", 'last_name': "k",
            'email': "meg@gmail.com", 'account': self.account,
            'address_line': "",
            'street': "Arcade enclave colony", 'city': "NewTown",
            'state': "California",
            'postcode': "579", 'country': "AD",
            'phone': "+917894563452",
            'website': "www.gmail.com", 'status': '',
            'source': "", 'opportunity_amount': "700",
            'description': "Iam an Lead", 'created_by': self.user}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)


class LeadDetailTestCase(TestLeadModel, TestCase):

    def test_lead_detail(self):
        url = '/leads/' + str(self.lead.id) + '/view/'
        response = self.client.get(url, {'status': ''})
        self.assertEqual(response.status_code, 200)


class CommentTestCase(TestLeadModel, TestCase):

    def test_comment_add(self):
        self.client.login(email='mp@micropyramid.com', password='mp')
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
        self.client.login(email='mp@micropyramid.com', password='mp')
        response = self.client.post(
            '/leads/comment/edit/', {'commentid': self.comment.id})
        self.assertEqual(response.status_code, 200)

    def test_comment_delete(self):
        response = self.client.post(
            '/leads/comment/remove/', {'comment_id': self.comment.id})
        self.assertEqual(response.status_code, 200)

    def test_comment_deletion(self):
        self.client.login(email='mp@micropyramid.com', password='mp')
        response = self.client.post(
            '/leads/comment/remove/', {'comment_id': self.comment.id})
        self.assertEqual(response.status_code, 200)


class AttachmentTestCase(TestLeadModel, TestCase):

    def test_attachment_add(self):
        self.client.login(email='mp@micropyramid.com', password='mp')
        response = self.client.post(
            '/leads/attachment/add/', {'leadid': self.lead.id})
        self.assertEqual(response.status_code, 200)

    def test_attachment_delete(self):
        response = self.client.post(
            '/leads/attachment/remove/', {'attachment_id': self.attachment.id})
        self.assertEqual(response.status_code, 200)

    def test_attachment_deletion(self):
        self.client.login(email='mp@micropyramid.com', password='mp')
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
        resp = self.client.post(reverse('leads:list'), {'name': 'trevor',
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
                                    {'first_name': 'm',
                                     'last_name': 's',
                                     'title': 'lead',
                                     'status': 'converted',
                                     'description': 'wgrgre',
                                     'website': 'www.mike.com',
                                     'phone': '+91-123-456-7890',
                                     'email': 'a@gmail.com',
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
                                    {'first_name': 'm',
                                     'last_name': 's',
                                     'title': 'lead',
                                     "created_by": self.user,
                                     'status': 'converted',
                                     'description': 'wgrgre',
                                     'website': 'www.mike.com',
                                     'phone': '+91-123-456-7890',
                                     'email': 'a@gmail.com',
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
            username='gorge', email='g@mp.com')
        self.user.set_password('jorge2293')
        self.user.save()

        self.client.login(username='g@mp.com', password='jorge2293')

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

        self.client.login(username='mp2@mp.com', password='mp')
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
        self.client.login(username='mp2@mp.com', password='mp')
        resp = self.client.get(reverse('leads:view_lead', args=(self.lead.id,)))
        self.assertEqual(resp.status_code, 403)
        self.client.logout()


class TestCommentAddResponse(TestLeadModel, TestCase):

    def test_comment_add_response(self):
        self.client.login(username='mp3@mp.com', password='mp')
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


# class TestAddAttachmentView(TestLeadModel, TestCase):

#     def test_convert_lead_view(self):
#         response = self.client.post(reverse('leads:add_attachment'),{})
#         self.assertEqual(response.status_code, 200)
#         self.assertJSONEqual(
#             str(response.content, encoding='utf8'),
#             {'status': 'success'}
#         )



# class TestAddLeadViewFormError(TestLeadModel, TestCase):

#     def test_add_lead_view_form_error(self):
#         response = self.client.post(reverse('leads:add_lead'),{})
#         # self.assertEqual(response.status_code, 200)
#         print(response.json())
#         print(dir(response))
#         self.assertJSONEqual(
#             str(response.json(), encoding='utf8'),
#             {'status': 'success'}
#         )
