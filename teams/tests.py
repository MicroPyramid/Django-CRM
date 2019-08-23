from django.test import TestCase
from django.urls import reverse

from common.models import User
from teams.models import Teams


class TeamObjectTest(object):

    def setUp(self):
        self.user = User.objects.create(
            first_name="johnTeam", username='johnDoeTeam', email='johnDoeTeam@example.com', role='ADMIN')
        self.user.set_password('password')
        self.user.save()

        self.user1 = User.objects.create(
            first_name="janeTeam",
            username='janeDoeTeam',
            email='janeDoeTeam@example.com',
            role="USER",
            has_sales_access=True)
        self.user1.set_password('password')
        self.user1.save()

        self.user2 = User.objects.create(
            first_name="joeTeam",
            username='joeTeam',
            email='joeTeam@example.com',
            role="USER",
            has_sales_access=True)
        self.user2.set_password('password')
        self.user2.save()

        self.team_dev = Teams.objects.create(name='team 1')
        self.team_dev.users.add(self.user1.id)


class TeamListTestCase(TeamObjectTest, TestCase):

    def test_teams_list(self):
        self.client.login(email='johnDoeTeam@example.com',
                          password='password')
        response = self.client.get(reverse('teams:teams_list'))
        self.assertEqual(response.status_code, 200)

        self.client.login(email='janeDoeTeam@example.com',
                          password='password')
        response = self.client.get(reverse('teams:teams_list'))
        self.assertEqual(response.status_code, 403)

        data = {
            'team_name': 'team 1',
            'created_by': self.user.id,
            'assigned_to': self.user1.id,
        }

        self.client.login(email='johnDoeTeam@example.com',
                          password='password')
        response = self.client.post(reverse('teams:teams_list'), data)
        self.assertEqual(response.status_code, 200)


class TeamCreateCase(TeamObjectTest, TestCase):

    def test_team_create(self):
        self.client.login(email='johnDoeTeam@example.com',
                          password='password')
        response = self.client.get(reverse('teams:team_create'))
        self.assertEqual(response.status_code, 200)

        self.client.login(email='janeDoeTeam@example.com',
                          password='password')
        response = self.client.get(reverse('teams:team_create'))
        self.assertEqual(response.status_code, 403)

        data = {
            'name': 'team create',
            'users': self.user1.id,
            'description': 'team description'
        }

        self.client.login(email='johnDoeTeam@example.com',
                          password='password')
        response = self.client.post(reverse('teams:team_create'), data)
        self.assertEqual(response.status_code, 200)

        data = {
            'name': '',
            'users': self.user1.id,
            'description': 'team description'
        }

        response = self.client.post(reverse('teams:team_create'), data)
        self.assertEqual(response.status_code, 200)


class TeamDetailCase(TeamObjectTest, TestCase):

    def test_team_detail(self):
        self.client.login(email='johnDoeTeam@example.com',
                          password='password')
        response = self.client.get(
            reverse('teams:team_detail', args=(self.team_dev.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(str(self.team_dev), 'team 1')

        self.client.login(email='janeDoeTeam@example.com',
                          password='password')
        response = self.client.get(
            reverse('teams:team_detail', args=(self.team_dev.id,)))
        self.assertEqual(response.status_code, 403)


class TeamEditCase(TeamObjectTest, TestCase):

    def test_team_edit(self):
        self.client.login(email='johnDoeTeam@example.com',
                          password='password')
        response = self.client.get(
            reverse('teams:team_edit', args=(self.team_dev.id,)))
        self.assertEqual(response.status_code, 200)

        self.client.login(email='janeDoeTeam@example.com',
                          password='password')
        response = self.client.get(
            reverse('teams:team_edit', args=(self.team_dev.id,)))
        self.assertEqual(response.status_code, 403)

        data = {
            'name': 'team 1 edit',
            'users': '',
        }

        self.client.login(email='johnDoeTeam@example.com',
                          password='password')
        response = self.client.post(
            reverse('teams:team_edit', args=(self.team_dev.id,)), data)
        self.assertEqual(response.status_code, 200)
        data = {
            'name': 'team 1 edit',
            'users': self.user1.id,
        }
        response = self.client.post(
            reverse('teams:team_edit', args=(self.team_dev.id,)), data)
        self.assertEqual(response.status_code, 200)

        data = {
            'name': 'team 1 Edit',
            'users': self.user1.id,
        }
        response = self.client.post(
            reverse('teams:team_create'), data)
        self.assertEqual(response.status_code, 200)


class TeamDeleteCase(TeamObjectTest, TestCase):

    def test_team_delete(self):
        self.client.login(email='janeDoeTeam@example.com',
                          password='password')
        response = self.client.get(
            reverse('teams:team_delete', args=(self.team_dev.id,)))
        self.assertEqual(response.status_code, 403)

        self.client.login(email='johnDoeTeam@example.com',
                          password='password')
        response = self.client.get(
            reverse('teams:team_delete', args=(self.team_dev.id,)))
        self.assertEqual(response.status_code, 302)
