from django.urls import path

from opportunity.views.line_item_views import (
    OpportunityLineItemDetailView,
    OpportunityLineItemListView,
)
from opportunity.views.opportunity_interactions import (
    OpportunityAttachmentView,
    OpportunityCommentView,
)
from opportunity.views.opportunity_views import (
    OpportunityDetailView,
    OpportunityListView,
)

app_name = "api_opportunities"

urlpatterns = [
    path("", OpportunityListView.as_view()),
    path("<str:pk>/", OpportunityDetailView.as_view()),
    path("comment/<str:pk>/", OpportunityCommentView.as_view()),
    path("attachment/<str:pk>/", OpportunityAttachmentView.as_view()),
    # Line items
    path(
        "<str:opportunity_id>/line-items/",
        OpportunityLineItemListView.as_view(),
        name="opportunity-line-items-list",
    ),
    path(
        "<str:opportunity_id>/line-items/<str:line_item_id>/",
        OpportunityLineItemDetailView.as_view(),
        name="opportunity-line-items-detail",
    ),
]
