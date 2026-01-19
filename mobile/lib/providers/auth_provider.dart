import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../data/models/auth_response.dart';
import '../services/auth_service.dart';

/// Authentication state for the app
class AuthState {
  final AuthUser? user;
  final List<Organization>? organizations;
  final Organization? selectedOrganization;
  final bool isLoading;
  final bool isAuthenticated;
  final String? error;

  const AuthState({
    this.user,
    this.organizations,
    this.selectedOrganization,
    this.isLoading = false,
    this.isAuthenticated = false,
    this.error,
  });

  /// Initial state
  const AuthState.initial()
      : user = null,
        organizations = null,
        selectedOrganization = null,
        isLoading = false,
        isAuthenticated = false,
        error = null;

  /// Check if user needs to select an organization
  bool get needsOrgSelection =>
      isAuthenticated &&
      organizations != null &&
      organizations!.isNotEmpty &&
      selectedOrganization == null;

  /// Create a copy with updated fields
  /// Use [clearSelectedOrganization] to explicitly set selectedOrganization to null
  AuthState copyWith({
    AuthUser? user,
    List<Organization>? organizations,
    Organization? selectedOrganization,
    bool? isLoading,
    bool? isAuthenticated,
    String? error,
    bool clearError = false,
    bool clearSelectedOrganization = false,
  }) {
    return AuthState(
      user: user ?? this.user,
      organizations: organizations ?? this.organizations,
      selectedOrganization: clearSelectedOrganization
          ? null
          : (selectedOrganization ?? this.selectedOrganization),
      isLoading: isLoading ?? this.isLoading,
      isAuthenticated: isAuthenticated ?? this.isAuthenticated,
      error: clearError ? null : (error ?? this.error),
    );
  }

  @override
  String toString() =>
      'AuthState(isAuthenticated: $isAuthenticated, user: ${user?.email}, isLoading: $isLoading)';
}

/// Notifier for authentication state changes
class AuthNotifier extends StateNotifier<AuthState> {
  AuthNotifier() : super(const AuthState.initial());

  final AuthService _authService = AuthService();

  /// Check if user is already authenticated (on app launch)
  Future<void> checkAuthStatus() async {
    debugPrint('AuthNotifier: Checking auth status...');

    state = state.copyWith(isLoading: true, clearError: true);

    // AuthService.initialize() should have been called before this
    final isLoggedIn = _authService.isLoggedIn;

    state = state.copyWith(
      isLoading: false,
      isAuthenticated: isLoggedIn,
      user: _authService.currentUser,
      organizations: _authService.organizations,
      selectedOrganization: _authService.selectedOrganization,
    );

    debugPrint('AuthNotifier: Auth status checked, isAuthenticated: ${state.isAuthenticated}');
  }

  /// Sign in with Google
  Future<bool> signInWithGoogle() async {
    debugPrint('AuthNotifier: Starting Google sign-in...');

    state = state.copyWith(isLoading: true, clearError: true);

    try {
      final success = await _authService.signInWithGoogle();

      if (success) {
        // Fresh Google sign-in clears selected org - user must select again
        state = state.copyWith(
          isLoading: false,
          isAuthenticated: true,
          user: _authService.currentUser,
          organizations: _authService.organizations,
          clearSelectedOrganization: true,
        );

        debugPrint('AuthNotifier: Google sign-in successful');
        return true;
      } else {
        state = state.copyWith(
          isLoading: false,
          error: 'Sign-in was cancelled or failed. Please try again.',
        );

        debugPrint('AuthNotifier: Google sign-in failed');
        return false;
      }
    } catch (e) {
      debugPrint('AuthNotifier: Google sign-in error: $e');

      state = state.copyWith(
        isLoading: false,
        error: 'An error occurred during sign-in: ${e.toString()}',
      );

      return false;
    }
  }

  /// Switch to a different organization
  Future<bool> switchOrganization(Organization org) async {
    debugPrint('AuthNotifier: Switching organization to ${org.name}...');

    state = state.copyWith(isLoading: true, clearError: true);

    try {
      final success = await _authService.selectOrganization(org);

      if (success) {
        state = state.copyWith(
          isLoading: false,
          selectedOrganization: org,
        );

        debugPrint('AuthNotifier: Organization switched to ${org.name}');
        return true;
      } else {
        state = state.copyWith(
          isLoading: false,
          error: 'Failed to switch organization',
        );

        return false;
      }
    } catch (e) {
      debugPrint('AuthNotifier: Switch organization error: $e');

      state = state.copyWith(
        isLoading: false,
        error: 'An error occurred: ${e.toString()}',
      );

      return false;
    }
  }

  /// Sign out
  Future<void> signOut() async {
    debugPrint('AuthNotifier: Signing out...');

    state = state.copyWith(isLoading: true, clearError: true);

    await _authService.signOut();

    state = const AuthState.initial();

    debugPrint('AuthNotifier: Signed out');
  }

  /// Clear any error message
  void clearError() {
    state = state.copyWith(clearError: true);
  }
}

/// Provider for authentication state
final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  return AuthNotifier();
});

/// Provider for checking if user is authenticated
final isAuthenticatedProvider = Provider<bool>((ref) {
  return ref.watch(authProvider).isAuthenticated;
});

/// Provider for current user
final currentUserProvider = Provider<AuthUser?>((ref) {
  return ref.watch(authProvider).user;
});

/// Provider for selected organization
final selectedOrgProvider = Provider<Organization?>((ref) {
  return ref.watch(authProvider).selectedOrganization;
});

/// Provider for checking if org selection is needed
final needsOrgSelectionProvider = Provider<bool>((ref) {
  return ref.watch(authProvider).needsOrgSelection;
});
