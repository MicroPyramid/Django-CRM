from django.urls import path
from leads import api_views

app_name = "api_leads"

urlpatterns = [
    path(
        "create-from-site/",
        api_views.CreateLeadFromSite.as_view(),
        name="create_lead_from_site",
    ),
    path("", api_views.LeadListView.as_view()),
    path("<int:pk>/", api_views.LeadDetailView.as_view()),
    path("upload/", api_views.LeadUploadView.as_view()),
    path("comment/<int:pk>/", api_views.LeadCommentView.as_view()),
    path("attachment/<int:pk>/", api_views.LeadAttachmentView.as_view()),
]
