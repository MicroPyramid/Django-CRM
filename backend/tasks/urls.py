from django.urls import path

from tasks import views

app_name = "api_tasks"

urlpatterns = [
    # Task endpoints
    path("", views.TaskListView.as_view()),
    path("<str:pk>/", views.TaskDetailView.as_view()),
    path("comment/<str:pk>/", views.TaskCommentView.as_view()),
    path("attachment/<str:pk>/", views.TaskAttachmentView.as_view()),
]

# Board URLs (kept separate for namespace compatibility with frontend)
board_urlpatterns = [
    # Boards
    path("", views.BoardListCreateView.as_view(), name="board_list_create"),
    path("<str:pk>/", views.BoardDetailView.as_view(), name="board_detail"),
    # Columns
    path(
        "<str:board_pk>/columns/",
        views.BoardColumnListCreateView.as_view(),
        name="column_list_create",
    ),
    # Tasks
    path(
        "columns/<str:column_pk>/tasks/",
        views.BoardTaskListCreateView.as_view(),
        name="task_list_create",
    ),
    path("tasks/<str:pk>/", views.BoardTaskDetailView.as_view(), name="task_detail"),
]
