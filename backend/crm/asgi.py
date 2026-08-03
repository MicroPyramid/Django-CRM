"""ASGI entrypoint for Django-CRM.

Mirror of `wsgi.py` for ASGI servers (uvicorn, hypercorn, daphne). Required
for the in-app notifications SSE stream. Async views serving long-lived
connections will hold a worker hostage when run under WSGI.

Production deploy must run an ASGI server pointing at this module:

    uvicorn crm.asgi:application --host 0.0.0.0 --port 8000

`runserver` uses WSGI, so dev workflows for the Django app itself are
unchanged.

Agents and scripts reach the CRM through the REST API under `/api/`,
authenticated with a personal access token (`Authorization: Bearer
bcrm_pat_...`). See docs/integrations/ai-agents.md.
"""

import os
import sys

from django.core.asgi import get_asgi_application

PROJECT_DIR = os.path.abspath(__file__)
sys.path.append(PROJECT_DIR)


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crm.settings")

application = get_asgi_application()
