from django.urls import include, path

app_name = "common_urls"
urlpatterns = [
    path("", include(("common.api_urls"))),
    path("accounts/", include("accounts.api_urls", namespace="api_accounts")),
    path("contacts/", include("contacts.api_urls", namespace="api_contacts")),
]
