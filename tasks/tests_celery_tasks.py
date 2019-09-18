from django.test import TestCase
from django.test.utils import override_settings

from tasks.celery_tasks import send_email
from tasks.tests import TaskCreateTest


class TestEventCeleryTasks(TaskCreateTest, TestCase):

    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                       CELERY_ALWAYS_EAGER=True,
                       BROKER_BACKEND='memory')
    def test_event_celery_tasks(self):
        task = send_email.apply((self.task.id, [self.user.id, self.user1.id,]))
        self.assertEqual('SUCCESS', task.state)
