from django.urls import path

from cases import kanban_views, solution_views, views

app_name = "api_cases"

urlpatterns = [
    # Cases list endpoint
    path("", views.CaseListView.as_view()),
    # Kanban endpoints (must be before <str:pk>/ to avoid conflicts)
    path("kanban/", kanban_views.CaseKanbanView.as_view(), name="case_kanban"),
    # Pipeline management
    path(
        "pipelines/",
        kanban_views.CasePipelineListCreateView.as_view(),
        name="pipeline_list_create",
    ),
    path(
        "pipelines/<str:pk>/",
        kanban_views.CasePipelineDetailView.as_view(),
        name="pipeline_detail",
    ),
    path(
        "pipelines/<str:pipeline_pk>/stages/",
        kanban_views.CaseStageCreateView.as_view(),
        name="stage_create",
    ),
    path(
        "pipelines/<str:pipeline_pk>/stages/reorder/",
        kanban_views.CaseStageReorderView.as_view(),
        name="stage_reorder",
    ),
    # Stage management
    path(
        "stages/<str:pk>/",
        kanban_views.CaseStageDetailView.as_view(),
        name="stage_detail",
    ),
    # Case detail routes (must be after specific routes due to pk pattern)
    path("<str:pk>/", views.CaseDetailView.as_view()),
    path("<str:pk>/move/", kanban_views.CaseMoveView.as_view(), name="case_move"),
    path("comment/<str:pk>/", views.CaseCommentView.as_view()),
    path("attachment/<str:pk>/", views.CaseAttachmentView.as_view()),
    # Solutions (Knowledge Base) endpoints
    path(
        "solutions/", solution_views.SolutionListView.as_view(), name="solutions_list"
    ),
    path(
        "solutions/<str:pk>/",
        solution_views.SolutionDetailView.as_view(),
        name="solution_detail",
    ),
    path(
        "solutions/<str:pk>/publish/",
        solution_views.SolutionPublishView.as_view(),
        name="solution_publish",
    ),
    path(
        "solutions/<str:pk>/unpublish/",
        solution_views.SolutionUnpublishView.as_view(),
        name="solution_unpublish",
    ),
]
