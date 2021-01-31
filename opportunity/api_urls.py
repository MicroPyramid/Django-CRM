from django.urls import path
from opportunity import api_views

app_name = "api_opportunities"

urlpatterns = [
    path("", api_views.OpportunityListView.as_view()),
    path("<int:pk>/", api_views.OpportunityDetailView.as_view()),
    path("comment/<int:pk>/", api_views.OpportunityCommentView.as_view()),
    path("attachment/<int:pk>/", api_views.OpportunityAttachmentView.as_view()),
]
