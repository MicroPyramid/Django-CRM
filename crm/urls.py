from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views
from django.urls import include, path
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf.urls import url
from rest_framework import permissions
from common.views import index


openapi_info = openapi.Info(
    title="Crm API",
    default_version="v1",
)

schema_view = get_schema_view(
    openapi_info,
    public=True,
    permission_classes=(permissions.AllowAny,),
)


app_name = "crm"

urlpatterns = [
    url(
        r"^swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    url(
        r"^swagger/$",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("", index),
    url(
        r"^redoc/$", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"
    ),
    path("api/", include("common.app_urls", namespace="common_urls")),
    path("logout/", views.LogoutView, {"next_page": "/login/"}, name="logout"),
]

if settings.DEBUG:
    urlpatterns = urlpatterns + static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
