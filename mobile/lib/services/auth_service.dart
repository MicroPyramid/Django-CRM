import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:jwt_decoder/jwt_decoder.dart';
import '../config/api_config.dart';
import '../data/models/auth_response.dart';
import 'api_service.dart';

/// Authentication service for BottleCRM
///
/// Handles Google Sign-In using ID token flow (same as old app),
/// token storage, and authentication state management.
class AuthService {
  static final AuthService _instance = AuthService._internal();
  factory AuthService() => _instance;
  AuthService._internal();

  // Initialize GoogleSignIn instance (singleton in v7.1.1)
  final GoogleSignIn _googleSignIn = GoogleSignIn.instance;
  final ApiService _apiService = ApiService();

  // Storage keys
  static const String _accessTokenKey = 'jwt_token';
  static const String _refreshTokenKey = 'refresh_token';
  static const String _userKey = 'user_data';
  static const String _organizationsKey = 'organizations';
  static const String _selectedOrgKey = 'selected_organization';

  // State
  String? _accessToken;
  String? _refreshToken;
  AuthUser? _currentUser;
  List<Organization>? _organizations;
  Organization? _selectedOrganization;

  // Getters
  bool get isLoggedIn => _accessToken != null && !_isTokenExpired;
  AuthUser? get currentUser => _currentUser;
  List<Organization>? get organizations => _organizations;
  Organization? get selectedOrganization => _selectedOrganization;
  String? get accessToken => _accessToken;

  /// Check if user needs to select an organization
  bool get needsOrgSelection =>
      isLoggedIn &&
      _organizations != null &&
      _organizations!.isNotEmpty &&
      _selectedOrganization == null;

  bool get _isTokenExpired {
    if (_accessToken == null) return true;
    try {
      return JwtDecoder.isExpired(_accessToken!);
    } catch (e) {
      return true;
    }
  }

  /// Initialize the auth service - call on app startup
  Future<void> initialize() async {
    debugPrint('AuthService: Initializing...');

    // Initialize Google Sign-In (required in v7.1.1)
    try {
      await _googleSignIn.initialize();
      debugPrint('AuthService: Google Sign-In initialized successfully');
    } catch (e) {
      debugPrint('AuthService: Google Sign-In initialization failed: $e');
    }

    await _loadFromStorage();

    // Sync token with ApiService
    if (_accessToken != null) {
      _apiService.setAccessToken(_accessToken);
    }
    if (_selectedOrganization != null) {
      _apiService.setOrganizationId(_selectedOrganization!.id);
    }

    debugPrint('AuthService: Initialized, isLoggedIn: $isLoggedIn');
  }

  /// Sign in with Google using ID token flow (same as old app)
  Future<bool> signInWithGoogle() async {
    try {
      debugPrint('AuthService: Initiating Google Sign-In...');

      // Check if platform supports authenticate method
      if (!_googleSignIn.supportsAuthenticate()) {
        debugPrint('AuthService: Platform does not support authenticate method');
        return false;
      }

      // Authenticate with Google (v7.1.1 method)
      final googleUser = await _googleSignIn.authenticate();

      debugPrint('AuthService: Authentication successful');
      debugPrint('AuthService: User email: ${googleUser.email}');

      // Get authentication token from Google
      final authentication = googleUser.authentication;
      final idToken = authentication.idToken;

      if (idToken == null) {
        debugPrint('AuthService: Failed to get ID token');
        return false;
      }

      debugPrint('AuthService: Got ID token, sending to backend...');

      // Send Google ID token to backend
      final response = await _apiService.post(
        ApiConfig.googleLogin,
        {'idToken': idToken},
        requiresAuth: false,
      );

      if (!response.success || response.data == null) {
        debugPrint('AuthService: Backend authentication failed: ${response.message}');
        return false;
      }

      debugPrint('AuthService: Backend returned tokens, storing...');

      // Handle the response
      await _handleAuthResponse(response.data!);

      return true;
    } catch (e, stack) {
      debugPrint('AuthService: Google Sign-In error: $e');
      debugPrint('Stack: $stack');
      return false;
    }
  }

  /// Handle authentication response from backend
  Future<void> _handleAuthResponse(Map<String, dynamic> data) async {
    // Backend returns JWTtoken (matching old app response format)
    _accessToken = data['JWTtoken'] as String?;

    if (data['user'] != null) {
      final userData = data['user'] as Map<String, dynamic>;
      _currentUser = AuthUser(
        id: userData['id'] as String,
        email: userData['email'] as String,
        name: userData['name'] as String?,
        profilePic: userData['profileImage'] as String?,
      );
    }

    if (data['organizations'] != null) {
      _organizations = (data['organizations'] as List<dynamic>)
          .map((org) => Organization.fromJson(org as Map<String, dynamic>))
          .toList();
    }

    // Clear any previously selected organization on fresh login
    _selectedOrganization = null;

    // Sync with ApiService
    _apiService.setAccessToken(_accessToken);
    _apiService.setOrganizationId(null);

    // Persist to storage (including clearing selected org)
    await _saveToStorage();
    await _clearSelectedOrganization();

    debugPrint('AuthService: Auth response handled, user: ${_currentUser?.email}');
    debugPrint('AuthService: Organizations: ${_organizations?.length ?? 0}');
  }

