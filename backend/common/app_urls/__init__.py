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
    path("cases/", include("cases.urls", namespace="api_cases")),
    path("invoices/", include("invoices.api_urls", namespace="api_invoices")),  # Phase 2 completion
    path("marketing/", include("marketing.urls", namespace="api_marketing")),  # Phase 3
    path("boards/", include("boards.urls", namespace="api_boards")),  # Phase 3: Kanban Boards
]
