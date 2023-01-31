from django.urls import path

from opportunity import views

app_name = "api_opportunities"

urlpatterns = [
    path("", views.OpportunityListView.as_view()),
    path("<int:pk>/", views.OpportunityDetailView.as_view()),
    path("comment/<int:pk>/", views.OpportunityCommentView.as_view()),
    path("attachment/<int:pk>/", views.OpportunityAttachmentView.as_view()),
]
