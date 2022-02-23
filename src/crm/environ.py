import environ

env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False),
    SECRET_KEY=(str, "&q1&ftrxho9lrzm$$%6!cplb5ac957-9y@t@17u(3yqqb#9xl%"),
    ALLOWED_HOSTS=(list, ["127.0.0.1", "localhost", ".bottlecrm.com"]),
    ENV_TYPE=(str, "dev"),

    DEFAULT_FROM_EMAIL=(str, ''),
    ADMIN_EMAIL=(str, ''),
    MARKETING_REPLY_EMAIL=(str, ''),
    PASSWORD_RESET_MAIL_FROM_USER=(str, ''),

    CELERY_BROKER_URL=(str, "redis://127.0.0.1:6379/9"),
    CELERY_RESULT_BACKEND=(str, "redis://127.0.0.1:6379/10"),

    TIME_ZONE=(str, "Asia/Kolkata"),

    DOMAIN_NAME=(str, 'example.com'),

    # Server
    AWS_BUCKET_NAME=(str, ''),
    AWS_ACCESS_KEY_ID=(str, ''),
    AWS_SECRET_ACCESS_KEY=(str, ''),
    AWS_S3_CUSTOM_DOMAIN=(str, ''),
    AWS_SES_REGION_NAME=(str, ''),
    AWS_SES_REGION_ENDPOINT=(str, ''),

    SENTRY_DSN=(str, ''),
)
