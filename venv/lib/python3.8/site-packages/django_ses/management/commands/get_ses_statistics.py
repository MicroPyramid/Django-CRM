#!/usr/bin/env python

from collections import defaultdict

import boto3
from django.core.management.base import BaseCommand

from django_ses import settings
from django_ses.models import SESStat
from django_ses.views import stats_to_list


def stat_factory():
    return {
        'delivery_attempts': 0,
        'bounces': 0,
        'complaints': 0,
        'rejects': 0,
    }


class Command(BaseCommand):
    """
    Get SES sending statistic and store the result, grouped by date.
    """

    def handle(self, *args, **options):

        connection = boto3.client(
            'ses',
            aws_access_key_id=settings.ACCESS_KEY,
            aws_secret_access_key=settings.SECRET_KEY,
            aws_session_token=settings.SESSION_TOKEN,
            region_name=settings.AWS_SES_REGION_NAME,
            endpoint_url=settings.AWS_SES_REGION_ENDPOINT_URL,
            config=settings.AWS_SES_CONFIG,
        )
        stats = connection.get_send_statistics()
        data_points = stats_to_list(stats, localize=False)
        stats_dict = defaultdict(stat_factory)

        for data in data_points:
            attempts = int(data['DeliveryAttempts'])
            bounces = int(data['Bounces'])
            complaints = int(data['Complaints'])
            rejects = int(data['Rejects'])
            date = data['Timestamp'].date()
            stats_dict[date]['delivery_attempts'] += attempts
            stats_dict[date]['bounces'] += bounces
            stats_dict[date]['complaints'] += complaints
            stats_dict[date]['rejects'] += rejects

        for k, v in stats_dict.items():
            stat, created = SESStat.objects.get_or_create(
                date=k,
                defaults={
                    'delivery_attempts': v['delivery_attempts'],
                    'bounces': v['bounces'],
                    'complaints': v['complaints'],
                    'rejects': v['rejects'],
                })

            # If statistic is not new, modify data if values are different
            if not created and stat.delivery_attempts != v['delivery_attempts']:
                stat.delivery_attempts = v['delivery_attempts']
                stat.bounces = v['bounces']
                stat.complaints = v['complaints']
                stat.rejects = v['rejects']
                stat.save()