  /// Refresh the access token
  Future<bool> refreshAccessToken() async {
    if (_refreshToken == null) {
      debugPrint('AuthService: No refresh token available');
      return false;
    }

    try {
      debugPrint('AuthService: Refreshing access token...');

      final response = await _apiService.post(
        ApiConfig.refreshToken,
        {'refresh': _refreshToken},
        requiresAuth: false,
      );

      if (!response.success || response.data == null) {
        debugPrint('AuthService: Token refresh failed: ${response.message}');
        return false;
      }

      _accessToken = response.data!['access'] as String?;
      _refreshToken = response.data!['refresh'] as String?;

      _apiService.setAccessToken(_accessToken);
      await _saveToStorage();

      debugPrint('AuthService: Token refreshed successfully');
      return true;
    } catch (e) {
      debugPrint('AuthService: Token refresh error: $e');
      return false;
    }
  }

  /// Select an organization and get new tokens with org context
  Future<bool> selectOrganization(Organization org) async {
    try {
      debugPrint('AuthService: Switching to organization: ${org.name}...');

      // Call switch-org API to get new tokens with org context
      final response = await _apiService.post(
        ApiConfig.switchOrg,
        {'org_id': org.id},
        requiresAuth: true,
      );

      if (!response.success || response.data == null) {
        debugPrint('AuthService: Switch org failed: ${response.message}');
        return false;
      }

      // Update tokens from response
      _accessToken = response.data!['access_token'] as String?;
      _refreshToken = response.data!['refresh_token'] as String?;

      // Update selected organization
      _selectedOrganization = org;

      // Sync with ApiService
      _apiService.setAccessToken(_accessToken);
      _apiService.setOrganizationId(org.id);

      // Persist to storage
      await _saveToStorage();
      await _saveSelectedOrganization();

      debugPrint('AuthService: Switched to organization: ${org.name}');
      return true;
    } catch (e) {
      debugPrint('AuthService: Switch org error: $e');
      return false;
    }
  }

  /// Sign out and clear all stored data
  Future<void> signOut() async {
    debugPrint('AuthService: Signing out...');

    _accessToken = null;
    _refreshToken = null;
    _currentUser = null;
    _organizations = null;
    _selectedOrganization = null;

    _apiService.clearAuth();

    await _clearStorage();

    debugPrint('AuthService: Signed out');
  }

  /// Load authentication state from storage
  Future<void> _loadFromStorage() async {
    try {
      final prefs = await SharedPreferences.getInstance();

      _accessToken = prefs.getString(_accessTokenKey);
      _refreshToken = prefs.getString(_refreshTokenKey);

      final userJson = prefs.getString(_userKey);
      if (userJson != null) {
        final userData = jsonDecode(userJson) as Map<String, dynamic>;
        _currentUser = AuthUser(
          id: userData['id'] as String,
          email: userData['email'] as String,
          name: userData['name'] as String?,
          profilePic: userData['profileImage'] as String?,
        );
      }

      final orgsJson = prefs.getString(_organizationsKey);
      if (orgsJson != null) {
        _organizations = (jsonDecode(orgsJson) as List<dynamic>)
            .map((org) => Organization.fromJson(org as Map<String, dynamic>))
            .toList();
      }

      final selectedOrgJson = prefs.getString(_selectedOrgKey);
      if (selectedOrgJson != null) {
        _selectedOrganization =
            Organization.fromJson(jsonDecode(selectedOrgJson) as Map<String, dynamic>);
      }

      debugPrint('AuthService: Loaded from storage, user: ${_currentUser?.email}');
    } catch (e) {
      debugPrint('AuthService: Load from storage error: $e');
    }
  }

  /// Save authentication state to storage
  Future<void> _saveToStorage() async {
    try {
      final prefs = await SharedPreferences.getInstance();

      if (_accessToken != null) {
        await prefs.setString(_accessTokenKey, _accessToken!);
      }
      if (_refreshToken != null) {
        await prefs.setString(_refreshTokenKey, _refreshToken!);
      }
      if (_currentUser != null) {
        await prefs.setString(_userKey, jsonEncode({
          'id': _currentUser!.id,
          'email': _currentUser!.email,
          'name': _currentUser!.name,
          'profileImage': _currentUser!.profilePic,
        }));
      }
      if (_organizations != null) {
        await prefs.setString(
          _organizationsKey,
          jsonEncode(_organizations!.map((o) => o.toJson()).toList()),
        );
      }

      debugPrint('AuthService: Saved to storage');
    } catch (e) {
      debugPrint('AuthService: Save to storage error: $e');
    }
  }

  /// Save selected organization
  Future<void> _saveSelectedOrganization() async {
    if (_selectedOrganization != null) {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_selectedOrgKey, jsonEncode(_selectedOrganization!.toJson()));
    }
  }

  /// Clear selected organization from storage
  Future<void> _clearSelectedOrganization() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_selectedOrgKey);
  }

  /// Clear all stored authentication data
  Future<void> _clearStorage() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(_accessTokenKey);
      await prefs.remove(_refreshTokenKey);
      await prefs.remove(_userKey);
      await prefs.remove(_organizationsKey);
      await prefs.remove(_selectedOrgKey);

      debugPrint('AuthService: Storage cleared');
    } catch (e) {
      debugPrint('AuthService: Clear storage error: $e');
    }
  }
}
