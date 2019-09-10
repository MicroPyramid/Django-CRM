import os
from celery.schedules import crontab

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
# Set in local_settings.py
SECRET_KEY = 'SECRET_SECRET_SECRET'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG_STATUS', True)

ALLOWED_HOSTS = ['*']

# Application definition

LOGIN_REDIRECT_URL = '/'

LOGIN_URL = '/login/'

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'simple_pagination',
    'compressor',
    'common',
    'accounts',
    'cases',
    'contacts',
    'emails',
    'leads',
    'opportunity',
    'planner',
    'sorl.thumbnail',
    'phonenumber_field',
    'storages',
    'marketing',
    'tasks',
    'invoices',
    'events',
    'teams',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'crm.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, "templates"), ],
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
]

WSGI_APPLICATION = 'crm.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'dj_crm',
        'USER': 'postgres',
        'PASSWORD': 'root',
        'HOST': os.getenv('DB_HOST', '127.0.0.1'),
        'PORT': os.getenv('DB_PORT', '5432')
    }
}

STATICFILES_DIRS = [os.path.join(BASE_DIR, "static"), ]

# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

STATIC_URL = '/static/'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# EMAIL_HOST = 'localhost'
# EMAIL_PORT = 25
# AUTHENTICATION_BACKENDS = ('django.contrib.auth.backends.ModelBackend', )


EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_HOST_USER = os.getenv('SG_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('SG_PWD', '')
EMAIL_PORT = 587
EMAIL_USE_TLS = True

AUTH_USER_MODEL = 'common.User'

STORAGE_TYPE = os.getenv('STORAGE_TYPE', 'normal')

if STORAGE_TYPE == 'normal':
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
    MEDIA_URL = '/media/'

    STATIC_URL = '/static/'
    STATICFILES_DIRS = (BASE_DIR + '/static',)
    COMPRESS_ROOT = BASE_DIR + '/static/'

elif STORAGE_TYPE == 's3-storage':

    AWS_STORAGE_BUCKET_NAME = AWS_BUCKET_NAME = os.getenv('AWSBUCKETNAME', '')
    AM_ACCESS_KEY = AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', '')
    AM_PASS_KEY = AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', '')
    S3_DOMAIN = AWS_S3_CUSTOM_DOMAIN = str(AWS_BUCKET_NAME) + '.s3.amazonaws.com'

    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }

    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    DEFAULT_S3_PATH = "media"
    STATICFILES_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
    STATIC_S3_PATH = "static"
    COMPRESS_STORAGE = 'storages.backends.s3boto.S3BotoStorage'

    COMPRESS_CSS_FILTERS = [
        'compressor.filters.css_default.CssAbsoluteFilter', 'compressor.filters.cssmin.CSSMinFilter']
    COMPRESS_JS_FILTERS = ['compressor.filters.jsmin.JSMinFilter']
    COMPRESS_REBUILD_TIMEOUT = 5400

    MEDIA_ROOT = '/%s/' % DEFAULT_S3_PATH
    MEDIA_URL = '//%s/%s/' % (S3_DOMAIN, DEFAULT_S3_PATH)
    STATIC_ROOT = "/%s/" % STATIC_S3_PATH
    STATIC_URL = 'https://%s/' % (S3_DOMAIN)
    ADMIN_MEDIA_PREFIX = STATIC_URL + 'admin/'

    CORS_ORIGIN_ALLOW_ALL = True

    AWS_IS_GZIPPED = True
    AWS_ENABLED = True
    AWS_S3_SECURE_URLS = True

COMPRESS_ROOT = BASE_DIR + '/static/'

COMPRESS_ENABLED = True

COMPRESS_OFFLINE_CONTEXT = {
    'STATIC_URL': 'STATIC_URL',
}

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

COMPRESS_CSS_FILTERS = [
    'compressor.filters.css_default.CssAbsoluteFilter', 'compressor.filters.cssmin.CSSMinFilter']
COMPRESS_REBUILD_TIMEOUT = 5400

COMPRESS_OUTPUT_DIR = 'CACHE'
COMPRESS_URL = STATIC_URL

COMPRESS_PRECOMPILERS = (
    ('text/less', 'lessc {infile} {outfile}'),
    ('text/x-sass', 'sass {infile} {outfile}'),
    ('text/x-scss', 'sass {infile} {outfile}'),
)

