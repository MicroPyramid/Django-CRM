from django.test import TestCase
from django.test import Client
from common.models import User


class ObjectsCreation(object):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(first_name="admin", username='admin', email='admin@micropyramid.com')
        self.user.set_password('admin123')
        self.user.save()
        user_login = self.client.login(username='admin@micropyramid.com', password='admin123')


class TestHomePage(ObjectsCreation, TestCase):
    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        if response.status_code == 200:
            self.assertIn("Micro", str(response.content))
