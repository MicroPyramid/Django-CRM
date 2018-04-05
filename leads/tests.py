from django.test import TestCase, Client
from leads.models import Lead
from common.models import Address, User
from accounts.models import Account


class TestLeadModel(object):
    def setUp(self):
        self.client = Client()

        self.user = User.objects.create(username='uday', email='u@mp.com')
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
                                                  billing_address=Address.objects.get(pk=1),
                                                  shipping_address=Address.objects.get(pk=1),
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

    def testaddress_post_object_creation(self):
        c = Address.objects.count()
        self.assertEqual(c, 1)

    def test_get_addressobject_with_name(self):
        p = Address.objects.get(state="Telangana")
        self.assertEqual(p.street, "Gokul enclave colony")

    def test_lead_object_creation(self):
        c = Lead.objects.count()
        self.assertEqual(c, 1)

    def test_get_leadobjects_with_name(self):
        p = Lead.objects.get(title="LeadCreation")
        self.assertEqual(p.account.name, "account")


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
        response = self.client.get('/leads/list/')
        self.assertEqual(response.status_code, 200)

    def test_leads_list_html(self):
        response = self.client.get('/leads/list/')
        self.assertTemplateUsed(response, 'leads/leads.html')


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
        self.assertTemplateUsed(response, 'leads/create_lead.html')


class LeadsEditUrlTestCase(TestLeadModel, TestCase):
    def test_lead_editurl(self):
        response = self.client.get('/leads/1/edit/', {
                                   'title': 'LeadCreation',
                                   'first_name': "kotha",
                                   'email': "fathimakotha1993@gmail.com",
                                   'account': self.account,
                                   'address': self.address,
                                   'website': "www.gmail.com",
                                   "status ": "assigned",
                                   "source": "Call",
                                   'opportunity_amount': "700",
                                   'description': "Iam an Lead",
                                   'created_by': self.user})
        self.assertEqual(response.status_code, 200)


class LeadsUpdateTestCase(TestLeadModel, TestCase):
    def test_leadsedit_update_status(self):
        response = self.client.get('/leads/1/edit/')
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
        self.lead = Lead.objects.all()
        response = self.client.get('/leads/1/view/')
        self.assertEqual(response.status_code, 200)


class LeadsRemoveTestCase(TestLeadModel, TestCase):

    def test_leads_remove(self):
        self.lead = Lead.objects.all()
        response = self.client.get('/leads/1/delete/')
        self.assertEqual(response['location'], '/leads/list/')

    def test_leads_remove_status(self):
        Lead.objects.filter(id=self.lead.id).delete()
        response = self.client.get('/leads/list/')
        self.assertEqual(response.status_code, 200)
