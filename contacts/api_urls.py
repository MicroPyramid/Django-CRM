from django.urls import path
from contacts import api_views

app_name = "api_contacts"

urlpatterns = [
    path("", api_views.ContactsListView.as_view()),
    path("<int:pk>/", api_views.ContactDetailView.as_view()),
    path("comment/<int:pk>/", api_views.ContactCommentView.as_view()),
    path("attachment/<int:pk>/", api_views.ContactAttachmentView.as_view()),
]
