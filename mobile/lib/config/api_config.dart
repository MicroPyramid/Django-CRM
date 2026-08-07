import 'package:flutter/foundation.dart';

/// API Configuration for BottleCRM
///
/// Provides centralized configuration for API endpoints.
/// Update [_developmentUrl] with your ngrok URL for development.
class ApiConfig {
  // ==========================================================================
  // BASE URLS - Update these for your environment
  // ==========================================================================

  /// Development API URL
  static const String _developmentUrl = 'https://pc-8000.rcdev.in';

  /// Production API URL
  static const String _productionUrl = 'https://api.bottlecrm.io';

  /// Public marketing site. Hosts the documents the app has to link to
  /// (`/terms-of-service`, `/privacy-policy`) rather than ship its own copies,
  /// which would drift the moment either is edited.
  static const String marketingSite = 'https://bottlecrm.io';

  /// Build-time override, so somebody self-hosting points a build at their own
  /// server without editing this file:
  ///
  ///     flutter build apk --release --dart-define=API_BASE_URL=https://crm.example.com
  ///
  /// Compile-time on purpose. A runtime setting would mean anything able to
  /// write the app's storage could redirect every request, and every JWT with
  /// it, to a server of its own choosing.
  static const String _baseUrlOverride = String.fromEnvironment('API_BASE_URL');

  /// Google's Web OAuth client, the audience the backend's `GOOGLE_CLIENT_ID`
  /// verifies against. Overridable the same way, because a self-hoster signs in
  /// against their own Google project:
  ///
  ///     --dart-define=GOOGLE_SERVER_CLIENT_ID=<id>.apps.googleusercontent.com
  ///
  /// Not a secret. A client id is public by design; the backend is what decides
  /// whether an ID token is acceptable.
  static const String googleServerClientId = String.fromEnvironment(
    'GOOGLE_SERVER_CLIENT_ID',
    defaultValue:
        '1072513761792-p59rct7b1c3go7l58e51r3geuqff2tfl.apps.googleusercontent.com',
  );

  /// The API host this build talks to.
  static final String baseUrl = resolveBaseUrl(
    override: _baseUrlOverride,
    isDebug: kDebugMode,
  );

  /// The override rules, separated from the build constants so both branches
  /// can be tested. `flutter test` runs one build, so a `--dart-define` the
  /// suite does not pass is a branch no test could otherwise reach.
  @visibleForTesting
  static String resolveBaseUrl({
    required String override,
    required bool isDebug,
  }) {
    if (override.isEmpty) {
      return isDebug ? _developmentUrl : _productionUrl;
    }
    // A trailing slash would produce `https://host//api`, and the resulting 404
    // on every request says nothing about the cause.
    final trimmed = override.endsWith('/')
        ? override.substring(0, override.length - 1)
        : override;
    // A release build talking plain HTTP puts every JWT on the wire in the
    // clear. Refusing loudly beats falling back to the default, which would
    // leave a self-hoster looking at somebody else's server and no explanation.
    // `http://` stays allowed in debug: that is how anyone runs against a local
    // Django.
    if (!isDebug && !trimmed.startsWith('https://')) {
      throw StateError(
        'API_BASE_URL must start with https:// in a release build. '
        'Got "$trimmed", which would send every token unencrypted.',
      );
    }
    return trimmed;
  }

  /// API base path
  static String get apiBaseUrl => '$baseUrl/api';

  // ==========================================================================
  // AUTHENTICATION ENDPOINTS
  // ==========================================================================

  /// Google Sign-In with ID token (same as old app)
  static String get googleLogin => '$apiBaseUrl/auth/google/';

  /// Request a passwordless sign-in code (OTP) by email
  static String get magicLinkRequest => '$apiBaseUrl/auth/magic-link/request/';

  /// Verify a 6-digit OTP code and exchange it for JWT tokens
  static String get magicLinkVerifyCode => '$apiBaseUrl/auth/magic-link/verify-code/';

  /// Refresh JWT token
  static String get refreshToken => '$apiBaseUrl/auth/refresh-token/';

  /// Sign out: blacklists the refresh token server-side. Needs no access
  /// token, which is what lets it work when the session has already expired.
  static String get logout => '$apiBaseUrl/auth/logout/';

  /// Get current user info
  static String get me => '$apiBaseUrl/auth/me/';

