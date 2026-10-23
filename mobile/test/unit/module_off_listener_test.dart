import 'dart:async';
import 'dart:convert';

import 'package:bottle_crm/config/api_config.dart';
import 'package:bottle_crm/providers/org_modules_provider.dart';
import 'package:bottle_crm/services/api_service.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

const _off =
    '{"detail": "Tickets is switched off for this organization.", '
    '"code": "module_off", "module": "tickets"}';

class _Client extends http.BaseClient {
  int otherStatus = 404;
  String otherBody = _off;
  Completer<void>? holdModules;
  int modulesCalls = 0;

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    final isModules = request.url.path == Uri.parse(ApiConfig.orgModules).path;
    var status = otherStatus;
    var body = otherBody;
    if (isModules) {
      modulesCalls++;
      status = 200;
      body = '{"modules": [], "can_edit": true}';
      await holdModules?.future;
    }
    return http.StreamedResponse(
      Stream.value(utf8.encode(body)),
      status,
      request: request,
    );
  }
}

void main() {
  late _Client client;
  late ProviderContainer container;

  setUp(() async {
    client = _Client();
    ApiService().setClientForTesting(client);
    container = ProviderContainer();
    container.listen(orgModulesProvider, (_, _) {});
    container.read(moduleOffListenerProvider);
    await container.read(orgModulesProvider.future);
    client.modulesCalls = 0;
  });

  tearDown(() {
    container.dispose();
    ApiService().setModuleOffCallback(null);
  });

  test('a module_off answer on any request reloads the modules', () async {
    final api = ApiService();
    await api.get('${ApiConfig.apiBaseUrl}/tickets/');
    await container.read(orgModulesProvider.future);
    expect(client.modulesCalls, 1);
    await api.post('${ApiConfig.apiBaseUrl}/tickets/', {});
    await container.read(orgModulesProvider.future);
    expect(client.modulesCalls, 2);
    await api.delete('${ApiConfig.apiBaseUrl}/tickets/1/');
    await container.read(orgModulesProvider.future);
    expect(client.modulesCalls, 3);
  });

  test(
    'a 404 without code, and a 409 without module_off, do not reload them',
    () async {
      final api = ApiService();
      client.otherBody = '{"detail": "Not found."}';
      await api.get('${ApiConfig.apiBaseUrl}/tickets/9/');
      client.otherBody = 'not json';
      await api.get('${ApiConfig.apiBaseUrl}/tickets/9/');
      client.otherStatus = 409;
      client.otherBody = '{"detail": "Has open tickets."}';
      await api.delete('${ApiConfig.apiBaseUrl}/tickets/1/');
      await Future<void>.delayed(Duration.zero);
      expect(client.modulesCalls, 0);
    },
  );

  test('a 409 with code module_off reloads them', () async {
    final api = ApiService();
    client.otherStatus = 409;
    client.otherBody = _off;
    await api.delete('${ApiConfig.apiBaseUrl}/tickets/1/');
    await container.read(orgModulesProvider.future);
    expect(client.modulesCalls, 1);
  });

  test('several module_off answers while a reload runs ask once', () async {
    final api = ApiService();
    client.holdModules = Completer<void>();
    await api.get('${ApiConfig.apiBaseUrl}/tickets/');
    await api.get('${ApiConfig.apiBaseUrl}/tickets/');
    await api.get('${ApiConfig.apiBaseUrl}/tickets/');
    client.holdModules!.complete();
    await container.read(orgModulesProvider.future);
    expect(client.modulesCalls, 1);
  });

  test('disposing the listener clears the callback', () async {
    expect(ApiService().hasModuleOffCallback, isTrue);
    container.dispose();
    expect(ApiService().hasModuleOffCallback, isFalse);
    await ApiService().get('${ApiConfig.apiBaseUrl}/tickets/');
    expect(client.modulesCalls, 0);
  });
}
