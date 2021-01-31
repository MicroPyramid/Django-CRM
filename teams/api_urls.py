from django.urls import path
from teams import api_views

app_name = "api_leads"

urlpatterns = [
    path("", api_views.TeamsListView.as_view()),
    path("<int:pk>/", api_views.TeamsDetailView.as_view()),
]
