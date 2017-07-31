#!/usr/bin/env python
import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner
from django.conf.urls import include, url
from django_crm import CRM_APPS


if __name__ == "__main__":

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    settings.configure(
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
            }
        },
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.staticfiles',
        ] + CRM_APPS,
        MIDDLEWARE_CLASSES=(
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
        ),
        ROOT_URLCONF='run_tests',
        STATIC_URL='/static/',
        STATIC_ROOT=BASE_DIR + '/static',
        STATICFILES_FINDERS=[
            'django.contrib.staticfiles.finders.FileSystemFinder',
            'django.contrib.staticfiles.finders.AppDirectoriesFinder',
            'compressor.finders.CompressorFinder',
        ],
        TEMPLATES=[
            {
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'DIRS': ['templates'],
                'APP_DIRS': True,
                'OPTIONS': {
                    'context_processors': [
                        'django.template.context_processors.debug',
                        'django.template.context_processors.request',
                        'django.contrib.auth.context_processors.auth',
                        'django.contrib.messages.context_processors.messages',
                    ],
                },
            },
        ],
        ALLOWED_HOSTS=[
            'django-crm.com',
        ],
        HOST_URL='http://django-crm.com',
        MAIL_SENDER=None
    )

    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["django_crm"])
    sys.exit(bool(failures))


urlpatterns = [
    url(r'^', include('django_crm.urls')),
]
