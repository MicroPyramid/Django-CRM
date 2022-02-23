from django.urls import path
from leads import views

app_name = "api_leads"

urlpatterns = [
    path(
        "create-from-site/",
        views.CreateLeadFromSite.as_view(),
        name="create_lead_from_site",
    ),
    path("", views.LeadListView.as_view()),
    path("<int:pk>/", views.LeadDetailView.as_view()),
    path("upload/", views.LeadUploadView.as_view()),
    path("comment/<int:pk>/", views.LeadCommentView.as_view()),
    path("attachment/<int:pk>/", views.LeadAttachmentView.as_view()),
]
