from __future__ import absolute_import
from __future__ import unicode_literals

from .celery import app as celery_app

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.

__all__ = ["celery_app"]
