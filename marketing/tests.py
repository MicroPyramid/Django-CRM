from django.test import TestCase
from django.test import Client
from common.models import User
# from marketing.models import Tag, Document, ContactList, EmailTemplate, Contact, Campaign, CampaignLinkClick, CampaignLog, Link, CampaignOpen
# from .models import *
from marketing.views import *
# Create your tests here.


class TestMarketingModel(object):
    def setUp(self):
        self.client = Client()

        self.user = User.objects.create(
            username='jorge', email='j@mp.com', role="ADMIN")
        self.user.set_password('jorge2293')
        self.user.save()

        self.client.login(username='j@mp.com', password='jorge2293')


class TestTemplates(TestMarketingModel, TestCase):
    def test_templates(self):
        url1 = '/m/'
        url2 = '/m/cl/all/'
        url3 = '/m/cl/edit_contact/'
        url4 = '/m/cl/lists/'
        url5 = '/m/cl/list/new/'
        url6 = '/m/cl/list/cnew/'
        url7 = '/m/cl/list/detail/'
        url8 = '/m/et/list/'
        url9 = '/m/et/new/'
        # url10 = '/m/et/edit/'
        # url11 = '/m/et/detail/'
        url12 = '/m/cm/list/'
        url13 = '/m/cm/new/'
        # url14 = '/m/cm/edit/'
        # url15 = '/m/cm/details/'
        resp1 = self.client.get(url1)
        resp2 = self.client.get(url2)
        resp3 = self.client.get(url3)
        resp4 = self.client.get(url4)
        resp5 = self.client.get(url5)
        resp6 = self.client.get(url6)
        resp7 = self.client.get(url7)
        resp8 = self.client.get(url8)
        resp9 = self.client.get(url9)
        # resp10 = self.client.get(url10)
        # resp11 = self.client.get(url11)
        resp12 = self.client.get(url12)
        resp13 = self.client.get(url13)
        # resp14 = self.client.get(url14)
        # resp15 = self.client.get(url15)
        self.assertEqual(resp1.status_code, 200)
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp3.status_code, 200)
        self.assertEqual(resp4.status_code, 200)
        self.assertEqual(resp5.status_code, 200)
        self.assertEqual(resp6.status_code, 200)
        self.assertEqual(resp7.status_code, 200)
        self.assertEqual(resp8.status_code, 200)
        self.assertEqual(resp9.status_code, 200)
        # self.assertEqual(resp10.status_code, 200)
        # self.assertEqual(resp11.status_code, 200)
        self.assertEqual(resp12.status_code, 200)
        self.assertEqual(resp13.status_code, 200)
        # self.assertEqual(resp14.status_code, 200)
        # self.assertEqual(resp15.status_code, 200)
