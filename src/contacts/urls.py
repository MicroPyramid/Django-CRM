from django.urls import path
from contacts import views

app_name = "api_contacts"

urlpatterns = [
    path("", views.ContactsListView.as_view()),
    path("<int:pk>/", views.ContactDetailView.as_view()),
    path("comment/<int:pk>/", views.ContactCommentView.as_view()),
    path("attachment/<int:pk>/", views.ContactAttachmentView.as_view()),
]
