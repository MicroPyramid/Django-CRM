import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Where the JWTs live.
///
/// `mobile/CLAUDE.md` forbids putting tokens in `SharedPreferences` by name,
/// and until now that is exactly where both of them sat. On Android
/// `SharedPreferences` is a plain XML file in the app's data directory:
/// readable on a rooted device, and pullable through `adb backup` on any build
/// that has not turned backups off. A refresh token read out of it is good for
/// up to fourteen days, and no logout endpoint exists to cut it short.
///
/// Secure storage means the Android Keystore and the iOS Keychain, so the
/// ciphertext on disk is useless without the hardware-backed key.
///
/// Only the two tokens moved. The cached user, org list and selected org stay
/// in `SharedPreferences`: they are display data the UI already shows on
/// screen, and moving them would buy nothing while making every read slower.
class TokenStorage {
  TokenStorage({FlutterSecureStorage? storage})
    : _storage = storage ?? const FlutterSecureStorage();

  final FlutterSecureStorage _storage;

  static const String accessTokenKey = 'jwt_token';
  static const String refreshTokenKey = 'refresh_token';

  /// Reads both tokens, migrating them out of `SharedPreferences` first if a
  /// previous build left them there.
  Future<({String? access, String? refresh})> read() async {
    await _migrateLegacyTokens();
    return (
      access: await _read(accessTokenKey),
      refresh: await _read(refreshTokenKey),
    );
  }

  /// Writes both tokens. A null clears its key rather than leaving the
  /// previous value behind, so a token can never outlive the session that
  /// obtained it.
  Future<void> write({String? access, String? refresh}) async {
    await _write(accessTokenKey, access);
    await _write(refreshTokenKey, refresh);
  }

  /// Clears both tokens, including any legacy copy, so signing out on a
  /// device that upgraded mid-session does not leave a usable refresh token
  /// in the old location.
  Future<void> clear() async {
    await _write(accessTokenKey, null);
    await _write(refreshTokenKey, null);
    await _removeLegacyTokens();
  }

  /// Moves tokens written by a pre-secure-storage build, then deletes the
  /// originals.
  ///
  /// The delete is the point of the exercise. Copying alone would leave the
  /// readable plaintext on disk forever on every device that ever ran an
  /// older build, so the upgrade would fix new installs and no one else.
  ///
  /// Migration is skipped once secure storage holds an access token, so the
  /// common path is one read rather than three.
  Future<void> _migrateLegacyTokens() async {
    if (await _read(accessTokenKey) != null) return;

    final SharedPreferences prefs;
    try {
      prefs = await SharedPreferences.getInstance();
    } catch (e) {
      debugPrint('TokenStorage: legacy check skipped: $e');
      return;
    }

    final legacyAccess = prefs.getString(accessTokenKey);
    final legacyRefresh = prefs.getString(refreshTokenKey);
    if (legacyAccess == null && legacyRefresh == null) return;

    await _write(accessTokenKey, legacyAccess);
    await _write(refreshTokenKey, legacyRefresh);
    await prefs.remove(accessTokenKey);
    await prefs.remove(refreshTokenKey);
    debugPrint('TokenStorage: migrated tokens out of shared preferences');
  }

  Future<void> _removeLegacyTokens() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(accessTokenKey);
      await prefs.remove(refreshTokenKey);
    } catch (e) {
      debugPrint('TokenStorage: legacy clear skipped: $e');
    }
  }

  /// Secure storage talks to the Keystore and can fail: a corrupt entry after
  /// an OS restore, or a locked device on iOS. A throw here would take out
  /// app startup, so a failed read is treated as "no token", which lands the
  /// user on the sign-in screen instead of a crash.
  Future<String?> _read(String key) async {
    try {
      return await _storage.read(key: key);
    } catch (e) {
      debugPrint('TokenStorage: read failed for $key: $e');
      return null;
    }
  }

  Future<void> _write(String key, String? value) async {
    try {
      if (value == null) {
        await _storage.delete(key: key);
      } else {
        await _storage.write(key: key, value: value);
      }
    } catch (e) {
      debugPrint('TokenStorage: write failed for $key: $e');
    }
  }
}
