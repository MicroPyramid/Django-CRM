from django.urls import path
from tasks import api_views

app_name = "api_tasks"

urlpatterns = [
    path("", api_views.TaskListView.as_view()),
    path("<int:pk>/", api_views.TaskDetailView.as_view()),
    path("comment/<int:pk>/", api_views.TaskCommentView.as_view()),
    path("attachment/<int:pk>/", api_views.TaskAttachmentView.as_view()),
]
