from django.urls import path

from accounts.views import AccountDeleteView
from accounts.views import AccountDetailView
from accounts.views import AccountsListView
from accounts.views import AccountUpdateView
from accounts.views import AddAttachmentView
from accounts.views import AddCommentView
from accounts.views import CreateAccountView
from accounts.views import DeleteAttachmentsView
from accounts.views import DeleteCommentView
from accounts.views import UpdateCommentView

app_name = "accounts"

urlpatterns = [
    path("list/", AccountsListView.as_view(), name="list"),
    path("create/", CreateAccountView.as_view(), name="new_account"),
    path("<int:pk>/view/", AccountDetailView.as_view(), name="view_account"),
    path("<int:pk>/edit/", AccountUpdateView.as_view(), name="edit_account"),
    path("<int:pk>/delete/", AccountDeleteView.as_view(), name="remove_account"),
    path("comment/add/", AddCommentView.as_view(), name="add_comment"),
    path("comment/edit/", UpdateCommentView.as_view(), name="edit_comment"),
    path("comment/remove/", DeleteCommentView.as_view(), name="remove_comment"),
    path("attachment/add/", AddAttachmentView.as_view(), name="add_attachment"),
    path(
        "attachment/remove/", DeleteAttachmentsView.as_view(), name="remove_attachment",
    ),
]
