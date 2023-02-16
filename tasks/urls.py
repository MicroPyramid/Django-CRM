from django.urls import path

from tasks import views

app_name = "api_tasks"

urlpatterns = [
    path("", views.TaskListView.as_view()),
    path("<int:pk>/", views.TaskDetailView.as_view()),
    path("comment/<int:pk>/", views.TaskCommentView.as_view()),
    path("attachment/<int:pk>/", views.TaskAttachmentView.as_view()),
]
