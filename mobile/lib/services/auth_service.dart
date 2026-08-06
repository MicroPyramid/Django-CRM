import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:jwt_decoder/jwt_decoder.dart';
import '../config/api_config.dart';
import '../data/models/auth_response.dart';
import 'api_service.dart';
import 'crash_reporting.dart';

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

    // Initialize Google Sign-In (required in v7.1.1).
    // serverClientId is the Web OAuth client (client_type: 3 in google-services.json)
    //. This is the audience the Django backend's GOOGLE_CLIENT_ID verifies against,
    // and it's what makes Android return a usable ID token.
    try {
      await _googleSignIn.initialize(
        serverClientId:
            '1072513761792-p59rct7b1c3go7l58e51r3geuqff2tfl.apps.googleusercontent.com',
      );
      debugPrint('AuthService: Google Sign-In initialized successfully');
    } catch (e) {
      debugPrint('AuthService: Google Sign-In initialization failed: $e');
    }

    await _loadFromStorage();

    // Wire auto-refresh BEFORE any network calls so the preemptive refresh
    // below, and every subsequent authenticated request, can hit the
    // refresh endpoint on 401.
    _apiService.setRefreshCallback(refreshAccessToken);

    // If the access token is already expired on launch but the refresh token
    // is still alive (14-day lifetime), refresh in-place. Without this the
    // user gets bounced to the login screen after every short app suspension
    // longer than the 1-hour access lifetime, even though their session is
    // still valid.
    if (_accessToken != null && _isTokenExpired && _refreshToken != null) {
      debugPrint('AuthService: Access token expired on launch, refreshing...');
      await refreshAccessToken();
    }

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
        debugPrint(
          'AuthService: Platform does not support authenticate method',
        );
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
      final response = await _apiService.post(ApiConfig.googleLogin, {
        'idToken': idToken,
      }, requiresAuth: false);

      if (!response.success || response.data == null) {
        debugPrint(
          'AuthService: Backend authentication failed: ${response.message}',
        );
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

  /// Request a 6-digit sign-in code by email (mobile OTP flow).
  ///
  /// Backend always returns 200 to prevent email enumeration, so a `true`
  /// return value means "the request was accepted," not "an email was sent."
  Future<bool> requestMagicCode(String email) async {
    try {
      debugPrint('AuthService: Requesting magic code for $email...');
      final response = await _apiService.post(
        ApiConfig.magicLinkRequest,
        {'email': email, 'delivery': 'code'},
        requiresAuth: false,
      );
      return response.success;
    } catch (e) {
      debugPrint('AuthService: requestMagicCode error: $e');
      return false;
    }
  }

  /// Verify a 6-digit OTP code and exchange it for JWT tokens.
  ///
  /// Response shape matches `UserDetailSerializer` (see backend
  /// `MagicLinkVerifyCodeView`), which is different from the Google sign-in
  /// shape, hence the separate parser instead of `_handleAuthResponse`.
  Future<bool> signInWithMagicCode({
    required String email,
    required String code,
  }) async {
    try {
      debugPrint('AuthService: Verifying magic code for $email...');
      final response = await _apiService.post(
        ApiConfig.magicLinkVerifyCode,
        {'email': email, 'code': code},
        requiresAuth: false,
      );

      if (!response.success || response.data == null) {
        debugPrint(
          'AuthService: Magic code verify failed: ${response.message}',
        );
        return false;
      }

      final data = response.data!;
      _accessToken = data['access_token'] as String?;
      _refreshToken = data['refresh_token'] as String?;

      final userData = data['user'] as Map<String, dynamic>?;
      if (userData != null) {
        _currentUser = AuthUser(
          id: userData['id'] as String,
          email: userData['email'] as String,
          name: userData['name'] as String?,
          profilePic: userData['profile_pic'] as String?,
        );
      }

      // `organizations` is a sibling of `user`, not a member of it. Reading it
      // from inside `user` found nothing, so a code sign-in ended with no org
      // list at all: the picker needs a non-empty list to appear, so it never
      // did, while the JWT quietly carried whichever org the server had picked.
      // The nested read is kept as a fallback in case an older build of the
      // API is on the other end.
      final orgsList =
          (data['organizations'] ?? userData?['organizations']) as List<dynamic>?;
      _organizations = orgsList
          ?.map((org) => Organization.fromJson(org as Map<String, dynamic>))
          .toList();

      // Backend returns `current_org` only when the user already belongs to an
      // org and its claim is baked into the JWT. Pre-select it so the user
      // skips org selection.
      final currentOrgData = data['current_org'] as Map<String, dynamic>?;
      if (currentOrgData != null && _organizations != null) {
        _selectedOrganization = _organizations!.firstWhere(
          (o) => o.id == currentOrgData['id'],
          orElse: () => Organization.fromJson(currentOrgData),
        );
      } else {
        _selectedOrganization = null;
      }

      _apiService.setAccessToken(_accessToken);
      _apiService.setOrganizationId(_selectedOrganization?.id);

      await _saveToStorage();
      if (_selectedOrganization != null) {
        await _saveSelectedOrganization();
      } else {
        await _clearSelectedOrganization();
      }

      debugPrint('AuthService: Magic code sign-in successful');
      await CrashReporting.applyFromAuth(this);
      return true;
    } catch (e, stack) {
      debugPrint('AuthService: signInWithMagicCode error: $e');
      debugPrint('Stack: $stack');
      return false;
    }
  }

  /// Handle authentication response from backend
  Future<void> _handleAuthResponse(Map<String, dynamic> data) async {
    // Backend returns JWTtoken (matching old app response format) and a
    // refresh_token alongside it, without the refresh token, the access
    // token would die in 1 hour with no way to refresh until the user picks
    // an org (which re-issues both via OrgSwitchView).
    _accessToken = data['JWTtoken'] as String?;
    _refreshToken = data['refresh_token'] as String?;

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

    debugPrint(
      'AuthService: Auth response handled, user: ${_currentUser?.email}',
    );
    debugPrint('AuthService: Organizations: ${_organizations?.length ?? 0}');

    await CrashReporting.applyFromAuth(this);
  }

  /// Refresh the access token
  Future<bool> refreshAccessToken() async {
    if (_refreshToken == null) {
      debugPrint('AuthService: No refresh token available');
      return false;
    }

    try {
      debugPrint('AuthService: Refreshing access token...');

      final response = await _apiService.post(ApiConfig.refreshToken, {
        'refresh': _refreshToken,
      }, requiresAuth: false);

      if (!response.success || response.data == null) {
        debugPrint('AuthService: Token refresh failed: ${response.message}');
        return false;
      }

      final newAccess = response.data!['access'] as String?;
      final newRefresh = response.data!['refresh'] as String?;
      if (newAccess == null) {
        debugPrint('AuthService: Refresh response missing access token');
        return false;
      }
      _accessToken = newAccess;
      // Backend rotates refresh tokens (ROTATE_REFRESH_TOKENS=True), so the
      // old refresh is blacklisted on success. Only overwrite when the new
      // one is present, never null out a valid refresh on a malformed reply.
      if (newRefresh != null) {
        _refreshToken = newRefresh;
      }

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

      // Call switch-org API to get new tokens with org context. The outgoing
      // refresh token is sent so the backend blacklists it. We replace it below
      // either way, and leaving it live keeps a stolen copy working against the
      // previous org until it expires.
      final response = await _apiService.post(ApiConfig.switchOrg, {
        'org_id': org.id,
        if (_refreshToken != null) 'refresh': _refreshToken,
      }, requiresAuth: true);

      if (!response.success || response.data == null) {
        debugPrint('AuthService: Switch org failed: ${response.message}');
        return false;
      }

      // Update tokens from response. The backend has now blacklisted the token
      // we sent, so a malformed reply must not clear the field, mirror the
      // guard in refreshAccessToken rather than stranding the session.
      _accessToken = response.data!['access_token'] as String?;
      final newRefresh = response.data!['refresh_token'] as String?;
      if (newRefresh != null) {
        _refreshToken = newRefresh;
      }

      // Update selected organization
      _selectedOrganization = org;

      // Sync with ApiService
      _apiService.setAccessToken(_accessToken);
      _apiService.setOrganizationId(org.id);

      // Persist to storage
      await _saveToStorage();
      await _saveSelectedOrganization();

      debugPrint('AuthService: Switched to organization: ${org.name}');
      await CrashReporting.applyFromAuth(this);
      return true;
    } catch (e) {
      debugPrint('AuthService: Switch org error: $e');
      return false;
    }
  }

  /// Update the cached user's name after a successful profile PATCH so the
  /// rest of the app (greeting, More sheet header) reflects the new value
  /// without forcing a sign-out / sign-in.
  Future<void> updateCachedUserName(String name) async {
    final u = _currentUser;
    if (u == null) return;
    _currentUser = AuthUser(
      id: u.id,
      email: u.email,
      name: name,
      profilePic: u.profilePic,
    );
    await _saveToStorage();
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
    // Leave the refresh callback wired, `refreshAccessToken` already bails
    // when `_refreshToken == null`, so it's safe to keep registered. Nulling
    // it here used to break refresh for any signOut → signIn cycle inside
    // the same app session (no path re-registers it).
    await _clearStorage();
    await CrashReporting.clear();

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
        _selectedOrganization = Organization.fromJson(
          jsonDecode(selectedOrgJson) as Map<String, dynamic>,
        );
      }

      debugPrint(
        'AuthService: Loaded from storage, user: ${_currentUser?.email}',
      );
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
        await prefs.setString(
          _userKey,
          jsonEncode({
            'id': _currentUser!.id,
            'email': _currentUser!.email,
            'name': _currentUser!.name,
            'profileImage': _currentUser!.profilePic,
          }),
        );
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
      await prefs.setString(
        _selectedOrgKey,
        jsonEncode(_selectedOrganization!.toJson()),
      );
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
