from datetime import datetime, timedelta

from django.test import TestCase
from django.test.utils import override_settings

from accounts.tests import AccountCreateTest
from cases.tests import CaseCreation
from common.models import User, Comment
from common.tasks import (resend_activation_link_to_user,
                          send_email_to_new_user, send_email_user_delete,
                          send_email_user_mentions, send_email_user_status)
from common.tests import ObjectsCreation
from contacts.tests import ContactObjectsCreation
from events.tests import EventObjectTest
from invoices.tests import InvoiceCreateTest
from leads.tests import TestLeadModel
from opportunity.tests import OpportunityModel
from tasks.tests import TaskCreateTest


class TestCeleryTasks(ObjectsCreation, TestCase):

    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                       CELERY_ALWAYS_EAGER=True,
                       BROKER_BACKEND='memory')
    def test_celery_tasks(self):
        task = send_email_to_new_user.apply((
            self.user1.email, self.user.email,),)
        self.assertEqual('SUCCESS', task.state)

        task = send_email_user_status.apply((
            self.user1.id, self.user.id,),)
        self.assertEqual('SUCCESS', task.state)

        self.user1.is_active = False
        self.user1.has_sales_access = False
        self.user1.has_marketing_access = True
        self.user1.save()

        task = send_email_user_status.apply((
            self.user1.id,),)
        self.assertEqual('SUCCESS', task.state)

        self.user1.is_active = True
        self.user1.has_sales_access = False
        self.user1.has_marketing_access = False
        self.user1.save()

        task = send_email_user_status.apply((
            self.user1.id,),)
        self.assertEqual('SUCCESS', task.state)

        task = send_email_user_delete.apply((
            self.user1.email,),)
        self.assertEqual('SUCCESS', task.state)

        task = resend_activation_link_to_user.apply((
            self.user1.email,),)
        self.assertEqual('SUCCESS', task.state)

        task = resend_activation_link_to_user.apply((
            self.user1.email,),)
        self.assertEqual('SUCCESS', task.state)


class TestUserMentionsForAccountComments(AccountCreateTest, TestCase):

    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                       CELERY_ALWAYS_EAGER=True,
                       BROKER_BACKEND='memory')
    def test_user_mentions_for_account_comment(self):
        self.user_comment = User.objects.create(
            first_name="johnComment", username='johnDoeComment', email='johnDoeComment@example.com', role='ADMIN')
        self.user_comment.set_password('password')
        self.user_comment.save()

        self.comment.comment = 'content @{}'.format(self.user_comment.username)
        self.comment.account = self.account
        self.comment.save()

        task = send_email_user_mentions.apply((
            self.comment.id, 'accounts',),)
        self.assertEqual('SUCCESS', task.state)


class TestUserMentionsForContactsComments(ContactObjectsCreation, TestCase):

    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                       CELERY_ALWAYS_EAGER=True,
                       BROKER_BACKEND='memory')
    def test_user_mentions_for_contacts_comments(self):
        self.user_comment = User.objects.create(
            first_name="johnComment", username='johnDoeComment', email='johnDoeComment@example.com', role='ADMIN')
        self.user_comment.set_password('password')
        self.user_comment.save()

        self.comment.comment = 'content @{}'.format(self.user_comment.username)
        self.comment.contact = self.contact
        self.comment.save()

        task = send_email_user_mentions.apply((
            self.comment.id, 'contacts',),)
        self.assertEqual('SUCCESS', task.state)


class TestUserMentionsForLeadsComments(TestLeadModel, TestCase):

    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                       CELERY_ALWAYS_EAGER=True,
                       BROKER_BACKEND='memory')
    def test_user_mentions_for_leads_comments(self):
        self.user_comment = User.objects.create(
            first_name="johnComment", username='johnDoeComment', email='johnDoeComment@example.com', role='ADMIN')
        self.user_comment.set_password('password')
        self.user_comment.save()

        self.comment.comment = 'content @{}'.format(self.user_comment.username)
        self.comment.lead = self.lead
        self.comment.save()

        task = send_email_user_mentions.apply((
            self.comment.id, 'leads',),)
        self.assertEqual('SUCCESS', task.state)


