from django.urls import path
from common import api_views


app_name = "api_common"


urlpatterns = [
    path("dashboard/", api_views.ApiHomeView.as_view()),
    path("auth/register/", api_views.RegistrationView.as_view()),
    path("auth/login/", api_views.LoginView.as_view()),
    path("auth/validate-subdomain/", api_views.check_sub_domain),
    path("profile/", api_views.ProfileView.as_view()),
    path("users/get_teams_and_users/", api_views.GetTeamsAndUsersView.as_view()),
    path("profile/change-password/", api_views.ChangePasswordView.as_view()),
    path("auth/forgot-password/", api_views.ForgotPasswordView.as_view()),
    path("auth/reset-password/", api_views.ResetPasswordView.as_view()),
    path("users/", api_views.UsersListView.as_view()),
    path("users/<int:pk>/", api_views.UserDetailView.as_view()),
    path("documents/", api_views.DocumentListView.as_view()),
]
