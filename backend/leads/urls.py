from django.urls import path

from leads.views.lead_interactions import (
    CreateLeadFromSite,
    LeadAttachmentView,
    LeadCommentView,
    LeadUploadView,
)
from leads.views.lead_views import LeadDetailView, LeadListView

app_name = "api_leads"

urlpatterns = [
    path(
        "create-from-site/",
        CreateLeadFromSite.as_view(),
        name="create_lead_from_site",
    ),
    path("", LeadListView.as_view()),
    path("<str:pk>/", LeadDetailView.as_view()),
    path("upload/", LeadUploadView.as_view()),
    path("comment/<str:pk>/", LeadCommentView.as_view()),
    path("attachment/<str:pk>/", LeadAttachmentView.as_view()),
]
