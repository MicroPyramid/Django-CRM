from unittest.mock import patch

from django.test import SimpleTestCase

from accounts.models import AccountEmail
from accounts.tasks import send_email


class SendEmailTaskTest(SimpleTestCase):
    @patch("accounts.tasks.set_rls_context")
    @patch("accounts.tasks.AccountEmail.objects.get")
    def test_logs_and_returns_when_account_email_is_missing(
        self, get_account_email, set_rls_context
    ):
        get_account_email.side_effect = AccountEmail.DoesNotExist

        with self.assertLogs("accounts.tasks", level="ERROR") as logs:
            result = send_email.run("missing-email", "org-id")

        self.assertIsNone(result)
        set_rls_context.assert_called_once_with("org-id")
        get_account_email.assert_called_once_with(id="missing-email")
        self.assertEqual(
            logs.output,
            [
                "ERROR:accounts.tasks:AccountEmail id=missing-email not found, "
                "skipping task."
            ],
        )
