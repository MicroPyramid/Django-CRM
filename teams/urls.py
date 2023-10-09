from django.urls import path

from teams import views

app_name = "api_leads"

urlpatterns = [
    path("", views.TeamsListView.as_view()),
    path("<str:pk>/", views.TeamsDetailView.as_view()),
]
