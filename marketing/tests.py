from django.test import TestCase
from django.test import Client
from common.models import User
from django.shortcuts import reverse
import os
# from marketing.models import Tag, Document, ContactList, EmailTemplate, Contact, Campaign, CampaignLinkClick, CampaignLog, Link, CampaignOpen
# from .models import *
from marketing.views import *
# Create your tests here.


class TestMarketingModel(object):
    def setUp(self):
        self.client = Client()

        self.user = User.objects.create(
            username='john', email='john@example.com', role="ADMIN")
        self.user.set_password('password')
        self.user.save()

        self.client.login(username='john@example.com', password='password')


class TestTemplates(TestMarketingModel, TestCase):
    def test_templates(self):
        url1 = reverse('marketing:dashboard')
        url2 = reverse('marketing:contact_lists')
        url4 = reverse('marketing:contacts_list')
        url5 = reverse('marketing:contact_list_new')
        url8 = reverse('marketing:email_template_list')
        url9 = reverse('marketing:email_template_new')
        url12 = reverse('marketing:campaign_list')
        url13 = reverse('marketing:campaign_new')
        resp1 = self.client.get(url1)
        resp2 = self.client.get(url2)
        resp4 = self.client.get(url4)
        resp5 = self.client.get(url5)
        resp8 = self.client.get(url8)
        resp9 = self.client.get(url9)
        resp12 = self.client.get(url12)
        resp13 = self.client.get(url13)
        self.assertEqual(resp1.status_code, 200)
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp4.status_code, 200)
        self.assertEqual(resp5.status_code, 200)
        self.assertEqual(resp8.status_code, 200)
        self.assertEqual(resp9.status_code, 200)
        self.assertEqual(resp12.status_code, 200)
        self.assertEqual(resp13.status_code, 200)



class TestCreateContacts(TestMarketingModel, TestCase):

    def test_contact_list_new(self):
        data= ['company name,email,first name,last name,city,state\n',
                    'mp,admin@mp,Admin,MP,Hyderabad,Telangana\n',
                    'mp,hrmp.com,HR,MP,Hyderabad,Telangana\n',
                    'mp,contactus@mp.com,,MP,Hyderabad,Telangana\n',
                    'mp,test@mp.com,Test,MP,Hyderabad,Telangana\n',
                    'mp,hello@mp.com,Hello,MP,Hyderabad,Telangana\n']

        with open('marketing/test_file.csv', 'w') as fp:
            fp.writelines(data)

        with open('marketing/test_file.csv') as fp:
            response = self.client.post(reverse('marketing:contact_list_new'),
                {'name': 'sample_test', 'attachment': fp})
            self.assertEqual(response.status_code, 200)

        os.remove('marketing/test_file.csv')

class TestViewContactList(TestMarketingModel, TestCase):

    # def test_view_contact_list(self):
    #     ## ContactList create object first !!!
    #     response = self.client.get('/m/cl/list/1/detail/')
    #     self.assertEqual(response.status_code, 200)
    #     self.assertTemplateUsed(response, 'marketing/lists/detail.html')

    def test_contact_list_pagination(self):
        response = self.client.get(reverse('marketing:contact_lists') + '?page=1')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('marketing:contact_lists') + '?page=asdf')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('marketing:contact_lists') + '?page=')
        self.assertEqual(response.status_code, 200)


class TestEmailTemplateList(TestMarketingModel, TestCase):


    def test_email_template_list_pagination(self):
        response = self.client.get(reverse('marketing:email_template_list') + '?page=1')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('marketing:email_template_list') + '?page=asdf')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('marketing:email_template_list') + '?page=')
        self.assertEqual(response.status_code, 200)


# class SearchContactsList(TestMarketingModel, TestCase):


#     def test_search_contact_list(self):
#         response = self.client.post('/m/cl/all/', {'tags':'abcd', 'search': 'campaign1'})
#         self.assertEqual(response.status_code, 301)