from django.urls import path

from opportunity.views.opportunity_interactions import (
    OpportunityAttachmentView,
    OpportunityCommentView,
)
from opportunity.views.opportunity_views import OpportunityDetailView, OpportunityListView

app_name = "api_opportunities"

urlpatterns = [
    path("", OpportunityListView.as_view()),
    path("<str:pk>/", OpportunityDetailView.as_view()),
    path("comment/<str:pk>/", OpportunityCommentView.as_view()),
    path("attachment/<str:pk>/", OpportunityAttachmentView.as_view()),
]
