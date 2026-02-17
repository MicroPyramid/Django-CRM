from django.urls import path

from common.views.auth_views import (
    GoogleIdTokenView,
    GoogleOAuthCallbackView,
    LoginView,
    MeView,
    OrgAwareTokenRefreshView,
    OrgSwitchView,
    RegisterView,
)
from common.views.dashboard_views import ActivityListView, ApiHomeView
from common.views.document_views import DocumentDetailView, DocumentListView
from common.views.organization_views import (
    OrgProfileCreateView,
    OrgUpdateView,
    ProfileDetailView,
    ProfileView,
)
from common.views.settings_views import DomainDetailView, DomainList
from common.views.org_settings_views import OrgSettingsView
from common.views.tags_views import TagsDetailView, TagsListView, TagsRestoreView
from common.views.team_views import TeamsDetailView, TeamsListView
from common.views.user_views import (
    GetTeamsAndUsersView,
    UserDetailView,
    UsersListView,
    UserStatusView,
)

app_name = "api_common"


urlpatterns = [
    path("dashboard/", ApiHomeView.as_view()),
    # JWT Authentication endpoints for SvelteKit integration
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/register/", RegisterView.as_view(), name="register"),
    path(
        "auth/refresh-token/",
        OrgAwareTokenRefreshView.as_view(),
        name="token_refresh",
    ),
    path("auth/me/", MeView.as_view(), name="me"),
    path("auth/profile/", ProfileDetailView.as_view(), name="profile_detail"),
    path("auth/switch-org/", OrgSwitchView.as_view(), name="switch_org"),
    # Google OAuth callback with PKCE (secure implementation)
    path("auth/google/callback/", GoogleOAuthCallbackView.as_view()),
    # Google ID token auth for mobile apps
    path("auth/google/", GoogleIdTokenView.as_view(), name="google_id_token"),
    # Organization and profile management
    path("org/", OrgProfileCreateView.as_view()),
    path("org/settings/", OrgSettingsView.as_view(), name="org_settings"),
    path("org/<str:pk>/", OrgUpdateView.as_view()),
    path("profile/", ProfileView.as_view()),
    # User management
    path("users/get-teams-and-users/", GetTeamsAndUsersView.as_view()),
    path("users/", UsersListView.as_view()),
    path("user/<str:pk>/", UserDetailView.as_view()),
    path("user/<str:pk>/status/", UserStatusView.as_view()),
    # Documents
    path("documents/", DocumentListView.as_view()),
    path("documents/<str:pk>/", DocumentDetailView.as_view()),
    # API Settings
    path("api-settings/", DomainList.as_view()),
    path("api-settings/<str:pk>/", DomainDetailView.as_view()),
    # Activities (for dashboard recent activities)
    path("activities/", ActivityListView.as_view(), name="activities"),
    # Teams (merged from teams app)
    path("teams/", TeamsListView.as_view()),
    path("teams/<str:pk>/", TeamsDetailView.as_view()),
    # Tags
    path("tags/", TagsListView.as_view()),
    path("tags/<str:pk>/", TagsDetailView.as_view()),
    path("tags/<str:pk>/restore/", TagsRestoreView.as_view()),
]
