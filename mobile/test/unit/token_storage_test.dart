import 'package:bottle_crm/services/token_storage.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// `mobile/CLAUDE.md` forbids keeping tokens in `SharedPreferences` by name,
/// and both JWTs sat there until now. These tests pin the two halves of the
/// fix: new tokens go to secure storage, and tokens an older build already
/// wrote are moved out of the readable file rather than merely shadowed.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  /// The map handed to `setMockInitialValues` is the live backing store, so
  /// holding a reference is how a test sees what really landed in the
  /// keychain.
  late Map<String, String> secure;

  void useStores({
    Map<String, String> secureSeed = const {},
    Map<String, Object> prefsSeed = const {},
  }) {
    secure = Map<String, String>.from(secureSeed);
    FlutterSecureStorage.setMockInitialValues(secure);
    SharedPreferences.setMockInitialValues(prefsSeed);
  }

  group('where a token ends up', () {
    test(
      'a written token is in secure storage and not in preferences',
      () async {
        useStores();
        final storage = TokenStorage();

        await storage.write(access: 'access-jwt', refresh: 'refresh-jwt');

        expect(secure[TokenStorage.accessTokenKey], 'access-jwt');
        expect(secure[TokenStorage.refreshTokenKey], 'refresh-jwt');

        final prefs = await SharedPreferences.getInstance();
        expect(prefs.getString(TokenStorage.accessTokenKey), isNull);
        expect(prefs.getString(TokenStorage.refreshTokenKey), isNull);
      },
    );

    test('what was written is what comes back', () async {
      useStores();
      final storage = TokenStorage();

      await storage.write(access: 'access-jwt', refresh: 'refresh-jwt');
      final tokens = await storage.read();

      expect(tokens.access, 'access-jwt');
      expect(tokens.refresh, 'refresh-jwt');
    });

    test('writing null clears rather than leaving the old value', () async {
      useStores();
      final storage = TokenStorage();
      await storage.write(access: 'access-jwt', refresh: 'refresh-jwt');

      // The session ended without a full clear. A token that survived here
      // would outlive the session that obtained it.
      await storage.write(access: null, refresh: null);

      expect(secure, isEmpty);
    });
  });

  group('upgrading from a build that used preferences', () {
    test('legacy tokens are moved into secure storage', () async {
      useStores(
        prefsSeed: {
          TokenStorage.accessTokenKey: 'old-access',
          TokenStorage.refreshTokenKey: 'old-refresh',
        },
      );

      final tokens = await TokenStorage().read();

      // The user stays signed in across the upgrade.
      expect(tokens.access, 'old-access');
      expect(tokens.refresh, 'old-refresh');
      expect(secure[TokenStorage.accessTokenKey], 'old-access');
    });

    test('and are deleted from preferences, which is the point', () async {
      useStores(
        prefsSeed: {
          TokenStorage.accessTokenKey: 'old-access',
          TokenStorage.refreshTokenKey: 'old-refresh',
        },
      );

      await TokenStorage().read();

      // Copying alone would leave readable plaintext on disk forever on every
      // device that ever ran an older build, so the upgrade would protect new
      // installs and nobody else.
      final prefs = await SharedPreferences.getInstance();
      expect(prefs.getString(TokenStorage.accessTokenKey), isNull);
      expect(prefs.getString(TokenStorage.refreshTokenKey), isNull);
    });

    test('a legacy value never overwrites a newer secure one', () async {
      useStores(
        secureSeed: {
          TokenStorage.accessTokenKey: 'current-access',
          TokenStorage.refreshTokenKey: 'current-refresh',
        },
        prefsSeed: {TokenStorage.accessTokenKey: 'stale-access'},
      );

      final tokens = await TokenStorage().read();

      // Migration is skipped once secure storage holds an access token.
      // Without that guard a stale copy would sign the user back into an
      // older session on the next launch.
      expect(tokens.access, 'current-access');
    });

    test('other preferences are left alone', () async {
      useStores(
        prefsSeed: {
          TokenStorage.accessTokenKey: 'old-access',
          'user_data': '{"id":"u1"}',
          'selected_organization': '{"id":"o1"}',
        },
      );

      await TokenStorage().read();

      final prefs = await SharedPreferences.getInstance();
      expect(prefs.getString('user_data'), '{"id":"u1"}');
      expect(prefs.getString('selected_organization'), '{"id":"o1"}');
    });
  });

  group('signing out', () {
    test('clear empties secure storage', () async {
      useStores(
        secureSeed: {
          TokenStorage.accessTokenKey: 'access-jwt',
          TokenStorage.refreshTokenKey: 'refresh-jwt',
        },
      );

      await TokenStorage().clear();

      expect(secure, isEmpty);
    });

    test('clear also empties a legacy copy left by an older build', () async {
      // Signing out on a device that upgraded mid-session, before any read
      // had a chance to migrate. Missing this leaves a refresh token good for
      // fourteen days behind a UI that says you are signed out.
      useStores(
        prefsSeed: {
          TokenStorage.accessTokenKey: 'old-access',
          TokenStorage.refreshTokenKey: 'old-refresh',
        },
      );

      await TokenStorage().clear();

      final prefs = await SharedPreferences.getInstance();
      expect(prefs.getString(TokenStorage.accessTokenKey), isNull);
      expect(prefs.getString(TokenStorage.refreshTokenKey), isNull);
    });
  });

  group('when the keystore itself fails', () {
    test(
      'a read failure signs the user out rather than crashing launch',
      () async {
        SharedPreferences.setMockInitialValues({});
        final storage = TokenStorage(storage: _BrokenSecureStorage());

        final tokens = await storage.read();

        expect(tokens.access, isNull);
        expect(tokens.refresh, isNull);
      },
    );
  });
}

/// A corrupt keychain entry after an OS restore, or a locked device on iOS.
/// Real, and a throw out of `read` would take out app startup.
class _BrokenSecureStorage implements FlutterSecureStorage {
  @override
  Future<String?> read({
    required String key,
    dynamic iOptions,
    dynamic aOptions,
    dynamic lOptions,
    dynamic webOptions,
    dynamic mOptions,
    dynamic wOptions,
  }) async {
    throw PlatformExceptionStub();
  }

  @override
  Future<void> write({
    required String key,
    required String? value,
    dynamic iOptions,
    dynamic aOptions,
    dynamic lOptions,
    dynamic webOptions,
    dynamic mOptions,
    dynamic wOptions,
  }) async {
    throw PlatformExceptionStub();
  }

  @override
  Future<void> delete({
    required String key,
    dynamic iOptions,
    dynamic aOptions,
    dynamic lOptions,
    dynamic webOptions,
    dynamic mOptions,
    dynamic wOptions,
  }) async {
    throw PlatformExceptionStub();
  }

  @override
  noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

class PlatformExceptionStub implements Exception {}
