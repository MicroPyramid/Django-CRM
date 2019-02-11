from django.test import TestCase, Client
from cases.models import Case
from leads.models import Lead
from common.models import Address, User, Comment, Attachments
from accounts.models import Account


class TestLeadModel(object):
    def setUp(self):
        self.client = Client()

        self.user = User.objects.create(
            username='uday', email='u@mp.com', role="ADMIN")
        self.user.set_password('uday2293')
        self.user.save()

        self.client.login(username='u@mp.com', password='uday2293')

        self.address = Address.objects.create(street="Gokul enclave colony",
                                              city="Hasthinapuram",
                                              state="Telangana",
                                              postcode="500079",
                                              country="AD")

        self.account = Account.objects.create(name="account",
                                              email="account@gmail.com",
                                              phone="12345",
                                              billing_address=self.address,
                                              shipping_address=self.address,
                                              website="account.com",
                                              industry="IT",
                                              description="account",
                                              created_by=self.user)

        self.lead = Lead.objects.create(title="LeadCreation",
                                        first_name="anjali",
                                        last_name="k",
                                        email="anjalikotha1993@gmail.com",
                                        account=self.account,
                                        address=self.address,
                                        website="www.gmail.com",
                                        status="assigned",
                                        source="Call",
                                        opportunity_amount="700",
                                        description="Iam an Lead",
                                        created_by=self.user)
        self.case = Case.objects.create(
            name="raghu", case_type="Problem", status="New", account=self.account,
            priority="Low", description="something",
            created_by=self.user, closed_on="2016-05-04")
        self.comment = Comment.objects.create(
            comment='testikd', case=self.case, commented_by=self.user)
        self.attachment = Attachments.objects.create(
            attachment='image.png', case=self.case, created_by=self.user, account=self.account)
    # @pytest.mark.django_db(transaction=True)
    # def testaddress_post_object_creation(self):
    #     c = Address.objects.count()
    #     self.assertEqual(c, 1)

    # def test_get_addressobject_with_name(self):
    #     p = Address.objects.get(state="Telangana")
    #     self.assertEqual(p.street, "Gokul enclave colony")

    # def test_lead_object_creation(self):
    #     c = Lead.objects.count()
    #     self.assertEqual(c, 1)

    # def test_get_leadobjects_with_name(self):
    #     p = Lead.objects.get(title="LeadCreation")
    #     self.assertEqual(p.account.name, "account")


class LeadsPostrequestTestCase(TestLeadModel, TestCase):
    def test_valid_postrequesttestcase_date(self):
        data = {'title': 'LeadCreation', 'first_name': "kotha",
                'last_name': "anjali", 'email': "anjalikotha1993@gmail.com",
                'account': self.account, 'address': self.address,
                'website': "www.gmail.com", "status ": "assigned",
                "source": "Call",
                'opportunity_amount': "700",
                'description': "Iam an Lead"}
        resp = self.client.post('/leads/create/', data)
        self.assertEqual(resp.status_code, 200)

    def test_leads_list(self):
        self.lead = Lead.objects.all()
        get_name = Lead.objects.get(first_name='anjali')
        # print(get_name.first_name+get_name.last_name,str(get_name))
        self.assertEqual(get_name.first_name + get_name.last_name, str(get_name))
        response = self.client.get('/leads/list/')
        self.assertEqual(response.status_code, 200)

    def test_leads_list_html(self):
        response = self.client.get('/leads/list/')
        self.assertTemplateUsed(response, 'leads.html')


