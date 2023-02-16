import os

from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views
from django.urls import include, path
from django.urls import re_path as url
from django.views.generic import TemplateView
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls

openapi_info = openapi.Info(
    title="Crm API",
    default_version="v1",
)

schema_view = get_schema_view(
    openapi_info,
    public=True,
    url=settings.SWAGGER_ROOT_URL,
    permission_classes=(permissions.AllowAny,),
)


app_name = "crm"

urlpatterns = [
    url(
        r"^healthz/$",
        TemplateView.as_view(template_name="healthz.html"),
        name="healthz",
    ),
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
    url(
        r"^redoc/$", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"
    ),
    path("api/", include("common.app_urls", namespace="common_urls")),
    path(
        "logout/", views.LogoutView.as_view(), {"next_page": "/login/"}, name="logout"
    ),
    path('admin/', include(wagtailadmin_urls)),
    path('documents/', include(wagtaildocs_urls)),
    path('', include(wagtail_urls))

]


if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # urlpatterns = urlpatterns + static(
    #     settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    # )
