from django.urls import path

from leads.views.lead_interactions import (
    CreateLeadFromSite,
    LeadAttachmentView,
    LeadCommentView,
    LeadUploadView,
)
from leads.views.lead_views import LeadDetailView, LeadListView
from leads.views.kanban_views import (
    LeadKanbanView,
    LeadMoveView,
    LeadPipelineListCreateView,
    LeadPipelineDetailView,
    LeadStageCreateView,
    LeadStageDetailView,
    LeadStageReorderView,
)

app_name = "api_leads"

urlpatterns = [
    # Lead from external site
    path(
        "create-from-site/",
        CreateLeadFromSite.as_view(),
        name="create_lead_from_site",
    ),
    # Lead list and bulk operations
    path("", LeadListView.as_view()),
    path("upload/", LeadUploadView.as_view()),
    # Kanban endpoints
    path("kanban/", LeadKanbanView.as_view(), name="lead_kanban"),
    # Pipeline management
    path(
        "pipelines/", LeadPipelineListCreateView.as_view(), name="pipeline_list_create"
    ),
    path(
        "pipelines/<str:pk>/", LeadPipelineDetailView.as_view(), name="pipeline_detail"
    ),
    path(
        "pipelines/<str:pipeline_pk>/stages/",
        LeadStageCreateView.as_view(),
        name="stage_create",
    ),
    path(
        "pipelines/<str:pipeline_pk>/stages/reorder/",
        LeadStageReorderView.as_view(),
        name="stage_reorder",
    ),
    # Stage management
    path("stages/<str:pk>/", LeadStageDetailView.as_view(), name="stage_detail"),
    # Lead detail routes (must be after specific routes due to pk pattern)
    path("<str:pk>/", LeadDetailView.as_view()),
    path("<str:pk>/move/", LeadMoveView.as_view(), name="lead_move"),
    path("comment/<str:pk>/", LeadCommentView.as_view()),
    path("attachment/<str:pk>/", LeadAttachmentView.as_view()),
]
