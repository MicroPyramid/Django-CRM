from django.conf import settings


def app_name(request):
    return {
        "APPLICATION_NAME": settings.APPLICATION_NAME,
    }
