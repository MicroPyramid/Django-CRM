from django.urls import path

from leads import views
from .import views

app_name = "api_leads"

urlpatterns = [
    path(
        "create-from-site/",
        views.CreateLeadFromSite.as_view(),
        name="create_lead_from_site",
    ),
    path("", views.LeadListView.as_view()),
    path("<str:pk>/", views.LeadDetailView.as_view()),
    path("upload/", views.LeadUploadView.as_view()),
    path("comment/<str:pk>/", views.LeadCommentView.as_view()),
    path("attachment/<str:pk>/", views.LeadAttachmentView.as_view()),
    path("companies",views.CompaniesView.as_view()),
    path('company/<str:pk>', views.CompanyDetail.as_view()),
]
