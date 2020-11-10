from django.urls import path
from contacts import api_views

app_name = "api_contacts"

urlpatterns = [
    path("", api_views.ContactsListView.as_view()),
    path("<int:pk>/", api_views.ContactDetailView.as_view(), name="view_contact"),
]
