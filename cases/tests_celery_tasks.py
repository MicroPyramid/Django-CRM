from django.test import TestCase
from django.test.utils import override_settings

from cases.tasks import send_email_to_assigned_user
from cases.tests import CaseCreation


class TestCeleryTasks(CaseCreation, TestCase):

    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                       CELERY_ALWAYS_EAGER=True,
                       BROKER_BACKEND='memory')
    def test_celery_tasks(self):
        task = send_email_to_assigned_user.apply(
            ([self.user.id, self.user1.id, ], self.case.id,),)
        self.assertEqual('SUCCESS', task.state)