  /// Get user profile with org details (read; ProfileDetailView)
  static String get profile => '$apiBaseUrl/auth/profile/';

  /// Update user profile, only `phone` is editable per backend contract.
  /// Distinct endpoint from `profile` above (ProfileView vs ProfileDetailView).
  static String get profileUpdate => '$apiBaseUrl/profile/';

  /// Switch organization context
  static String get switchOrg => '$apiBaseUrl/auth/switch-org/';

  /// Create an organization and become its admin (OrgProfileCreateView).
  /// Needs a signed-in user but no org context, which is the point: the caller
  /// is someone who has none yet.
  static String get orgCreate => '$apiBaseUrl/org/';

  /// IANA zone names with their current UTC offsets, for the org form's
  /// timezone picker. Served rather than read from the device so both clients
  /// use one vocabulary (see `common/org_time.py`).
  static String get timezones => '$apiBaseUrl/org/timezones/';

  // ==========================================================================
  // DASHBOARD
  // ==========================================================================

  /// Dashboard summary data
  static String get dashboard => '$apiBaseUrl/dashboard/';

  // ==========================================================================
  // CRM ENDPOINTS
  // ==========================================================================

  /// Leads management
  static String get leads => '$apiBaseUrl/leads/';

  /// Lead comment (for update/delete)
  static String leadComment(String commentId) =>
      '$apiBaseUrl/leads/comment/$commentId/';

  /// Contacts management
  static String get contacts => '$apiBaseUrl/contacts/';

  /// Accounts (companies) management
  static String get accounts => '$apiBaseUrl/accounts/';

  /// Opportunities (deals) management
  static String get opportunities => '$apiBaseUrl/opportunities/';

  /// Opportunity comment (for update/delete)
  static String opportunityComment(String commentId) =>
      '$apiBaseUrl/opportunities/comment/$commentId/';

  /// Tasks management
  static String get tasks => '$apiBaseUrl/tasks/';

  /// Tickets (support tickets) management
  static String get tickets => '$apiBaseUrl/cases/';

  /// Ticket detail (retrieve / update / delete / add comment)
  static String ticketDetail(String id) => '$apiBaseUrl/cases/$id/';

  /// Ticket comment (single, for delete or status checks)
  static String ticketComment(String commentId) =>
      '$apiBaseUrl/cases/comment/$commentId/';

  /// Watch / unwatch a ticket (POST / DELETE).
  static String ticketWatch(String id) => '$apiBaseUrl/cases/$id/watch/';

  /// List watchers on a ticket.
  static String ticketWatchers(String id) =>
      '$apiBaseUrl/cases/$id/watchers/';

  /// Tickets the current user is watching.
  static String get ticketsWatching => '$apiBaseUrl/cases/watching/';

  /// Merge source ticket as duplicate INTO another ticket.
  static String ticketMerge(String sourceId, String intoId) =>
      '$apiBaseUrl/cases/$sourceId/merge/$intoId/';

  /// Reverse a prior merge. Called on the SOURCE id.
  static String ticketUnmerge(String sourceId) =>
      '$apiBaseUrl/cases/$sourceId/unmerge/';

  /// Parent/child tree rooted at the closest visible ancestor.
  static String ticketTree(String id) => '$apiBaseUrl/cases/$id/tree/';

  /// Link this ticket to a parent (or detach by sending null parent_id).
  static String ticketLinkParent(String id) =>
      '$apiBaseUrl/cases/$id/link/';

  /// Close this ticket and optionally its descendants.
  static String ticketCloseWithChildren(String id) =>
      '$apiBaseUrl/cases/$id/close-with-children/';

  /// Time entries for a ticket (GET list / POST manual entry).
  static String ticketTimeEntries(String id) =>
      '$apiBaseUrl/cases/$id/time-entries/';

  /// Start a running timer on a ticket.
  static String ticketTimerStart(String id) =>
      '$apiBaseUrl/cases/$id/time-entries/start/';

  /// Time summary for a ticket, totals + per-profile breakdown.
  static String ticketTimeSummary(String id) =>
      '$apiBaseUrl/cases/$id/time-summary/';

  /// Stop a running timer by entry id (entry-scoped, not case-scoped).
  static String timeEntryStop(String entryId) =>
      '$apiBaseUrl/time-entries/$entryId/stop/';

