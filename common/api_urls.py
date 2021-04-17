from django.urls import path
from common import api_views


app_name = "api_common"


urlpatterns = [
    path("dashboard/", api_views.ApiHomeView.as_view()),
    path("auth/register/", api_views.RegistrationView.as_view()),
    path("auth/login/", api_views.LoginView.as_view()),
    path("profile/", api_views.ProfileView.as_view()),
    path("users/get-teams-and-users/", api_views.GetTeamsAndUsersView.as_view()),
    path("profile/change-password/", api_views.ChangePasswordView.as_view()),
    path("auth/forgot-password/", api_views.ForgotPasswordView.as_view()),
    path(
        "auth/reset-password/<str:uid>/<str:token>/",
        api_views.ResetPasswordView.as_view(),
    ),
    path(
        "auth/activate-user/<str:uid>/<str:token>/<str:activation_key>/",
        api_views.ActivateUserView.as_view(),
    ),
    path("auth/resend-activation-link/", api_views.ResendActivationLinkView.as_view()),
    path("users/", api_views.UsersListView.as_view()),
    path("users/<int:pk>/", api_views.UserDetailView.as_view()),
    path("documents/", api_views.DocumentListView.as_view()),
    path("documents/<int:pk>/", api_views.DocumentDetailView.as_view()),
    path("api-settings/", api_views.DomainList.as_view()),
    path("api-settings/<int:pk>/", api_views.DomainDetailView.as_view()),
    path("users/<int:pk>/status/", api_views.UserStatusView.as_view()),
]
