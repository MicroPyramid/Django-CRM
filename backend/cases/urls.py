from django.urls import path

from cases import views
from cases import solution_views

app_name = "api_cases"

urlpatterns = [
    # Cases endpoints
    path("", views.CaseListView.as_view()),
    path("<str:pk>/", views.CaseDetailView.as_view()),
    path("comment/<str:pk>/", views.CaseCommentView.as_view()),
    path("attachment/<str:pk>/", views.CaseAttachmentView.as_view()),

    # Solutions (Knowledge Base) endpoints
    path("solutions/", solution_views.SolutionListView.as_view(), name="solutions_list"),
    path("solutions/<str:pk>/", solution_views.SolutionDetailView.as_view(), name="solution_detail"),
    path("solutions/<str:pk>/publish/", solution_views.SolutionPublishView.as_view(), name="solution_publish"),
    path("solutions/<str:pk>/unpublish/", solution_views.SolutionUnpublishView.as_view(), name="solution_unpublish"),
]
