from django.urls import path
from rest_framework_simplejwt import views as jwt_views

from common import views

app_name = "api_common"


urlpatterns = [
    path("dashboard/", views.ApiHomeView.as_view()),

    # JWT Authentication endpoints for SvelteKit integration
    path("auth/login/", views.LoginView.as_view(), name="login"),
    path("auth/register/", views.RegisterView.as_view(), name="register"),
    path(
        "auth/refresh-token/",
        views.OrgAwareTokenRefreshView.as_view(),
        name="token_refresh",
    ),
    path("auth/me/", views.MeView.as_view(), name="me"),
    path("auth/profile/", views.ProfileDetailView.as_view(), name="profile_detail"),
    path("auth/switch-org/", views.OrgSwitchView.as_view(), name="switch_org"),

    # GoogleLoginView
    path("auth/google/", views.GoogleLoginView.as_view()),

    # Organization and profile management
    path("org/", views.OrgProfileCreateView.as_view()),
    path("org/<str:pk>/", views.OrgUpdateView.as_view()),
    path("profile/", views.ProfileView.as_view()),

    # User management
    path("users/get-teams-and-users/", views.GetTeamsAndUsersView.as_view()),
    path("users/", views.UsersListView.as_view()),
    path("user/<str:pk>/", views.UserDetailView.as_view()),
    path("user/<str:pk>/status/", views.UserStatusView.as_view()),

    # Documents
    path("documents/", views.DocumentListView.as_view()),
    path("documents/<str:pk>/", views.DocumentDetailView.as_view()),

    # API Settings
    path("api-settings/", views.DomainList.as_view()),
    path("api-settings/<str:pk>/", views.DomainDetailView.as_view()),

    # Activities (for dashboard recent activities)
    path("activities/", views.ActivityListView.as_view(), name="activities"),

    # Teams (merged from teams app)
    path("teams/", views.TeamsListView.as_view()),
    path("teams/<str:pk>/", views.TeamsDetailView.as_view()),
]
