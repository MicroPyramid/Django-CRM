import os
import sys
from django.core.wsgi import get_wsgi_application


PROJECT_DIR = os.path.abspath(__file__)
sys.path.append(PROJECT_DIR)


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crm.settings")

application = get_wsgi_application()
