from django.urls import path
from common import views


app_name = "api_common"


urlpatterns = [
    path("dashboard/", views.ApiHomeView.as_view()),
    path("auth/register/", views.RegistrationView.as_view()),
    path("auth/login/", views.LoginView.as_view()),
    path("profile/", views.ProfileView.as_view()),
    path("users/get-teams-and-users/", views.GetTeamsAndUsersView.as_view()),
    path("profile/change-password/", views.ChangePasswordView.as_view()),
    path("auth/forgot-password/", views.ForgotPasswordView.as_view()),
    path(
        "auth/reset-password/<str:uid>/<str:token>/",
        views.ResetPasswordView.as_view(),
    ),
    path(
        "auth/activate-user/<str:uid>/<str:token>/<str:activation_key>/",
        views.ActivateUserView.as_view(),
    ),
    path("auth/resend-activation-link/", views.ResendActivationLinkView.as_view()),
    path("users/", views.UsersListView.as_view()),
    path("users/<int:pk>/", views.UserDetailView.as_view()),
    path("documents/", views.DocumentListView.as_view()),
    path("documents/<int:pk>/", views.DocumentDetailView.as_view()),
    path("api-settings/", views.DomainList.as_view()),
    path("api-settings/<int:pk>/", views.DomainDetailView.as_view()),
    path("users/<int:pk>/status/", views.UserStatusView.as_view()),
]
