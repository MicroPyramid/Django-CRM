from django.urls import path

from opportunity import views

app_name = "api_opportunities"

urlpatterns = [
    path("", views.OpportunityListView.as_view()),
    path("<str:pk>/", views.OpportunityDetailView.as_view()),
    path("comment/<str:pk>/", views.OpportunityCommentView.as_view()),
    path("attachment/<str:pk>/", views.OpportunityAttachmentView.as_view()),
]
