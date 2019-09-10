from django.test import TestCase
from django.test.utils import override_settings

from opportunity.tasks import send_email_to_assigned_user
from opportunity.tests import OpportunityModel


class TestCeleryTasks(OpportunityModel, TestCase):

    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                       CELERY_ALWAYS_EAGER=True,
                       BROKER_BACKEND='memory')
    def test_celery_tasks(self):
        task = send_email_to_assigned_user.apply(
            ([self.user.id, self.user1.id, ], self.opportunity.id,),)
        self.assertEqual('SUCCESS', task.state)
