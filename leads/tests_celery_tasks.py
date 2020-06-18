from django.test import TestCase
from django.test.utils import override_settings

from leads.tasks import (create_lead_from_file, send_email,
                         send_email_to_assigned_user,
                         send_lead_assigned_emails)
from leads.tests import TestLeadModel


class TestCeleryTasks(TestLeadModel, TestCase):

    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                       CELERY_ALWAYS_EAGER=True,
                       BROKER_BACKEND='memory')
    def test_celery_tasks(self):
        task = send_email_to_assigned_user.apply(
            ([self.user.id, self.user1.id, ], self.lead.id,),)
        self.assertEqual('SUCCESS', task.state)

        task = send_lead_assigned_emails.apply(
            (self.lead.id, [self.user.id, self.user1.id, self.user2.id, ], 'https://www.example.com',),)
        self.assertEqual('SUCCESS', task.state)

        task = send_email.apply(
            ('mail subject', 'html content',), {'recipients': [self.user.id, self.user1.id, self.user2.id, ], },)
        self.assertEqual('SUCCESS', task.state)

        task = send_lead_assigned_emails.apply(
            (self.lead1.id, [self.user.id, self.user1.id, self.user2.id, ], 'https://www.example.com',),)
        self.assertEqual('SUCCESS', task.state)

        valid_rows = [
            {'title': 'lead1 csv', 'first name': 'john', 'last name': 'doe', 'website': 'www.example.com',
             'phone': '911234567890', 'email': 'user1@email.com', 'address': 'address for lead1'},
            {'title': 'lead2 csv', 'first name': 'jane', 'last name': 'doe', 'website': 'www.website.com',
             'phone': '911234567891', 'email': 'user2@email.com', 'address': 'address for lead2'},
            {'title': 'lead3 csv', 'first name': 'joe', 'last name': 'doe', 'website': 'www.test.com',
             'phone': '911234567892', 'email': 'user3@email.com', 'address': 'address for lead3'},
            {'title': 'lead4 csv', 'first name': 'john', 'last name': 'doe', 'website': 'www.sample.com',
             'phone': '911234567893', 'email': 'user4@email.com', 'address': 'address for lead4'}
        ]
        invalid_rows = [
            {'title': 'lead5 csv', 'first name': 'joe', 'last name': 'doe', 'website': 'www.test.com',
             'phone': '911234567892', 'email': 'useremail.com', 'address': 'address for lead3'},
            {'title': 'lead6 csv', 'first name': 'john', 'last name': 'doe', 'website': 'www.sample.com',
             'phone': '911234567893', 'email': 'user4@email', 'address': 'address for lead4'}
        ]
        task = create_lead_from_file.apply(
            (valid_rows, invalid_rows, self.user.id, 'example.com'),)
        self.assertEqual('SUCCESS', task.state)
