from django.urls import path
from events import api_views

app_name = "api_events"

urlpatterns = [
    path("", api_views.EventListView.as_view()),
    path("<int:pk>/", api_views.EventDetailView.as_view()),
    path("comment/<int:pk>/", api_views.EventCommentView.as_view()),
    path("attachment/<int:pk>/", api_views.EventAttachmentView.as_view()),
]
