"""A failed SMTP send must be logged, not raised.

Regression for the ``MAILERS`` migration: before it, ``send_magic_link_email``
(and its siblings ``send_welcome_email`` / ``send_portal_login_email``) only
caught ``botocore.exceptions.ClientError``, an SES-specific exception, so an SMTP
failure propagated out of the Celery task instead of being logged.
"""

import secrets
import smtplib
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from common.models import MagicLinkToken, PortalLoginToken, User
from common.tasks import (
    send_magic_link_email,
    send_portal_login_email,
    send_welcome_email,
)
from contacts.models import Contact

SMTP_FAILURES = pytest.mark.parametrize(
    "exc",
    [
        smtplib.SMTPAuthenticationError(535, b"Authentication failed"),
        ConnectionRefusedError(111, "Connection refused"),
    ],
)


def _assert_logged(caplog, message):
    assert any(message in r.getMessage() for r in caplog.records)


@pytest.mark.django_db
@SMTP_FAILURES
def test_magic_link_smtp_failure_is_logged_not_raised(exc, caplog):
    token = MagicLinkToken.objects.create(
        email="ada@example.com",
        token=secrets.token_hex(32),
        expires_at=timezone.now() + timedelta(minutes=10),
    )
    caplog.set_level("ERROR", logger="common.tasks")

    with patch("common.tasks.EmailMessage.send", side_effect=exc):
        send_magic_link_email(token.id)

    _assert_logged(caplog, f"Failed to send email for magic link token {token.id}")


@pytest.mark.django_db
@SMTP_FAILURES
def test_welcome_smtp_failure_is_logged_not_raised(exc, caplog):
    user = User.objects.create_user(email="ada@example.com", password="pw-not-used")
    caplog.set_level("ERROR", logger="common.tasks")

    with patch("common.tasks.EmailMessage.send", side_effect=exc):
        send_welcome_email(user.id)

    _assert_logged(caplog, f"Failed to send welcome email for user {user.id}")


@pytest.mark.django_db
@SMTP_FAILURES
def test_portal_login_smtp_failure_is_logged_not_raised(exc, caplog, org_a):
    contact = Contact.objects.create(
        org=org_a, first_name="Pat", last_name="Smith", email="pat@example.com"
    )
    token = PortalLoginToken.objects.create(
        org=org_a,
        contact=contact,
        code_hash="not-a-real-hash",
        expires_at=timezone.now() + timedelta(minutes=10),
    )
    caplog.set_level("ERROR", logger="common.tasks")

    with patch("common.tasks.EmailMessage.send", side_effect=exc):
        send_portal_login_email(token.id, "123456")

    _assert_logged(caplog, f"Failed to send email for portal login token {token.id}")