  /// Solutions (Knowledge Base). List/create.
  static String get solutions => '$apiBaseUrl/cases/solutions/';

  /// Solution detail (GET / PUT / DELETE).
  static String solutionDetail(String id) =>
      '$apiBaseUrl/cases/solutions/$id/';

  /// Publish a solution (must be status=approved).
  static String solutionPublish(String id) =>
      '$apiBaseUrl/cases/solutions/$id/publish/';

  /// Unpublish a solution.
  static String solutionUnpublish(String id) =>
      '$apiBaseUrl/cases/solutions/$id/unpublish/';

  /// Link a solution to a ticket (POST {solution_id}).
  static String ticketSolutionLink(String ticketId) =>
      '$apiBaseUrl/cases/$ticketId/solutions/';

  /// Unlink a solution from a ticket.
  static String ticketSolutionUnlink(String ticketId, String solutionId) =>
      '$apiBaseUrl/cases/$ticketId/solutions/$solutionId/';

  /// Solution suggestions for a ticket (typeahead by ticket context).
  static String ticketSolutionSuggestions(String ticketId) =>
      '$apiBaseUrl/cases/$ticketId/solution-suggestions/';

  /// Approvals inbox / per-case list. Query params: ?case=&state=&mine=
  static String get approvals => '$apiBaseUrl/cases/approvals/';

  /// Approve / reject / cancel an approval.
  static String approvalApprove(String id) =>
      '$apiBaseUrl/cases/approvals/$id/approve/';
  static String approvalReject(String id) =>
      '$apiBaseUrl/cases/approvals/$id/reject/';
  static String approvalCancel(String id) =>
      '$apiBaseUrl/cases/approvals/$id/cancel/';

  /// Request approval for a ticket.
  static String ticketRequestApproval(String ticketId) =>
      '$apiBaseUrl/cases/$ticketId/request-approval/';

  /// Analytics endpoints. All accept ?from=YYYY-MM-DD&to=YYYY-MM-DD plus
  /// optional ?priority=, ?agent=, ?team= filters.
  static String get analyticsFrt => '$apiBaseUrl/cases/analytics/frt/';
  static String get analyticsMttr => '$apiBaseUrl/cases/analytics/mttr/';
  static String get analyticsBacklog => '$apiBaseUrl/cases/analytics/backlog/';
  static String get analyticsAgents => '$apiBaseUrl/cases/analytics/agents/';
  static String get analyticsSla => '$apiBaseUrl/cases/analytics/sla/';

  /// Invoices management
  static String get invoices => '$apiBaseUrl/invoices/';

  // ==========================================================================
  // USERS & TAGS ENDPOINTS
  // ==========================================================================

  /// Get teams and users (for assignment dropdowns)
  static String get teamsAndUsers => '$apiBaseUrl/users/get-teams-and-users/';

  /// Tags management
  static String get tags => '$apiBaseUrl/tags/';

  /// Custom field definitions (per-org schema for entities like Case/Lead/...).
  /// Query with `?target_model=Case&active_only=true`.
  static String get customFieldDefinitions =>
      '$apiBaseUrl/custom-fields/';

  /// People in the org: GET lists active and inactive, POST invites.
  /// Admin-only server-side, 403 for everyone else on both verbs.
  static String get orgUsers => '$apiBaseUrl/users/';

  /// One person's role: PATCH `{"role": "ADMIN"|"USER"}`. Takes the USER id,
  /// not the profile id.
  static String orgUser(String userId) => '$apiBaseUrl/user/$userId/';

  /// Activate or deactivate: POST `{"status": "Active"|"Inactive"}`. Also the
  /// USER id. The server refuses to deactivate the last active admin.
  static String orgUserStatus(String userId) =>
      '$apiBaseUrl/user/$userId/status/';

  // ==========================================================================
  // REQUEST CONFIGURATION
  // ==========================================================================

  /// Connection timeout duration
  static const Duration connectTimeout = Duration(seconds: 30);

  /// Uploads get longer. A 25 MB attachment (the server's limit) does not
  /// finish in 30 seconds on a phone connection, and the timeout that fired
  /// would look like a server fault.
  static const Duration uploadTimeout = Duration(minutes: 3);

  /// Receive timeout duration
  static const Duration receiveTimeout = Duration(seconds: 30);

  /// Default request headers
  static Map<String, String> get defaultHeaders => {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  };
}
