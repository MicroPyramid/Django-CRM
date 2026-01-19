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
  static const String _developmentUrl = 'https://pc-8000.furrypari.com';

  /// Production API URL
  static const String _productionUrl = 'https://api.bottlecrm.io';

  /// Get the current base URL based on build mode
  static String get baseUrl => kDebugMode ? _developmentUrl : _productionUrl;

  /// API base path
  static String get apiBaseUrl => '$baseUrl/api';

  // ==========================================================================
  // AUTHENTICATION ENDPOINTS
  // ==========================================================================

  /// Email/password login
  static String get login => '$apiBaseUrl/auth/login/';

  /// Google Sign-In with ID token (same as old app)
  static String get googleLogin => '$apiBaseUrl/auth/google/';

  /// Refresh JWT token
  static String get refreshToken => '$apiBaseUrl/auth/refresh-token/';

  /// Get current user info
  static String get me => '$apiBaseUrl/auth/me/';

  /// Get user profile with org details
  static String get profile => '$apiBaseUrl/auth/profile/';

  /// Switch organization context
  static String get switchOrg => '$apiBaseUrl/auth/switch-org/';

  /// User registration
  static String get register => '$apiBaseUrl/auth/register/';

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
  static String leadComment(String commentId) => '$apiBaseUrl/leads/comment/$commentId/';

  /// Contacts management
  static String get contacts => '$apiBaseUrl/contacts/';

  /// Accounts (companies) management
  static String get accounts => '$apiBaseUrl/accounts/';

  /// Opportunities (deals) management
  static String get opportunities => '$apiBaseUrl/opportunities/';

  /// Tasks management
  static String get tasks => '$apiBaseUrl/tasks/';

  /// Cases (support tickets) management
  static String get cases => '$apiBaseUrl/cases/';

  /// Invoices management
  static String get invoices => '$apiBaseUrl/invoices/';

  // ==========================================================================
  // USERS & TAGS ENDPOINTS
  // ==========================================================================

  /// Get teams and users (for assignment dropdowns)
  static String get teamsAndUsers => '$apiBaseUrl/users/get-teams-and-users/';

  /// Tags management
  static String get tags => '$apiBaseUrl/tags/';

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
