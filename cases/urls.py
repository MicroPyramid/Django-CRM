from django.urls import path

from cases import views

app_name = "api_cases"

urlpatterns = [
    path("", views.CaseListView.as_view()),
    path("<int:pk>/", views.CaseDetailView.as_view()),
    path("comment/<int:pk>/", views.CaseCommentView.as_view()),
    path("attachment/<int:pk>/", views.CaseAttachmentView.as_view()),
]
