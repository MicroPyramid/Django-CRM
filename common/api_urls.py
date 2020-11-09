from django.urls import path
from common import api_views


app_name = "api_common"


urlpatterns = [
    path("dashboard/", api_views.ApiHomeView.as_view()),
    path("registration/", api_views.RegistrationView.as_view()),
    path("login/", api_views.LoginView.as_view()),
    path("validate-subdomain/", api_views.check_sub_domain),
    path("profile/", api_views.ProfileView.as_view()),
    path("get_teams_and_users/", api_views.GetTeamsAndUsersView.as_view()),
    path("change-password/", api_views.ChangePasswordView.as_view(), name="change_password"),
    path("forgot-password/", api_views.ForgotPasswordView.as_view()),
    path("reset-password/", api_views.ResetPasswordView.as_view(), name='reset_password'),
    path("users/list/", api_views.UsersListView.as_view(), name="users_list"),
    path("users/<int:pk>/view/", api_views.UserDetailView.as_view(), name="view_user"),
    # path("users/create/", api_views.CreateUserView.as_view(), name="create_user"),
    path("documents/create/", api_views.DocumentCreate.as_view(), name="create_doc"),
    #To be checked
    path("users/<int:pk>/delete/", api_views.UserDeleteView.as_view(), name="remove_user"),
]
