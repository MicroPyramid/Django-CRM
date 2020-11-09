from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views
from django.urls import include, path
from common.views import handler404, handler500
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf.urls import url
from rest_framework import permissions


openapi_info = openapi.Info(
    title="Crm API",
    default_version='v1',
)

schema_view = get_schema_view(
    openapi_info,
    public=True,
    permission_classes=(permissions.AllowAny,),
)


app_name = "crm"

urlpatterns = [
    url(r'^swagger(?P<format>\.json|\.yaml)$',
        schema_view.without_ui(cache_timeout=0), name='schema-json'),
    url(r'^swagger/$', schema_view.with_ui('swagger',
                                           cache_timeout=0), name='schema-swagger-ui'),
    url(r'^redoc/$', schema_view.with_ui('redoc',
                                         cache_timeout=0), name='schema-redoc'),
    path("", include("common.urls", namespace="common")),
    path("api/", include("common.app_urls", namespace="common_urls")),
    path("", include("django.contrib.auth.urls")),
    path("marketing/", include("marketing.urls", namespace="marketing")),
    path("accounts/", include("accounts.urls", namespace="accounts")),
    path("leads/", include("leads.urls", namespace="leads")),
    path("contacts/", include("contacts.urls", namespace="contacts")),
    path("opportunities/", include("opportunity.urls", namespace="opportunities")),
    path("cases/", include("cases.urls", namespace="cases")),
    path("tasks/", include("tasks.urls", namespace="tasks")),
    path("invoices/", include("invoices.urls", namespace="invoices")),
    path("events/", include("events.urls", namespace="events")),
    path("teams/", include("teams.urls", namespace="teams")),
    path("emails/", include("emails.urls", namespace="emails")),
    # path('planner/', include('planner.urls', namespace="planner")),
    path("logout/", views.LogoutView, {"next_page": "/login/"}, name="logout"),
]

if settings.DEBUG:
    urlpatterns = urlpatterns + static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )


handler404 = handler404
handler500 = handler500
