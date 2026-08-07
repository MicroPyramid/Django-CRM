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
    TaskPipelineDetailView,
    TaskPipelineListCreateView,
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
    # Kanban endpoints (must be before <uid:pk>/ to avoid conflicts)
    path("kanban/", TaskKanbanView.as_view(), name="task_kanban"),
    path(
        "pipelines/", TaskPipelineListCreateView.as_view(), name="pipeline_list_create"
    ),
    path(
        "pipelines/<uid:pk>/", TaskPipelineDetailView.as_view(), name="pipeline_detail"
    ),
    path(
        "pipelines/<uid:pipeline_pk>/stages/",
        TaskStageCreateView.as_view(),
        name="stage_create",
    ),
    path(
        "pipelines/<uid:pipeline_pk>/stages/reorder/",
        TaskStageReorderView.as_view(),
        name="stage_reorder",
    ),
    path("stages/<uid:pk>/", TaskStageDetailView.as_view(), name="stage_detail"),
    # Task detail and move endpoints
    path("<uid:pk>/", TaskDetailView.as_view()),
    path("<uid:pk>/move/", TaskMoveView.as_view(), name="task_move"),
    path("comment/<uid:pk>/", TaskCommentView.as_view()),
    path("attachment/<uid:pk>/", TaskAttachmentView.as_view()),
]

# Board URLs (kept separate for namespace compatibility with frontend)
board_urlpatterns = [
    # Boards
    path("", BoardListCreateView.as_view(), name="board_list_create"),
    path("<uid:pk>/", BoardDetailView.as_view(), name="board_detail"),
    # Columns
    path(
        "<uid:board_pk>/columns/",
        BoardColumnListCreateView.as_view(),
        name="column_list_create",
    ),
    # Tasks
    path(
        "columns/<uid:column_pk>/tasks/",
        BoardTaskListCreateView.as_view(),
        name="task_list_create",
    ),
    path("tasks/<uid:pk>/", BoardTaskDetailView.as_view(), name="task_detail"),
]
