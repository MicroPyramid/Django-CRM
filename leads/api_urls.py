from django.urls import path
from leads import api_views

app_name = "api_leads"

urlpatterns = [
    path("", api_views.LeadListView.as_view()),
    path("<int:pk>/", api_views.LeadDetailView.as_view()),
]
