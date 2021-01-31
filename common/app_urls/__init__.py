from django.urls import include, path

app_name = "common_urls"
urlpatterns = [
    path("", include(("common.api_urls"))),
    path("accounts/", include("accounts.api_urls", namespace="api_accounts")),
    path("contacts/", include("contacts.api_urls", namespace="api_contacts")),
    path("leads/", include("leads.api_urls", namespace="api_leads")),
    path("opportunities/", include("opportunity.api_urls", namespace="api_opportunities")),
    path("teams/", include("teams.api_urls", namespace="api_teams")),
    path("tasks/", include("tasks.api_urls", namespace="api_tasks")),
]
