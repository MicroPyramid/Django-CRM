from django.test import TestCase
from opportunity.models import Opportunity
from common.models import Address
from accounts.models import Account
from contacts.models import Contact
from common.models import User,Comment,Attachments
from cases.models import Case
from django.utils import timezone


# Create your tests here.


class OpportunityModel(object):
    def setUp(self):
        self.address = Address.objects.create(
            street="kphb", city="hyderabad", postcode="584",
            country='IN')

        self.user = User.objects.create(first_name="madhurima", username='madhurima', email="m@mp.com", role="ADMIN")
        self.user.set_password('madhu123')
        self.user.save()

        self.client.login(email='m@mp.com', password='madhu123')

        self.account = Account.objects.create(
            name="uday", email="uday@gmail.com",
            phone="58964", billing_address=self.address,
            shipping_address=self.address,
            website="hello.com", industry="sw",
            description="bgyyr", created_by=self.user)

        self.contacts = Contact.objects.create(
            first_name="navi",
            last_name="s",
            email="navi@gmail.com", phone="8547",
            account=self.account,
            description="defyj",
            address=self.address,
            created_by=self.user)

        self.opportunity = Opportunity.objects.create(
            name="madhurima", amount="478",
            stage="negotiation/review", lead_source="Call", probability="58",
            closed_on="2016-05-04",
            description="hgfdxc",
            created_by=self.user)
        self.case = Case.objects.create(
            name="raghu", case_type="Problem", status="New", account=self.account,
            priority="Low", description="something",
            created_by=self.user, closed_on="2016-05-04")
        self.comment = Comment.objects.create(
            comment='testikd', case=self.case, commented_by=self.user)
        self.attachment = Attachments.objects.create(
            attachment='image.png', case=self.case, created_by=self.user, account=self.account)


class OpportunityCreateTestCase(OpportunityModel, TestCase):
    def test_opportunity_create(self):
        response = self.client.get('/opportunities/create/', {
            'name': "madhurima", 'amount': "478",
            'stage': "NEGOTIATION/REVIEW",
            'lead_source': "Call", 'probability': "58",
            'closed_on': "2016-05-04", 'description': "hgfdxc"})
        self.assertEqual(response.status_code, 200)

    def test_opportunity_create_post(self):
        url = '/opportunities/create/'
        data = {'name':"meghana",'amount':"500",'stage':"CLOSED WON",}
        response =self.client.post(url,data)
        self.assertEqual(response.status_code,302)

    def test_opportunity_invalid(self):
        url = '/opportunities/create/'
        data = {'name':"meghana",'amount':"",'stage':""}
        response =self.client.post(url,data)
        self.assertEqual(response.status_code,200)

class opportunityCreateTestCase(OpportunityModel, TestCase):

    def test_view_opportunity(self):
        response = self.client.get('/opportunities/'+ str(self.opportunity.id) +'/view/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['opportunity_record'].id, self.opportunity.id)

    def test_del_opportunity_url(self):
        response = self.client.get('/opportunities/'+ str(self.opportunity.id) +'/delete/')
        self.assertEqual(response['location'], '/opportunities/list/')

    def test_opportunity_delete(self):
        Opportunity.objects.filter(id=self.account.id).delete()
        response = self.client.get('/opportunities/list/')
        self.assertEqual(response.status_code, 200)

class EditOpportunityTestCase(OpportunityModel, TestCase):
    def test_edit_url(self):
        response = self.client.get('/opportunities/'+ str(self.opportunity.id) +'/edit/')
        self.assertEqual(response.status_code, 200)

    def test_edit_opportunity(self):
        response = self.client.get('/opportunities/'+ str(self.opportunity.id) +'/edit/', {
            'name': "madhurima", 'amount': "478",
            'stage': "negotiation/review",
            'lead_source': "Call", 'probability': "58",
            'closed_on': "2016-05-04", 'description': "hgfdxc"})
        self.assertEqual(response.status_code, 200)

    def test_update_opportunity(self):
        url = '/opportunities/' + str(self.opportunity.id) + '/edit/'
        data = {'name': "madhurima", 'amount': "478",'stage': "QUALIFICATION",'probability': "58",'closed_on': "2016-05-04", 'description': "hgfdxc"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

    def test_update_opportunity_invalid(self):
        url = '/opportunities/' + str(self.opportunity.id) + '/edit/'
        data = {'name':"", 'amount': "478",'stage': "",'probability': "58",'closed_on': "2016-05-04", 'description': "hgfdxc"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)

class OpportunityListView(OpportunityModel,TestCase):
    def test_opportunity_list(self):
        self.opportunity = Opportunity.objects.all()
        response = self.client.get('/opportunities/list/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'opportunity.html')

    def test_opportunity_list_queryset(self):
        self.account = Account.objects.all()
        data = {'name': 'madhurima','stage': 'city',
                'lead_source': 'Call', 'accounts':self.account}
        response = self.client.post('/opportunities/list/', data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'opportunity.html')

class ContactGetViewTestCase(OpportunityModel,TestCase):
    def test_get_contact(self):
        url = '/opportunities/contacts/'
        response = self.client.get(url)
        self.assertEqual(response.status_code,200)

class CommentTestCase(OpportunityModel, TestCase):
    def test_comment_add(self):
        response = self.client.post(
            '/opportunities/comment/add/', {'opportunityid': self.opportunity.id})
        self.assertEqual(response.status_code, 200)

    def test_comment_edit(self):
        response = self.client.post(
            '/opportunities/comment/edit/', {'commentid': self.comment.id})
        self.assertEqual(response.status_code, 200)

    def test_comment_delete(self):
        response = self.client.post(
            '/opportunities/comment/remove/', {'comment_id': self.comment.id})
        self.assertEqual(response.status_code, 200)


class AttachmentTestCase(OpportunityModel, TestCase):
    def test_attachment_add(self):
        url = "/opportunities/attachment/add/"
        data = {'opportunityid': self.opportunity.id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)

    # def test_attachment_delete(self):
    #     url = "/opportunities/attachment/remove/"
    #     data = {'attachment_id':self.attachment.id}
    #     response = self.client.post(url,data)
    #     self.assertEqual(response.status_code, 200)