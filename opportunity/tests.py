from django.test import TestCase
from opportunity.models import Opportunity
from accounts.models import Account, Tags
from contacts.models import Contact
from common.models import User, Comment, Attachments, Address
from cases.models import Case
from django.core.files.uploadedfile import SimpleUploadedFile
from django.shortcuts import reverse
from django.utils.encoding import force_text

# Create your tests here.


class OpportunityModel(object):

    def setUp(self):

        self.user = User.objects.create(
            first_name="meghan", username='meghan',
            email="m@mp.com", role="ADMIN")
        self.user.set_password('madhu123')
        self.user.save()

        self.user1 = User.objects.create(
            first_name="mp",
            username='mp',
            email='mp@micropyramid.com',
            role="USER")
        self.user1.set_password('mp')
        self.user1.save()

        self.address = Address.objects.create(
            street="kphb", city="canada", postcode="584",
            country='IN')

        self.client.login(email='m@mp.com', password='madhu123')

        self.account = Account.objects.create(
            name="john", email="john@gmail.com",
            phone="58964",
            billing_address_line="",
            billing_street="kphb", billing_city="canada",
            billing_postcode="584", billing_country='US',
            website="hello.com", industry="sw",
            description="bgyyr", created_by=self.user)

        self.contacts = Contact.objects.create(
            first_name="navi",
            last_name="s",
            email="navi@gmail.com", phone="8547",
            description="defyj",
            address=self.address,
            created_by=self.user)

        self.opportunity = Opportunity.objects.create(
            name="meghan", amount="478",
            stage="negotiation/review", lead_source="Call", probability="58",
            closed_on="2016-05-04",
            description="hgfdxc",
            created_by=self.user)
        self.opportunity.assigned_to.add(self.user)
        self.case = Case.objects.create(
            name="raghu", case_type="Problem", status="New", account=self.account,
            priority="Low", description="something",
            created_by=self.user, closed_on="2016-05-04")
        self.comment = Comment.objects.create(
            comment='testikd', case=self.case, commented_by=self.user)
        self.attachment = Attachments.objects.create(
            attachment='image.png', case=self.case,
            created_by=self.user, account=self.account, opportunity=self.opportunity)

        self.tag_1 = Tags.objects.create(name='tag9')
        self.tag_2 = Tags.objects.create(name='tag10')
        self.tag_3 = Tags.objects.create(name='tag11')


class OpportunityCreateTestCase(OpportunityModel, TestCase):

    def test_opportunity_create(self):
        response = self.client.get('/opportunities/create/', {
            'name': "meghan", 'amount': "478",
            'stage': "NEGOTIATION/REVIEW",
            'lead_source': "Call", 'probability': "58",
            'closed_on': "2016-05-04", 'description': "hgfdxc"})
        self.assertEqual(response.status_code, 200)

    def test_opportunity_create_post(self):
        upload_file = open('static/images/user.png', 'rb')
        url = '/opportunities/create/'
        data = {'name': "micky", 'amount': "500", 'stage': "CLOSED WON",
                'assigned_to': str(self.user.id),
                'contacts': str(self.contacts.id),
                'tags': 'tag', 'from_account': self.account.id,
                'oppurtunity_attachment': SimpleUploadedFile(
                    upload_file.name, upload_file.read())}
        response = self.client.post(url, data)
        # self.assertEqual(response.status_code, 302)
        self.assertEqual(response.status_code, 200)

    def test_opportunity_invalid(self):
        url = '/opportunities/create/'
        data = {'name': "micky", 'amount': "", 'stage': ""}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)