COMPRESS_OFFLINE_CONTEXT = {
    'STATIC_URL': 'STATIC_URL',
}

DEFAULT_FROM_EMAIL = 'no-reply@django-crm.micropyramid.com'

# celery Tasks
CELERY_BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'redis://localhost:6379'

CELERY_BEAT_SCHEDULE = {
    "runs-campaign-for-every-thiry-minutes": {
        "task": "marketing.tasks.run_all_campaigns",
        "schedule": crontab(minute=30, hour='*')
    },
    "runs-campaign-for-every-five-minutes": {
        "task": "marketing.tasks.list_all_bounces_unsubscribes",
        "schedule": crontab(minute='*/5')
    },
    "runs-scheduled-campaigns-for-every-one-hour": {
        "task": "marketing.tasks.send_scheduled_campaigns",
        "schedule": crontab(hour='*/1')
    },
    "runs-scheduled-emails-for-accounts-every-five-minutes": {
        "task": "accounts.tasks.send_scheduled_emails",
        "schedule": crontab(minute='*/1')
    }
}

MAIL_SENDER = 'AMAZON'
INACTIVE_MAIL_SENDER = 'MANDRILL'

AM_ACCESS_KEY = os.getenv('AM_ACCESS_KEY', '')
AM_PASS_KEY = os.getenv('AM_PASS_KEY', '')
AWS_REGION = os.getenv('AWS_REGION', '')

MGUN_API_URL = os.getenv('MGUN_API_URL', '')
MGUN_API_KEY = os.getenv('MGUN_API_KEY', '')

SG_USER = os.getenv('SG_USER', '')
SG_PWD = os.getenv('SG_PWD', '')

MANDRILL_API_KEY = os.getenv('MANDRILL_API_KEY', '')

ADMIN_EMAIL = "admin@micropyramid.com"

URL_FOR_LINKS = "http://demo.django-crm.io"

try:
    from .dev_settings import *
except ImportError:
    pass


GP_CLIENT_ID = os.getenv('GP_CLIENT_ID', False)
GP_CLIENT_SECRET = os.getenv('GP_CLIENT_SECRET', False)
ENABLE_GOOGLE_LOGIN = os.getenv('ENABLE_GOOGLE_LOGIN', False)

MARKETING_REPLY_EMAIL = 'djangocrm@micropyramid.com'

PASSWORD_RESET_TIMEOUT_DAYS = 3

SENTRY_ENABLED = os.getenv('SENTRY_ENABLED', False)

if SENTRY_ENABLED and not DEBUG:
    if os.getenv('SENTRYDSN') is not None:
        RAVEN_CONFIG = {
            'dsn': os.getenv('SENTRYDSN', ''),
        }
        INSTALLED_APPS = INSTALLED_APPS + [
            'raven.contrib.django.raven_compat',
        ]
        MIDDLEWARE = [
            'raven.contrib.django.raven_compat.middleware.Sentry404CatchMiddleware',
            'raven.contrib.django.raven_compat.middleware.SentryResponseErrorIdMiddleware',
         ] + MIDDLEWARE
        LOGGING = {
            'version': 1,
            'disable_existing_loggers': True,
            'root': {
                'level': 'WARNING',
                'handlers': ['sentry'],
            },
            'formatters': {
                'verbose': {
                    'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
                },
            },
            'handlers': {
                'sentry': {
                    'level': 'ERROR',
                    'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
                },
                'console': {
                    'level': 'DEBUG',
                    'class': 'logging.StreamHandler',
                    'formatter': 'verbose'
                }
            },
            'loggers': {
                'django.db.backends': {
                    'level': 'ERROR',
                    'handlers': ['console'],
                    'propagate': False,
                },
                'raven': {
                    'level': 'DEBUG',
                    'handlers': ['console'],
                    'propagate': False,
                },
                'sentry.errors': {
                    'level': 'DEBUG',
                    'handlers': ['console'],
                    'propagate': False,
                },
            },
        }

# Load the local settings file if it exists
if os.path.isfile('crm/local_settings.py'):
    from .local_settings import *
else:
    print("No local settings file found")
