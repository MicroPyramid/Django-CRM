from django.urls import path

from tasks.views.board_views import (
    BoardColumnListCreateView,
    BoardDetailView,
    BoardListCreateView,
    BoardTaskDetailView,
    BoardTaskListCreateView,
)
from tasks.views.kanban_views import (
    TaskKanbanView,
    TaskMoveView,
    TaskPipelineListCreateView,
    TaskPipelineDetailView,
    TaskStageCreateView,
    TaskStageDetailView,
    TaskStageReorderView,
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
    # Kanban endpoints (must be before <str:pk>/ to avoid conflicts)
    path("kanban/", TaskKanbanView.as_view(), name="task_kanban"),
    path(
        "pipelines/", TaskPipelineListCreateView.as_view(), name="pipeline_list_create"
    ),
    path(
        "pipelines/<str:pk>/", TaskPipelineDetailView.as_view(), name="pipeline_detail"
    ),
    path(
        "pipelines/<str:pipeline_pk>/stages/",
        TaskStageCreateView.as_view(),
        name="stage_create",
    ),
    path(
        "pipelines/<str:pipeline_pk>/stages/reorder/",
        TaskStageReorderView.as_view(),
        name="stage_reorder",
    ),
    path("stages/<str:pk>/", TaskStageDetailView.as_view(), name="stage_detail"),
    # Task detail and move endpoints
    path("<str:pk>/", TaskDetailView.as_view()),
    path("<str:pk>/move/", TaskMoveView.as_view(), name="task_move"),
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