class LeadsCreateUrlTestCase(TestLeadModel, TestCase):
    def test_leads_create_url(self):
        response = self.client.post('/leads/create/', {
                                    'title': 'LeadCreation',
                                    'first_name': "kotha",
                                    'email': "anjalikotha1993@gmail.com",
                                    'account': self.account,
                                    'address': self.address,
                                    'website': "www.gmail.com",
                                    "status": "assigned",
                                    "source": "Call",
                                    'opportunity_amount': "700",
                                    'description': "Iam an Lead",
                                    'created_by': self.user})
        self.assertEqual(response.status_code, 200)

    def test_leads_create_html(self):
        response = self.client.post('/leads/create/', {
            'title': 'LeadCreation', 'name': "kotha", 'email': "anjalikotha1993@gmail.com", 'account': self.account,
            'address': self.address, 'website': "www.gmail.com", 'status': "assigned",
            "source": "Call", 'opportunity_amount': "700", 'description': "Iam an Lead", 'created_by': self.user})
        self.assertTemplateUsed(response, 'create_lead.html')


class LeadsEditUrlTestCase(TestLeadModel, TestCase):
    def test_leads_editurl(self):
        response = self.client.get('/leads/' + str(self.lead.id) + '/edit/')
        self.assertEqual(response.status_code, 200)


class LeadsViewTestCase(TestLeadModel, TestCase):

    def test_leads_view(self):
        Lead.objects.create(title="LeadCreationbylead",
                            first_name="anjali",
                            last_name="k",
                            email="srilathakotha1993@gmail.com",
                            account=self.account,
                            address=self.address,
                            website="www.gmail.com",
                            status='converted',
                            source="Call",
                            opportunity_amount="900",
                            description="Iam an Opportunity",
                            created_by=self.user)
        response = self.client.get('/leads/' + str(self.lead.id) + '/view/')
        self.assertEqual(response.status_code, 200)


class LeadListTestCase(TestLeadModel, TestCase):

    def test_leads_list(self):
        self.lead = Lead.objects.all()
        response = self.client.get('/leads/list/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'leads.html')

    def test_leads_list_queryset(self):
        self.lead = Lead.objects.all()
        data = {'fist_name': "meghana", 'last_name': "reddy",
                'city': "hyd", 'email': "contact@gmail.com", 'status': "Assigned"}
        response = self.client.post('/leads/list/', data)
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
        self.assertEqual(response['location'], '/leads/list/')

    def test_leads_remove_status(self):
        Lead.objects.filter(id=self.lead.id).delete()
        response = self.client.get('/leads/list/')
        self.assertEqual(response.status_code, 200)


class UpdateLeadTestCase(TestLeadModel, TestCase):

    def test_update_lead(self):
        url = '/leads/' + str(self.lead.id) + '/edit/'
        data = {'title': "Creation", 'first_name': "meghana", 'last_name': "k", 'email': "meg@gmail.com",
                'account': self.account, 'address': self.address.id,'phone':"+917894563452", 'website': "www.gmail.com", 'status': "assigned",
                'source': "", 'opportunity_amount': "700", 'description': "Iam an Lead", 'created_by': self.user}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)


class LeadDetailTestCase(TestLeadModel, TestCase):
    def test_lead_detail(self):
        url = '/leads/' + str(self.lead.id) + '/view/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class CommentTestCase(TestLeadModel, TestCase):
    def test_comment_add(self):
        response = self.client.post(
            '/leads/comment/add/', {'leadid': self.lead.id})
        self.assertEqual(response.status_code, 200)

    def test_comment_edit(self):
        response = self.client.post(
            '/leads/comment/edit/', {'commentid': self.comment.id})
        self.assertEqual(response.status_code, 200)

    def test_comment_delete(self):
        response = self.client.post(
            '/leads/comment/remove/', {'comment_id': self.comment.id})
        self.assertEqual(response.status_code, 200)


class AttachmentTestCase(TestLeadModel, TestCase):
    def test_attachment_add(self):
        response = self.client.post(
            '/leads/attachment/add/', {'leadid': self.lead.id})
        self.assertEqual(response.status_code, 200)

    def test_attachment_delete(self):
        response = self.client.post(
            '/leads/attachment/remove/', {'attachment_id': self.attachment.id})
        self.assertEqual(response.status_code, 200)