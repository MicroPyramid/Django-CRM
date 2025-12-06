from datetime import datetime, timedelta

from django.test import TestCase
from django.test.utils import override_settings

from accounts.models import AccountEmail
from accounts.tasks import (
    send_email,
    send_email_to_assigned_user,
    send_scheduled_emails,
)
from accounts.tests import AccountCreateTest


class TestCeleryTasks(AccountCreateTest, TestCase):
    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND="memory",
    )
    def test_celery_tasks(self):
        org_id = str(self.account.org.id)
        email_scheduled = AccountEmail.objects.create(
            message_subject="message subject",
            message_body="message body",
            scheduled_later=True,
            timezone="Asia/Kolkata",
            from_account=self.account,
            scheduled_date_time=(datetime.now() - timedelta(minutes=5)),
            from_email="from@email.com",
            org=self.account.org,
        )
        email_scheduled.recipients.add(self.contact.id, self.contact_user1.id)
        task = send_scheduled_emails.apply((org_id,))
        self.assertEqual("SUCCESS", task.state)

        task = send_email.apply((email_scheduled.id, org_id))
        self.assertEqual("SUCCESS", task.state)

        task = send_email_to_assigned_user.apply(
            (
                [
                    self.user.id,
                    self.user1.id,
                ],
                self.account.id,
                org_id,
            ),
        )
        self.assertEqual("SUCCESS", task.state)
