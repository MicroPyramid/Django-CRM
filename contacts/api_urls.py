from django.urls import path
from contacts import api_views

app_name = 'api_contacts'

urlpatterns = [
    path("contacts-list/", api_views.ContactsListView.as_view()),
    path("create/", api_views.CreateContactView.as_view(), name="add_contact"),
    path("<int:pk>/view/", api_views.ContactDetailView.as_view(), name="view_contact"),
    path("<int:pk>/edit/", api_views.UpdateContactView.as_view(), name="edit_contact"),
    path("<int:pk>/delete/", api_views.RemoveContactView.as_view(), name="remove_contact"),
]
