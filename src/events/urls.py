from django.urls import path
from events import views

app_name = "api_events"

urlpatterns = [
    path("", views.EventListView.as_view()),
    path("<int:pk>/", views.EventDetailView.as_view()),
    path("comment/<int:pk>/", views.EventCommentView.as_view()),
    path("attachment/<int:pk>/", views.EventAttachmentView.as_view()),
]
