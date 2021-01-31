from django.urls import path
from leads import api_views

app_name = "api_leads"

urlpatterns = [
    path("", api_views.LeadListView.as_view()),
    path("<int:pk>/", api_views.LeadDetailView.as_view()),
    path("upload/", api_views.LeadUploadView.as_view()),
    path("comment/<int:pk>/", api_views.LeadCommentView.as_view()),
    path("attachment/<int:pk>/", api_views.LeadAttachmentView.as_view()),
]
