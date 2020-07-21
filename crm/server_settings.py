import os


DOMAIN_NAME = "bottlecrm.com"

AWS_STORAGE_BUCKET_NAME = AWS_BUCKET_NAME = os.getenv("AWSBUCKETNAME", "")
AM_ACCESS_KEY = AWS_ACCESS_KEY_ID = os.getenv("AWSACCESSKEYID", "")
AM_PASS_KEY = AWS_SECRET_ACCESS_KEY = os.getenv("AWSSECRETACCESSKEY", "")
S3_DOMAIN = AWS_S3_CUSTOM_DOMAIN = str(AWS_BUCKET_NAME) + ".s3.amazonaws.com"

AWS_S3_OBJECT_PARAMETERS = {
    "CacheControl": "max-age=86400",
}

STATICFILES_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
DEFAULT_S3_PATH = "media"
STATICFILES_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
STATIC_S3_PATH = "static"
COMPRESS_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

COMPRESS_JS_FILTERS = ["compressor.filters.jsmin.JSMinFilter"]

MEDIA_ROOT = "/%s/" % DEFAULT_S3_PATH
MEDIA_URL = "//%s/%s/" % (S3_DOMAIN, DEFAULT_S3_PATH)
STATIC_ROOT = "/%s/" % STATIC_S3_PATH
STATIC_URL = "https://%s/" % (S3_DOMAIN)
ADMIN_MEDIA_PREFIX = STATIC_URL + "admin/"

CORS_ORIGIN_ALLOW_ALL = True

AWS_IS_GZIPPED = True
AWS_ENABLED = True
AWS_S3_SECURE_URLS = True
COMPRESS_URL = STATIC_URL
