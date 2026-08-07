import 'dart:convert';
import 'dart:io';

import 'package:bottle_crm/config/api_config.dart';
import 'package:bottle_crm/services/api_service.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

/// A JWT that decodes but is not signed. `JwtDecoder` reads the claims without
/// verifying, which is all the expiry check does.
String jwtExpiring(Duration fromNow) {
  String seg(Map<String, dynamic> m) =>
      base64Url.encode(utf8.encode(jsonEncode(m))).replaceAll('=', '');
  final exp = DateTime.now().add(fromNow).millisecondsSinceEpoch ~/ 1000;
  return '${seg({'alg': 'HS256', 'typ': 'JWT'})}.${seg({'exp': exp})}.sig';
}

void main() {
  // The singleton carries state between tests, so every test sets what it
  // needs and clears afterwards.
  tearDown(() {
    ApiService().clearAuth();
    ApiService().setRefreshCallback(null);
    ApiService().setClientForTesting(http.Client());
  });

  group('access token refresh', () {
    test('refreshes an expired token before sending, even though the API '
        'answers 403 rather than 401', () async {
      final api = ApiService();
      final sentTokens = <String?>[];
      var refreshCalls = 0;

      api.setAccessToken(jwtExpiring(const Duration(minutes: -5)));
      api.setRefreshCallback(() async {
        refreshCalls++;
        api.setAccessToken(jwtExpiring(const Duration(hours: 1)));
        return true;
      });
      api.setClientForTesting(
        MockClient((request) async {
          sentTokens.add(request.headers['Authorization']);
          // What the real API returns for a credential it will not accept:
          // HasOrgContext denies before DRF's auth layer emits a 401.
          return http.Response(
            jsonEncode({'detail': 'Organization context is required.'}),
            403,
          );
        }),
      );

      await api.get(ApiConfig.leads);

      expect(
        refreshCalls,
        1,
        reason: 'expiry must trigger exactly one refresh',
      );
      // One send, not two: the token was renewed on the way out, so there is
      // nothing to retry. Before this fix the count was one send and zero
      // refreshes, because the 401 branch never saw a 401.
      expect(sentTokens, hasLength(1));
    });

    test(
      'the request carries the refreshed token, not the expired one',
      () async {
        final api = ApiService();
        final expired = jwtExpiring(const Duration(minutes: -5));
        final fresh = jwtExpiring(const Duration(hours: 1));
        String? sent;

        api.setAccessToken(expired);
        api.setRefreshCallback(() async {
          api.setAccessToken(fresh);
          return true;
        });
        api.setClientForTesting(
          MockClient((request) async {
            sent = request.headers['Authorization'];
            return http.Response('{}', 200);
          }),
        );

        await api.get(ApiConfig.leads);

        expect(sent, 'Bearer $fresh');
        expect(sent, isNot('Bearer $expired'));
      },
    );

    test('a live token is sent as-is, with no refresh round-trip', () async {
      final api = ApiService();
      final live = jwtExpiring(const Duration(hours: 1));
      var refreshCalls = 0;
      String? sent;

      api.setAccessToken(live);
      api.setRefreshCallback(() async {
        refreshCalls++;
        return true;
      });
      api.setClientForTesting(
        MockClient((request) async {
          sent = request.headers['Authorization'];
          return http.Response('{}', 200);
        }),
      );

      await api.get(ApiConfig.leads);

      expect(refreshCalls, 0);
      expect(sent, 'Bearer $live');
    });

    test('a token inside the grace window counts as expired', () async {
      final api = ApiService();
      var refreshCalls = 0;

      // Valid for another 5 seconds, which is less than the 30-second grace:
      // it would age out mid-flight.
      api.setAccessToken(jwtExpiring(const Duration(seconds: 5)));
      api.setRefreshCallback(() async {
        refreshCalls++;
        api.setAccessToken(jwtExpiring(const Duration(hours: 1)));
        return true;
      });
      api.setClientForTesting(
        MockClient((_) async => http.Response('{}', 200)),
      );

      await api.get(ApiConfig.leads);

      expect(refreshCalls, 1);
    });

    test('an unauthenticated call never refreshes', () async {
      final api = ApiService();
      var refreshCalls = 0;

      api.setAccessToken(jwtExpiring(const Duration(minutes: -5)));
      api.setRefreshCallback(() async {
        refreshCalls++;
        return true;
      });
      api.setClientForTesting(
        MockClient((_) async => http.Response('{}', 200)),
      );

      // The refresh endpoint itself posts with requiresAuth: false. Without
      // this exemption the expired token would trigger a refresh, whose own
      // request would trigger another, and `_refreshInFlight` would return the
      // future that is waiting on it.
      await api.post(ApiConfig.refreshToken, {
        'refresh': 'x',
      }, requiresAuth: false);

      expect(refreshCalls, 0);
    });

    test('a token that will not decode is sent as-is', () async {
      final api = ApiService();
      var refreshCalls = 0;
      String? sent;

      api.setAccessToken('not-a-jwt');
      api.setRefreshCallback(() async {
        refreshCalls++;
        return true;
      });
      api.setClientForTesting(
        MockClient((request) async {
          sent = request.headers['Authorization'];
          return http.Response('{}', 403);
        }),
      );

      await api.get(ApiConfig.leads);

      expect(refreshCalls, 0, reason: 'refreshing cannot repair a bad token');
      expect(sent, 'Bearer not-a-jwt');
    });
  });

  group('network failures', () {
    test('an offline request reports something the user can act on, not the '
        'API hostname', () async {
      final api = ApiService();
      api.setAccessToken(jwtExpiring(const Duration(hours: 1)));
      api.setOrganizationId('org-1');
      api.setClientForTesting(
        MockClient((request) async {
          throw const SocketException(
            'Failed host lookup: pc-8000.rcdev.in',
            osError: OSError('No address associated with hostname', 7),
          );
        }),
      );

      final response = await api.get('/api/leads/');

      expect(response.success, isFalse);
      expect(response.message, isNotNull);
      // The exception's own text carries the host and the URI. Neither belongs
      // on a screen, and neither helps the person reading it.
      expect(response.message, isNot(contains('pc-8000')));
      expect(response.message, isNot(contains('SocketException')));
      expect(response.message, contains('Check your connection'));
    });
  });
}
