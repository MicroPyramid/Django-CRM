from django.test import TestCase
from django.test.utils import override_settings

from events.tasks import send_email
from events.tests import EventObjectTest


class TestEventCeleryTasks(EventObjectTest, TestCase):

    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                       CELERY_ALWAYS_EAGER=True,
                       BROKER_BACKEND='memory')
    def test_event_celery_tasks(self):
        task = send_email.apply((self.event.id, [self.user.id, self.user1.id]))
        self.assertEqual('SUCCESS', task.state)
