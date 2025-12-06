from django.urls import path

from tasks.views.board_views import (
    BoardColumnListCreateView,
    BoardDetailView,
    BoardListCreateView,
    BoardTaskDetailView,
    BoardTaskListCreateView,
)
from tasks.views.task_views import (
    TaskAttachmentView,
    TaskCommentView,
    TaskDetailView,
    TaskListView,
)

app_name = "api_tasks"

urlpatterns = [
    # Task endpoints
    path("", TaskListView.as_view()),
    path("<str:pk>/", TaskDetailView.as_view()),
    path("comment/<str:pk>/", TaskCommentView.as_view()),
    path("attachment/<str:pk>/", TaskAttachmentView.as_view()),
]

# Board URLs (kept separate for namespace compatibility with frontend)
board_urlpatterns = [
    # Boards
    path("", BoardListCreateView.as_view(), name="board_list_create"),
    path("<str:pk>/", BoardDetailView.as_view(), name="board_detail"),
    # Columns
    path(
        "<str:board_pk>/columns/",
        BoardColumnListCreateView.as_view(),
        name="column_list_create",
    ),
    # Tasks
    path(
        "columns/<str:column_pk>/tasks/",
        BoardTaskListCreateView.as_view(),
        name="task_list_create",
    ),
    path("tasks/<str:pk>/", BoardTaskDetailView.as_view(), name="task_detail"),
]
