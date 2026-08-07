import 'package:bottle_crm/config/api_config.dart';
import 'package:flutter_test/flutter_test.dart';

/// The API host was two literals in Dart, so anyone self-hosting had to edit
/// source and rebuild. It is now a `--dart-define`, and the branches that
/// define adds are what these tests cover.
///
/// `flutter test` compiles once, without any `--dart-define`, so the override
/// path is unreachable through `ApiConfig.baseUrl` itself. `resolveBaseUrl`
/// takes the two inputs as arguments for exactly that reason.
void main() {
  group('with no override, which is every build today', () {
    test('debug and release resolve to different hosts', () {
      final debug = ApiConfig.resolveBaseUrl(override: '', isDebug: true);
      final release = ApiConfig.resolveBaseUrl(override: '', isDebug: false);

      expect(debug, isNot(release));
      expect(release, 'https://api.bottlecrm.io');
    });

    test('the shipped default is what the app actually uses', () {
      // Pins the wiring, not just the helper: a `baseUrl` that stopped calling
      // `resolveBaseUrl` would leave every test above green and every request
      // pointed somewhere else.
      expect(
        ApiConfig.baseUrl,
        ApiConfig.resolveBaseUrl(override: '', isDebug: true),
      );
    });
  });

  group('with an override', () {
    test('it wins over both built-in hosts', () {
      expect(
        ApiConfig.resolveBaseUrl(
          override: 'https://crm.example.com',
          isDebug: false,
        ),
        'https://crm.example.com',
      );
    });

    test('a trailing slash is dropped rather than doubled into the path', () {
      // `https://host//api` 404s on every call and says nothing about why.
      final resolved = ApiConfig.resolveBaseUrl(
        override: 'https://crm.example.com/',
        isDebug: false,
      );

      expect(resolved, 'https://crm.example.com');
      expect('$resolved/api', 'https://crm.example.com/api');
    });

    test('plain HTTP is refused in a release build', () {
      // The whole point of the guard: before this knob existed nobody could
      // ship a plaintext build without editing source. Now it is one flag away,
      // and every JWT would travel in the clear.
      expect(
        () => ApiConfig.resolveBaseUrl(
          override: 'http://crm.example.com',
          isDebug: false,
        ),
        throwsA(isA<StateError>()),
      );
    });

    test('the refusal names the address, so the mistake is findable', () {
      expect(
        () => ApiConfig.resolveBaseUrl(
          override: 'http://crm.example.com',
          isDebug: false,
        ),
        throwsA(
          isA<StateError>().having(
            (e) => e.message,
            'message',
            contains('http://crm.example.com'),
          ),
        ),
      );
    });

    test('plain HTTP is allowed in debug, where localhost lives', () {
      expect(
        ApiConfig.resolveBaseUrl(
          override: 'http://10.0.2.2:8000',
          isDebug: true,
        ),
        'http://10.0.2.2:8000',
      );
    });
  });

  group('the Google client id', () {
    test('has a default, so an unconfigured build still signs in', () {
      expect(
        ApiConfig.googleServerClientId,
        endsWith('.apps.googleusercontent.com'),
      );
    });
  });
}
