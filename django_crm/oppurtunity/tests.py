from django.test import TestCase
from .models import Opportunity
from ..djcrm.models import Country, Address
from ..accounts.models import LeadAccount
from ..contacts.models import Contact
from django.contrib.auth.models import User


# Create your tests here.


class OpportunityModel(object):
    def setUp(self):
        self.country = Country.objects.create(
            iso_3166_1_a2="jh", iso_3166_1_a3="nh",
            iso_3166_1_numeric="gt", printable_name="America",
                                              name="India",
                                              is_shipping_country="True")
        self.address = Address.objects.create(
            street="kphb", city="hyderabad", postcode="584",
            country=Country.objects.get(pk=1))
        self.account = LeadAccount.objects.create(
            name="uday", email="uday@gmail.com",
            phone="58964", billing_address=self.address,
            shipping_address=self.address,
            website="hello.com",
            account_type="initial",
            sis_code="98745", industry="sw", description="bgyyr")
        self.contacts = Contact.objects.create(
            name="navi",
            email="navi@gmail.com", phone="8547",
            account=self.account,
            description="defyj",
            address=self.address)
        self.opportunity = Opportunity.objects.create(
            name="madhurima", amount="478",
            stage="negotiation/review", lead_source="Call", probability="58",
            close_date="2016-05-04",
            description="hgfdxc")
        self.user = User.objects.create(username='madhurima')
        self.user.set_password('madhu123')
        self.user.save()
        self.client.login(username='madhurima', password='madhu123')


class OpportunityCreateTestCase(OpportunityModel, TestCase):
    def test_opportunity_create(self):
        response = self.client.get('/oppurtunities/create/', {
            'name': "madhurima", 'amount': "478",
            'stage': "NEGOTIATION/REVIEW",
            'lead_source': "Call", 'probability': "58",
            'close_date': "2016-05-04", 'description': "hgfdxc"})
        self.assertEqual(response.status_code, 200)


class opportunityCreateTestCase(OpportunityModel, TestCase):
    def test_create_opportunity(self):
        self.assertEqual(self.opportunity.id, 1)

    def test_view_opportunity(self):
        self.oppurtunity = Opportunity.objects.all()
        response = self.client.get('/oppurtunities/1/view/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['opp'].id, self.opportunity.id)

    def test_del_opportunity(self):
        response = self.client.get('/oppurtunities/1/delete/')
        self.assertEqual(response['location'], '/oppurtunities/list/')

    def test_opportunity_delete(self):
        Opportunity.objects.filter(id=self.account.id).delete()
        response = self.client.get('/oppurtunities/list/')
        self.assertEqual(response.status_code, 200)


class EditOpportunityTestCase(OpportunityModel, TestCase):
    def test_edit(self):
        response = self.client.get('/oppurtunities/1/edit/')
        self.assertEqual(response.status_code, 200)

    def test_edit_opportunity(self):
        response = self.client.get('/oppurtunities/1/edit/', {
            'name': "madhurima", 'amount': "478",
            'stage': "negotiation/review",
            'lead_source': "Call", 'probability': "58",
            'close_date': "2016-05-04", 'description': "hgfdxc"})
        self.assertEqual(response.status_code, 200)