class opportunityCreateTestCase(OpportunityModel, TestCase):

    def test_view_opportunity(self):
        response = self.client.get(
            '/opportunities/' + str(self.opportunity.id) + '/view/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['opportunity_record'].id, self.opportunity.id)

    def test_del_opportunity_url(self):
        response = self.client.get(
            '/opportunities/' + str(self.opportunity.id) + '/delete/')
        self.assertEqual(response['location'], '/opportunities/list/')

    def test_opportunity_delete(self):
        Opportunity.objects.filter(id=self.account.id).delete()
        response = self.client.get('/opportunities/list/')
        self.assertEqual(response.status_code, 200)


class EditOpportunityTestCase(OpportunityModel, TestCase):

    def test_edit_url(self):
        response = self.client.get(
            '/opportunities/' + str(self.opportunity.id) + '/edit/')
        self.assertEqual(response.status_code, 200)

    def test_edit_opportunity(self):
        response = self.client.get('/opportunities/' + str(self.opportunity.id) + '/edit/', {
            'name': "meghan", 'amount': "478",
            'stage': "negotiation/review",
            'lead_source': "Call", 'probability': "58",
            'closed_on': "2016-05-04", 'description': "hgfdxc"})
        resp = self.client.post('/opportunities/' + str(self.opportunity.id) +
                                '/edit/', **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        self.assertEqual(resp.status_code, 200)
        resp1 = self.client.post(
            '/opportunities/create/', **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        self.assertEqual(resp1.status_code, 200)

    def test_update_opportunity(self):
        upload_file = open('static/images/user.png', 'rb')
        url = '/opportunities/' + str(self.opportunity.id) + '/edit/'
        data = {
            'name': "meghan", 'amount': "478", 'stage': "QUALIFICATION",
            'probability': "58", 'closed_on': "2016-05-04",
            'description': "hgfdxc",
            'tags': 'tag', 'assigned_to': str(self.user.id),
            'contacts': str(self.contacts.id),
            'oppurtunity_attachment': SimpleUploadedFile(
                upload_file.name, upload_file.read())}
        response = self.client.post(url, data)
        # self.assertEqual(response.status_code, 302)
        self.assertEqual(response.status_code, 200)

    def test_update_opportunity_invalid(self):
        url = '/opportunities/' + str(self.opportunity.id) + '/edit/'
        data = {
            'name': "", 'amount': "478", 'stage': "", 'probability': "58",
            'closed_on': "2016-05-04", 'description': "hgfdxc"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)


class OpportunityListView(OpportunityModel, TestCase):

    def test_opportunity_list(self):
        self.opportunity = Opportunity.objects.all()
        response = self.client.get('/opportunities/list/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'opportunity.html')

    def test_opportunity_list_queryset(self):
        self.account = Account.objects.all()
        data = {
            'name': 'meghan', 'stage': 'city',
            'lead_source': 'Call', 'accounts': self.account}
        response = self.client.post('/opportunities/list/', data)
        get_opp_val = Opportunity.objects.get(lead_source='Call')
        self.assertEqual(get_opp_val.lead_source, 'Call')
        self.assertEqual(get_opp_val.name, str(get_opp_val))
        get_contact = Contact.objects.get(last_name="s")
        # get_account = Account.objects.get(name='john')           #  not done
        # print(get_account.name,"wqieoruopwqeiruqrewiou")
        # print(self.account.last())
        self.assertEqual(get_contact.last_name, "s")
        # self.assertEqual(get_account, self.account.last())      #  not done
        # self.assertEqual(get_opp_val.lead_source,'call')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'opportunity.html')


class ContactGetViewTestCase(OpportunityModel, TestCase):

    def test_get_contact(self):
        url = '/opportunities/contacts/'
        response = self.client.get(url)
        get_contact = Contact.objects.get(last_name="s")
        self.assertEqual(get_contact.last_name, "s")
        self.assertEqual(response.status_code, 200)


class CommentTestCase(OpportunityModel, TestCase):

    def test_comment_add(self):
        self.client.login(email='mp@micropyramid.com', password='mp')
        response = self.client.post(
            '/opportunities/comment/add/', {'opportunityid': self.opportunity.id})
        self.assertEqual(response.status_code, 200)

    def test_comment_create(self):
        response = self.client.post(
            '/opportunities/comment/add/', {'opportunityid': self.opportunity.id,
                                            'comment': 'comment'})
        self.assertEqual(response.status_code, 200)

    def test_comment_edit(self):
        response = self.client.post(
            '/opportunities/comment/edit/', {'commentid': self.comment.id})
        self.assertEqual(response.status_code, 200)

    def test_comment_update(self):
        response = self.client.post(
            '/opportunities/comment/edit/', {'commentid': self.comment.id,
                                             'comment': 'comment'})
        self.assertEqual(response.status_code, 200)

    def test_comment_delete(self):
        response = self.client.post(
            '/opportunities/comment/remove/', {'comment_id': self.comment.id})
        self.assertEqual(response.status_code, 200)

    def test_comment_form_valid(self):
        response = self.client.post(
            '/opportunities/comment/add/', {'opportunityid': self.opportunity.id,
                                            'comment': 'hello'})
        self.assertEqual(response.status_code, 200)


class AttachmentTestCase(OpportunityModel, TestCase):

    def test_attachment_create(self):
        self.client.login(email='mp@micropyramid.com', password='mp')
        url = "/opportunities/attachment/add/"
        data = {'opportunityid': self.opportunity.id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)

    def test_attachment_add(self):
        upload_file = open('static/images/user.png', 'rb')
        url = "/opportunities/attachment/add/"
        data = {'opportunityid': self.opportunity.id,
                'attachment': SimpleUploadedFile(
                    upload_file.name, upload_file.read())}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        data = {'opportunityid': self.opportunity.id}
        self.assertEqual(response.status_code, 200)

    def test_attachment_delete(self):
        url = "/opportunities/attachment/remove/"
        data = {'attachment_id': self.attachment.id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)

    def test_attachment_deletion(self):
        self.client.login(email='mp@micropyramid.com', password='mp')
        url = "/opportunities/attachment/remove/"
        data = {'attachment_id': self.attachment.id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)


class TestGetOpportunitiesView(OpportunityModel, TestCase):

    def test_get_page(self):
        url = "/opportunities/get/list/"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIsNotNone(resp.context['opportunities'])


class TestOpportunityListViewForUser(OpportunityModel, TestCase):

    def test_queryset_for_user(self):

        self.usermp = User.objects.create(
            first_name="mpmp",
            username='mpmp',
            email='mpmp@micropyramid.com',
            role="USER")
        self.usermp.set_password('mp')
        self.usermp.save()

        self.usermp1 = User.objects.create(
            first_name="mpmp1",
            username='mpmp1',
            email='mpmp1@micropyramid.com',
            role="USER")
        self.usermp1.set_password('mp')
        self.usermp1.save()

        self.opportunity = Opportunity.objects.create(
            name="meghan", amount="478",
            stage="negotiation/review", lead_source="Call", probability="58",
            closed_on="2016-05-04",
            description="hgfdxc",
            created_by=self.usermp)

        self.client.login(email='mpmp@micropyramid.com', password='mp')
        response = self.client.get(reverse('opportunity:list'))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('opportunity:list'),
                                    {'account': self.account.id, 'contacts': self.contacts.id})
        self.assertEqual(response.status_code, 200)

        self.account_mp = Account.objects.create(
            name="mike", email="mike@micropyramid.com", phone="8322855552",
            billing_address_line="", billing_street="KPHB",
            billing_city="New York",
            billing_state="usa", billing_postcode="500073",
            billing_country="IN",
            website="www.mike.com", created_by=self.usermp, status="open",
            industry="SOFTWARE", description="Yes.. Testing Done")

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
        # self.contact_mp.assigned_to.add(self.usermp)

        response = self.client.get(reverse('opportunity:save'))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('opportunity:save'),
                                    {'name': 'sample test', 'stage': "CLOSED WON", 'tags': 'tag11'})
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            reverse('opportunity:opp_edit', args=(self.opportunity.id,)))
        self.assertEqual(200, response.status_code)

        response = self.client.post(reverse('opportunity:opp_edit', args=(self.opportunity.id,)), {
            'name': 'sample update', 'stage': "CLOSED WON", 'assigned_to': str(self.user.id),
            'tags': 'tag11'
        })
        self.assertEqual(200, response.status_code)

        response = self.client.post(reverse('opportunity:opp_edit', args=(self.opportunity.id,)), {
            'name': 'sample update', 'stage': "CLOSED WON", 'tags': 'tag11'
        })
        self.assertEqual(200, response.status_code)

        response = self.client.post(
            '/opportunities/comment/add/', {'opportunityid': self.opportunity.id})
        self.assertJSONEqual(force_text(response.content), {
                             'error': ['This field is required.']})

        self.comment = Comment.objects.create(
            comment='testikd', case=self.case, commented_by=self.usermp)
        response = self.client.post(
            '/opportunities/comment/edit/', {'commentid': self.comment.id})
        self.assertJSONEqual(force_text(response.content), {
                             'error': ['This field is required.']})

        self.client.logout()

    def test_detail_view_error(self):
        self.usermp_2 = User.objects.create(
            first_name="mpmp_2",
            username='mpmp_2',
            email='mpmp2@micropyramid.com',
            role="USER")
        self.usermp_2.set_password('mp')
        self.usermp_2.save()
        self.client.login(email='mpmp2@micropyramid.com', password='mp')

        response = self.client.get(
            reverse('opportunity:opp_view', args=(self.opportunity.id,)))
        self.assertEqual(403, response.status_code)

        response = self.client.post(reverse('opportunity:opp_remove', args=(self.opportunity.id,)), {
            'pk': self.opportunity.id
        })
        self.assertEqual(403, response.status_code)

    def test_update_opportunity_error(self):
        self.usermp_3 = User.objects.create(
            first_name="mpmp_3",
            username='mpmp_3',
            email='mpmp3@micropyramid.com',
            role="USER")
        self.usermp_3.set_password('mp')
        self.usermp_3.save()
        self.client.login(email='mpmp3@micropyramid.com', password='mp')

        self.usermp4 = User.objects.create(
            first_name="mpmp4",
            username='mpmp4',
            email='mpmp4@micropyramid.com',
            role="USER")
        self.usermp4.set_password('mp')
        self.usermp4.save()

        self.opportunity2 = Opportunity.objects.create(
            name="meghansad", amount="478",
            stage="negotiation/review", lead_source="Call", probability="58",
            closed_on="2016-05-04",
            description="hgfdxc",
            created_by=self.usermp4)

        response = self.client.get(
            reverse('opportunity:opp_edit', args=(self.opportunity2.id,)))
        self.assertEqual(403, response.status_code)


class CommentTestCaseError(OpportunityModel, TestCase):

    def test_comment_add(self):

        self.client.login(email='mp@micropyramid.com', password='mp')
        response = self.client.post(
            '/opportunities/comment/add/', {'opportunityid': self.opportunity.id})
        self.assertJSONEqual(force_text(response.content), {
                             'error': "You don't have permission to comment."})

        self.usermp5 = User.objects.create(
            first_name="mpmp5",
            username='mpmp5',
            email='mpmp5@micropyramid.com',
            role="USER")
        self.usermp5.set_password('mp')
        self.usermp5.save()

        self.comment_mp = Comment.objects.create(
            comment='testikd', case=self.case, commented_by=self.user)

        response = self.client.post(
            '/opportunities/comment/edit/', {'commentid': self.comment_mp.id})
        self.assertJSONEqual(force_text(response.content), {
                             'error': "You don't have permission to edit this comment."})

        response = self.client.post(
            '/opportunities/comment/remove/', {'comment_id': self.comment_mp.id})
        self.assertJSONEqual(force_text(response.content), {
                             'error': "You don't have permission to delete this comment."})


class AttachmentTestCaseError(OpportunityModel, TestCase):

    def test_attachment_add(self):
        url = "/opportunities/attachment/add/"
        response = self.client.post(url, {'opportunityid': self.opportunity.id})
        self.assertJSONEqual(force_text(response.content),{"error": ["This field is required."]})