from django.urls import path

from cases import views

app_name = "api_cases"

urlpatterns = [
    path("", views.CaseListView.as_view()),
    path("<str:pk>/", views.CaseDetailView.as_view()),
    path("comment/<str:pk>/", views.CaseCommentView.as_view()),
    path("attachment/<str:pk>/", views.CaseAttachmentView.as_view()),
]
