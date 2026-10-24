from django.urls import path

from interactions.views import InteractionDetailView, InteractionListView

app_name = "api_interactions"

urlpatterns = [
    path("", InteractionListView.as_view(), name="interactions"),
    path("<uid:pk>/", InteractionDetailView.as_view(), name="interaction"),
]
