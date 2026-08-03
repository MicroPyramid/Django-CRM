import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_crashlytics/firebase_crashlytics.dart';
import 'package:flutter/foundation.dart';

import 'auth_service.dart';

/// Thin wrapper around Crashlytics so the rest of the app doesn't depend on
/// `firebase_*` directly. Every method is a no-op when Firebase isn't running
/// (debug iOS builds, tests, etc.), so callers can fire-and-forget.
class CrashReporting {
  static bool get _enabled {
    if (kIsWeb) return false;
    if (defaultTargetPlatform != TargetPlatform.android) return false;
    return Firebase.apps.isNotEmpty;
  }

  /// Reflect the current auth state into Crashlytics. User id + email + org.
  /// Call after sign-in, org switch, or restore-from-storage.
  static Future<void> applyFromAuth(AuthService auth) async {
    if (!_enabled) return;
    final user = auth.currentUser;
    final org = auth.selectedOrganization;
    final c = FirebaseCrashlytics.instance;
    await c.setUserIdentifier(user?.id ?? '');
    await c.setCustomKey('user_email', user?.email ?? '');
    await c.setCustomKey('org_id', org?.id ?? '');
    await c.setCustomKey('org_name', org?.name ?? '');
  }

  /// Clear identity on sign-out so subsequent crashes aren't attributed to the
  /// previous user.
  static Future<void> clear() async {
    if (!_enabled) return;
    final c = FirebaseCrashlytics.instance;
    await c.setUserIdentifier('');
    await c.setCustomKey('user_email', '');
    await c.setCustomKey('org_id', '');
    await c.setCustomKey('org_name', '');
  }
}