class TestUserMentionsForOpportunityComments(OpportunityModel, TestCase):

    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                       CELERY_ALWAYS_EAGER=True,
                       BROKER_BACKEND='memory')
    def test_user_mentions_for_opportunity_comments(self):
        self.user_comment = User.objects.create(
            first_name="johnComment", username='johnDoeComment', email='johnDoeComment@example.com', role='ADMIN')
        self.user_comment.set_password('password')
        self.user_comment.save()

        self.comment.comment = 'content @{}'.format(self.user_comment.username)
        self.comment.opportunity = self.opportunity
        self.comment.save()

        task = send_email_user_mentions.apply((
            self.comment.id, 'opportunity',),)
        self.assertEqual('SUCCESS', task.state)


class TestUserMentionsForCasesComments(CaseCreation, TestCase):

    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                       CELERY_ALWAYS_EAGER=True,
                       BROKER_BACKEND='memory')
    def test_user_mentions_for_cases_comments(self):
        self.user_comment = User.objects.create(
            first_name="johnComment", username='johnDoeComment', email='johnDoeComment@example.com', role='ADMIN')
        self.user_comment.set_password('password')
        self.user_comment.save()

        self.comment.comment = 'content @{}'.format(self.user_comment.username)
        self.comment.case = self.case
        self.comment.save()

        task = send_email_user_mentions.apply((
            self.comment.id, 'cases',),)
        self.assertEqual('SUCCESS', task.state)


class TestUserMentionsForTasksComments(TaskCreateTest, TestCase):

    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                       CELERY_ALWAYS_EAGER=True,
                       BROKER_BACKEND='memory')
    def test_user_mentions_for_tasks_comments(self):
        self.user_comment = User.objects.create(
            first_name="johnComment", username='johnDoeComment', email='johnDoeComment@example.com', role='ADMIN')
        self.user_comment.set_password('password')
        self.user_comment.save()

        self.comment.comment = 'content @{}'.format(self.user_comment.username)
        self.comment.task = self.task
        self.comment.save()

        task = send_email_user_mentions.apply((
            self.comment.id, 'tasks',),)
        self.assertEqual('SUCCESS', task.state)


class TestUserMentionsForInvoiceComments(InvoiceCreateTest, TestCase):

    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                       CELERY_ALWAYS_EAGER=True,
                       BROKER_BACKEND='memory')
    def test_user_mentions_for_invoice_comments(self):
        self.user_comment = User.objects.create(
            first_name="johnComment", username='johnDoeComment', email='johnDoeComment@example.com', role='ADMIN')
        self.user_comment.set_password('password')
        self.user_comment.save()

        self.comment.comment = 'content @{}'.format(self.user_comment.username)
        self.comment.invoice = self.invoice
        self.comment.save()

        task = send_email_user_mentions.apply((
            self.comment.id, 'invoices',),)
        self.assertEqual('SUCCESS', task.state)


class TestUserMentionsForEventsComments(EventObjectTest, TestCase):

    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                       CELERY_ALWAYS_EAGER=True,
                       BROKER_BACKEND='memory')
    def test_user_mentions_for_events_comments(self):
        self.user_comment = User.objects.create(
            first_name="johnComment", username='johnDoeComment', email='johnDoeComment@example.com', role='ADMIN')
        self.user_comment.set_password('password')
        self.user_comment.save()

        self.comment.comment = 'content @{}'.format(self.user_comment.username)
        self.comment.event = self.event
        self.comment.save()

        task = send_email_user_mentions.apply((
            self.comment.id, 'events',),)
        self.assertEqual('SUCCESS', task.state)
