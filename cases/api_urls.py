from django.urls import path
from cases import api_views

app_name = "api_cases"

urlpatterns = [
    path("", api_views.CaseListView.as_view()),
    path("<int:pk>/", api_views.CaseDetailView.as_view()),
    path("comment/<int:pk>/", api_views.CaseCommentView.as_view()),
    path("attachment/<int:pk>/", api_views.CaseAttachmentView.as_view()),
]
