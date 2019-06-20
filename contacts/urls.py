from django.urls import path

from contacts.views import AddAttachmentsView
from contacts.views import AddCommentView
from contacts.views import ContactDetailView
from contacts.views import ContactsListView
from contacts.views import CreateContactView
from contacts.views import DeleteAttachmentsView
from contacts.views import DeleteCommentView
from contacts.views import GetContactsView
from contacts.views import RemoveContactView
from contacts.views import UpdateCommentView
from contacts.views import UpdateContactView

app_name = "contacts"


urlpatterns = [
    path("list/", ContactsListView.as_view(), name="list"),
    path("create/", CreateContactView.as_view(), name="add_contact"),
    path("<int:pk>/view/", ContactDetailView.as_view(), name="view_contact"),
    path("<int:pk>/edit/", UpdateContactView.as_view(), name="edit_contact"),
    path("<int:pk>/delete/", RemoveContactView.as_view(), name="remove_contact"),
    path("get/list/", GetContactsView.as_view(), name="get_contacts"),
    path("comment/add/", AddCommentView.as_view(), name="add_comment"),
    path("comment/edit/", UpdateCommentView.as_view(), name="edit_comment"),
    path("comment/remove/", DeleteCommentView.as_view(), name="remove_comment"),
    path("attachment/add/", AddAttachmentsView.as_view(), name="add_attachment"),
    path(
        "attachment/remove/", DeleteAttachmentsView.as_view(), name="remove_attachment",
    ),
]
