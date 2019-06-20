from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.urls import path

from common.views import add_comment
from common.views import change_user_status
from common.views import ChangePasswordView
from common.views import CreateUserView
from common.views import DocumentCreateView
from common.views import DocumentDeleteView
from common.views import DocumentDetailView
from common.views import DocumentListView
from common.views import download_attachment
from common.views import download_document
from common.views import edit_comment
from common.views import ForgotPasswordView
from common.views import google_login
from common.views import HomeView
from common.views import LoginView
from common.views import LogoutView
from common.views import PasswordResetView
from common.views import ProfileView
from common.views import remove_comment
from common.views import UpdateDocumentView
from common.views import UpdateUserView
from common.views import UserDeleteView
from common.views import UserDetailView
from common.views import UsersListView


app_name = "common"


urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("login/", LoginView.as_view(), name="login"),
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot_password"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("change-password/", ChangePasswordView.as_view(), name="change_password"),
    path("profile/", ProfileView.as_view(), name="profile"),
    # User views
    path("users/list/", UsersListView.as_view(), name="users_list"),
    path("users/create/", CreateUserView.as_view(), name="create_user"),
    path("users/<int:pk>/edit/", UpdateUserView.as_view(), name="edit_user"),
    path("users/<int:pk>/view/", UserDetailView.as_view(), name="view_user"),
    path("users/<int:pk>/delete/", UserDeleteView.as_view(), name="remove_user"),
    path("password-reset/", PasswordResetView.as_view(), name="password_reset"),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    # Document
    path("documents/list/", DocumentListView.as_view(), name="doc_list"),
    path("documents/create/", DocumentCreateView.as_view(), name="create_doc"),
    path("documents/<int:pk>/edit/", UpdateDocumentView.as_view(), name="edit_doc"),
    path("documents/<int:pk>/view/", DocumentDetailView.as_view(), name="view_doc"),
    path(
        "documents/<int:pk>/delete/",
        DocumentDeleteView.as_view(), name="remove_doc",
    ),
    # download
    path(
        "documents/<int:pk>/download/",
        download_document, name="download_document",
    ),
    # download_attachment
    path(
        "attachments/<int:pk>/download/",
        download_attachment,
        name="download_attachment",
    ),
    path("user/status/<int:pk>/", change_user_status, name="change_user_status"),
    path("comment/add/", add_comment, name="add_comment"),
    path("comment/<int:pk>/edit/", edit_comment, name="edit_comment"),
    path("comment/remove/", remove_comment, name="remove_comment"),
    path("google/login/", google_login, name="google_login"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
