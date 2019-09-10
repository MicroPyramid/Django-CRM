from datetime import datetime, timedelta

from django.test import TestCase
from django.test.utils import override_settings

from marketing.tasks import (delete_multiple_contacts_tasks,
                             list_all_bounces_unsubscribes, run_all_campaigns,
                             run_campaign,
                             send_campaign_email_to_admin_contact,
                             send_scheduled_campaigns, upload_csv_file)
from marketing.tests import TestMarketingModel


class TestCeleryTasks(TestMarketingModel, TestCase):

    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                       CELERY_ALWAYS_EAGER=True,
                       BROKER_BACKEND='memory')
    def test_celery_tasks(self):
        task = run_campaign.apply((self.campaign.id,),)
        self.assertEqual('SUCCESS', task.state)

        self.campaign.reply_to_email = None
        self.campaign.save()

        task = run_campaign.apply((self.campaign.id,),)
        self.assertEqual('SUCCESS', task.state)

        self.campaign.schedule_date_time = datetime.now()
        self.campaign.save()

        task = run_all_campaigns.apply()
        self.assertEqual('SUCCESS', task.state)

        task = list_all_bounces_unsubscribes.apply()
        self.assertEqual('SUCCESS', task.state)

        task = send_scheduled_campaigns.apply()
        self.assertEqual('SUCCESS', task.state)

        task = delete_multiple_contacts_tasks.apply((self.contact_list.id,),)
        self.assertEqual('SUCCESS', task.state)

        task = send_campaign_email_to_admin_contact.apply((self.campaign.id,),)
        self.assertEqual('SUCCESS', task.state)

        valid_rows = [
            {'company name': 'company_name_1', 'email': 'user1@email.com', 'first name': 'first_name',
                'last name': 'last_name', 'city': 'Hyderabad', 'state': 'Telangana'},
            {'company name': 'company_name_2', 'email': 'user2@email.com', 'first name': 'first_name',
                'last name': 'last_name', 'city': 'Hyderabad', 'state': 'Telangana'},
            {'company name': 'company_name_3', 'email': 'user3@email.com', 'first name': 'first_name',
                'last name': 'last_name', 'city': 'Hyderabad', 'state': 'Telangana'},
            {'company name': 'company_name_4', 'email': 'user4@email.com', 'first name': 'first_name',
                'last name': 'last_name', 'city': 'Hyderabad', 'state': 'Telangana'}
        ]

        invalid_rows = [
            {'company name': 'company_name_1', 'email': 'useremail.com', 'first name': 'first_name',
                'last name': 'last_name', 'city': 'Hyderabad', 'state': 'Telangana'},
            {'company name': 'company_name_2', 'email': 'user2@email', 'first name': 'first_name',
                'last name': 'last_name', 'city': 'Hyderabad', 'state': 'Telangana'},
        ]
        task = upload_csv_file.apply(
            (valid_rows, invalid_rows, self.user.id, [self.contact_list.id, ],),)
        self.assertEqual('SUCCESS', task.state)
