from django.test import TestCase
from django.test import Client

from common.models import User, Team


class ObjectsCreation(object):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(first_name="admin", username='admin', email='admin@micropyramid.com',
                                        is_staff=True, is_admin=True,is_superuser=True,is_active=True)
        self.user.set_password('admin123')
        self.user.save()
        user_login = self.client.login(username='admin@micropyramid.com', password='admin123')


class TestHomePage(ObjectsCreation, TestCase):
    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        if response.status_code == 200:
            self.assertIn("Micro", str(response.content))


class CommonModelTest(ObjectsCreation, TestCase):

    def test_string_representation_user(self):
        user = self.user
        self.assertEqual(str(user.get_short_name()), user.username)

    def test_string_representation_team(self):
        team = Team(name='Ajjoj')
        self.assertEqual(str(team), team.name)


class UserCreateTestCase(ObjectsCreation, TestCase):

    def test_user_create_url(self):
        response = self.client.get('/users/create/', {'email': 'admin@micropyramid.com', 'first_name': 'user',
                                                      'last_name': 'user', 'username': 'user', 'role': 'r',
                                                      'profile_pic': None})
        self.assertEqual(response.status_code, 200)
