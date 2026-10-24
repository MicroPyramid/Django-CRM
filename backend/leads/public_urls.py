"""The public lead webhook, mounted at /api/public/leads/.

`RequireOrgContext.EXEMPT_PATHS` prefix-matches `/api/public/leads/`, so this
file must hold nothing but anonymous routes that resolve their own org.
"""

from django.urls import path

from leads.views.intake_public_views import LeadIntakePostView

app_name = "public_leads"

urlpatterns = [
    path("<uid:intake_id>/", LeadIntakePostView.as_view(), name="intake"),
]
