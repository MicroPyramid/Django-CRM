from django.urls import path

from contacts import views

app_name = "api_contacts"

urlpatterns = [
    path("", views.ContactsListView.as_view()),
    path("<str:pk>/", views.ContactDetailView.as_view()),
    path("comment/<str:pk>/", views.ContactCommentView.as_view()),
    path("attachment/<str:pk>/", views.ContactAttachmentView.as_view()),
]
 