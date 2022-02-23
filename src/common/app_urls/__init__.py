from django.urls import include, path

app_name = "common_urls"
urlpatterns = [
    path("", include(("common.urls"))),
    path("accounts/", include("accounts.urls", namespace="api_accounts")),
    path("contacts/", include("contacts.urls", namespace="api_contacts")),
    path("leads/", include("leads.urls", namespace="api_leads")),
    path("opportunities/", include("opportunity.urls", namespace="api_opportunities")),
    path("teams/", include("teams.urls", namespace="api_teams")),
    path("tasks/", include("tasks.urls", namespace="api_tasks")),
    path("events/", include("events.urls", namespace="api_events")),
    path("cases/", include("cases.urls", namespace="api_cases")),
]
