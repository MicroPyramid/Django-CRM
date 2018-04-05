from django.test import TestCase
from django.test import Client
from common.models import User


class TestHomePage(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_superuser(
            'user@micropyramid.com', 'username', 'password')
        user_login = self.client.login(username='user@micropyramid.com', password='password')

    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        if response.status_code == 200:
            self.assertIn("Micro", str(response.content))
