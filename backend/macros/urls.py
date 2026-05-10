from django.urls import path

from macros import views

app_name = "api_macros"

urlpatterns = [
    path("", views.MacroListCreateView.as_view(), name="list_create"),
    path("<str:pk>/", views.MacroDetailView.as_view(), name="detail"),
    path("<str:pk>/render/", views.MacroRenderView.as_view(), name="render"),
]
