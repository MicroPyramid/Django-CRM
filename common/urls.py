from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.urls import path

from common.views import (
    ChangePasswordView,
    CompanyLoginView,
    CreateUserView,
    DocumentDeleteView,
    DocumentDetailView,
    DocumentListView,
    ForgotPasswordView,
    HomeView,
    # LoginView,
    LogoutView,
    PasswordResetView,
    ProfileView,
    RegistrationView,
    UpdateUserView,
    UserDeleteView,
    UserDetailView,
    UsersListView,
    activate_user,
    add_api_settings,
    add_comment,
    api_settings,
    change_passsword_by_admin,
    change_user_status,
    check_sub_domain,
    create_lead_from_site,
    delete_api_settings,
    document_create,
    document_update,
    download_attachment,
    download_document,
    edit_comment,
    get_teams_and_users,
    google_login,
    landing_page,
    remove_comment,
    resend_activation_link,
    update_api_settings,
    view_api_settings,
)

app_name = "common"


urlpatterns = [
    path("", landing_page, name="landing_page"),
    path("dashboard/", HomeView.as_view(), name="dashboard"),
    path("login/", CompanyLoginView.as_view(), name="login"),
    #     path('login/', LoginView.as_view(), name='login'),
    path("register/", RegistrationView.as_view(), name="register"),
    path("auth/domain/", check_sub_domain, name="check_domain"),
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
    path("documents/", DocumentListView.as_view(), name="doc_list"),
    path("documents/create/", document_create, name="create_doc"),
    path("documents/<int:pk>/edit/", document_update, name="edit_doc"),
    path("documents/<int:pk>/view/", DocumentDetailView.as_view(), name="view_doc"),
    path("documents/<int:pk>/delete/", DocumentDeleteView.as_view(), name="remove_doc"),
    # download
    path("documents/<int:pk>/download/", download_document, name="download_document"),
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
    # settings
    path("api/settings/", api_settings, name="api_settings"),
    path("api/settings/add/", add_api_settings, name="add_api_settings"),
    path("api/settings/<int:pk>/", view_api_settings, name="view_api_settings"),
    path(
        "api/settings/<int:pk>/update/", update_api_settings, name="update_api_settings"
    ),
    path(
        "api/settings/<int:pk>/delete/", delete_api_settings, name="delete_api_settings"
    ),
    path(
        "change-password-by-admin/",
        change_passsword_by_admin,
        name="change_passsword_by_admin",
    ),
    path("google/login/", google_login, name="google_login"),
    path("create-lead-from-site/", create_lead_from_site, name="create_lead_from_site"),
    # user activate link
    path(
        "activate-user/<uidb64>/<token>/<activation_key>/",
        activate_user,
        name="activate_user",
    ),
    path(
        "resend_activation_link/<userId>/",
        resend_activation_link,
        name="resend_activation_link",
    ),
    path("get_teams_and_users/", get_teams_and_users, name="get_teams_and_users"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
