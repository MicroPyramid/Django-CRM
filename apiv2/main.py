# fastapi_app/main.py
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crm.settings")
django.setup()

from fastapi import FastAPI
from apiv2.routers import users, leads, tasks, auth, org
from fastapi import Request

app = FastAPI(title="CRM API", version="1.0.0")


@app.middleware("http")
async def log_request(request: Request, call_next):
    body = await request.body()
    print("Request body:", body)  # or use proper logging
    response = await call_next(request)
    return response

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(org.router, prefix="/api/org", tags=["Org"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
# app.include_router(leads.router, prefix="/api/leads", tags=["Leads"])
# app.include_router(tasks.router, prefix="/api/tasks", tags=["Tasks"])
