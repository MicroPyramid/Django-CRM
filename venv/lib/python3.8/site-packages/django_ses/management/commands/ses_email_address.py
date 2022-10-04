#!/usr/bin/env python
# encoding: utf-8
from optparse import make_option

import boto3
from django.core.management.base import BaseCommand

from django_ses import settings


def _add_options(target):
    return (
        target(
            '-a',
            '--add',
            dest='add',
            default=False,
            help="""Adds an email to your verified email address list.
                    This action causes a confirmation email message to be
                    sent to the specified address."""
        ),
        target(
            '-d',
            '--delete',
            dest='delete',
            default=False,
            help='Removes an email from your verified emails list'
        ),
        target(
            '-l',
            '--list',
            dest='list',
            default=False,
            action='store_true',
            help='Outputs all verified emails'
        )
    )


class Command(BaseCommand):
    """Verify, delete or list SES email addresses"""

    if hasattr(BaseCommand, 'option_list'):
        # Django < 1.10
        option_list = BaseCommand.option_list + _add_options(make_option)
    else:
        # Django >= 1.10
        def add_arguments(self, parser):
            _add_options(parser.add_argument)

    def handle(self, *args, **options):

        verbosity = options.get('verbosity', 0)
        email_to_add = options.get('add', '')
        email_to_delete = options.get('delete', '')
        list_emails = options.get('list', False)

        access_key_id = settings.ACCESS_KEY
        access_key = settings.SECRET_KEY
        session_token = settings.SESSION_TOKEN

        connection = boto3.client(
            'ses',
            aws_access_key_id=access_key_id,
            aws_secret_access_key=access_key,
            aws_session_token=session_token,
            region_name=settings.AWS_SES_REGION_NAME,
            endpoint_url=settings.AWS_SES_REGION_ENDPOINT_URL,
            config=settings.AWS_SES_CONFIG,
        )

        if email_to_add:
            if verbosity != '0':
                print(("Adding email: " + email_to_add))
            connection.verify_email_address(EmailAddress=email_to_add)
        elif email_to_delete:
            if verbosity != '0':
                print(("Removing email: " + email_to_delete))
            connection.delete_verified_email_address(EmailAddress=email_to_delete)
        elif list_emails:
            if verbosity != '0':
                print("Fetching list of verified emails:")
            response = connection.list_verified_email_addresses()
            emails = response['VerifiedEmailAddresses']
            for email in emails:
                print(email)
