from django.urls import path

from events import views

app_name = "api_events"

urlpatterns = [
    path("", views.EventListView.as_view()),
    path("<str:pk>/", views.EventDetailView.as_view()),
    path("comment/<str:pk>/", views.EventCommentView.as_view()),
    path("attachment/<str:pk>/", views.EventAttachmentView.as_view()),
]
