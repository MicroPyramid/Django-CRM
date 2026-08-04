"""ASGI entrypoint for Django-CRM.

Mirror of `wsgi.py` for ASGI servers (uvicorn, hypercorn, daphne). Kept so
existing ASGI deployments keep working, but **nothing in this project requires
it any more**. It existed for the in-app notifications SSE stream, which was
the only async view here; that was replaced by polling on 2026-08-03.

Prefer WSGI in production:

    gunicorn crm.wsgi:application --bind 0.0.0.0:8000 --workers 3 --threads 4

Not merely for simplicity. Under ASGI each in-flight request gets its own
thread-sensitive executor and its own thread-local database connection, with
no ceiling, which is what exhausted PostgreSQL twice in this project's
history. Under WSGI the ceiling is `workers x threads`, a number you choose.
If you do serve this module, enable pooling (`DB_POOL_ENABLED=true`, see
crm/settings.py) so the connection count is bounded some other way.

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
