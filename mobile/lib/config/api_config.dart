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
  static const String _developmentUrl = 'https://msi-8000.rcdev.in';

  /// Production API URL
  static const String _productionUrl = 'https://api.bottlecrm.io';

  /// Get the current base URL based on build mode
  static String get baseUrl => kDebugMode ? _developmentUrl : _productionUrl;

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

  /// Get current user info
  static String get me => '$apiBaseUrl/auth/me/';

  /// Get user profile with org details
  static String get profile => '$apiBaseUrl/auth/profile/';

  /// Switch organization context
  static String get switchOrg => '$apiBaseUrl/auth/switch-org/';

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

  /// Tasks management
  static String get tasks => '$apiBaseUrl/tasks/';

  /// Tickets (support tickets) management
  static String get tickets => '$apiBaseUrl/cases/';

  /// Ticket detail (retrieve / update / delete / add comment)
  static String ticketDetail(String id) => '$apiBaseUrl/cases/$id/';

  /// Ticket comment (single — for delete or status checks)
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

  /// Time summary for a ticket — totals + per-profile breakdown.
  static String ticketTimeSummary(String id) =>
      '$apiBaseUrl/cases/$id/time-summary/';

  /// Stop a running timer by entry id (entry-scoped, not case-scoped).
  static String timeEntryStop(String entryId) =>
      '$apiBaseUrl/time-entries/$entryId/stop/';

  /// Solutions (Knowledge Base) — list/create.
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

  // ==========================================================================
  // REQUEST CONFIGURATION
  // ==========================================================================

  /// Connection timeout duration
  static const Duration connectTimeout = Duration(seconds: 30);

  /// Receive timeout duration
  static const Duration receiveTimeout = Duration(seconds: 30);

  /// Default request headers
  static Map<String, String> get defaultHeaders => {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  };
}
