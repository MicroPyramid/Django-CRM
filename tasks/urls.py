from django.urls import path

from tasks import views

app_name = "api_tasks"

urlpatterns = [
    path("", views.TaskListView.as_view()),
    path("<str:pk>/", views.TaskDetailView.as_view()),
    path("comment/<str:pk>/", views.TaskCommentView.as_view()),
    path("attachment/<str:pk>/", views.TaskAttachmentView.as_view()),
]
