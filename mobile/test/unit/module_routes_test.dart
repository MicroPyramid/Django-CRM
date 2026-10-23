import 'package:bottle_crm/providers/auth_provider.dart';
import 'package:bottle_crm/routes/app_router.dart';
import 'package:bottle_crm/routes/module_routes.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

import '../support/modules_fixtures.dart';

// Every route that needs no module. A new route fails the walk below until it
// is here or has a need in module_routes.dart.
const corePaths = {
  '/splash',
  '/login',
  '/magic-link/email',
  '/magic-link/code',
  '/org-selection',
  '/org-selection/new',
  '/welcome/import',
  '/accounts',
  '/accounts/create',
  '/accounts/:id/edit',
  '/accounts/:id',
  '/contacts',
  '/contacts/create',
  '/contacts/:id/edit',
  '/contacts/:id',
  '/merge/:module/:id',
  '/notifications',
  '/help',
  '/help/new',
  '/help/:id',
  '/more/profile',
  '/more/team',
  '/more/profile/tokens',
  '/more/settings',
  '/more/settings/custom-fields',
  '/more/settings/tags',
  '/more/settings/web-forms',
  '/more/settings/web-forms/:formId',
  '/more/settings/webhooks',
  '/more/settings/webhooks/:webhookId',
  '/more/settings/automation',
  '/more/settings/automation/new',
  '/more/settings/automation/:ruleId',
  '/more/settings/automation/:ruleId/runs',
  '/more/settings/audit-log',
  '/more/settings/objects',
  '/more/settings/objects/:key',
  '/more/settings/api-tokens',
  '/more/settings/organization',
  '/more/settings/organization/edit',
  '/more/settings/modules',
  '/more/objects/:key',
  '/more/objects/:key/new',
  '/more/objects/:key/:id',
  '/more/objects/:key/:id/edit',
  '/dashboard',
  '/more',
};

void _walk(List<RouteBase> routes, String parent, List<String> out) {
  for (final route in routes) {
    if (route is GoRoute) {
      final full = route.path.startsWith('/')
          ? route.path
          : '${parent == '/' ? '' : parent}/${route.path}';
      out.add(full);
      _walk(route.routes, full, out);
    } else if (route is StatefulShellRoute) {
      for (final branch in route.branches) {
        _walk(branch.routes, parent, out);
      }
    } else {
      _walk(route.routes, parent, out);
    }
  }
}

void main() {
  test('maps each module path and leaves core paths alone', () {
    List<String>? keys(String path) => needFor(path)?.keys;
    expect(keys('/leads'), ['leads']);
    expect(keys('/leads/board'), ['leads']);
    expect(keys('/more/settings/lead-pipelines/:pipelineId'), ['leads']);
    expect(keys('/more/settings/deal-pipelines'), ['deals']);
    expect(keys('/deals/abc/edit'), ['deals']);
    expect(keys('/goals/history'), ['goals']);
    expect(keys('/tasks/:id'), ['tasks']);
    expect(keys('/more/profile/calendar-feed'), ['tasks']);
    expect(keys('/tickets/:id'), ['tickets']);
    expect(keys('/tickets/analytics'), ['tickets']);
    for (final s in [
      'routing',
      'escalation',
      'business-hours',
      'reopen',
      'macros',
      'inbound-email',
      'ticket-approvals',
    ]) {
      expect(keys('/more/settings/$s'), ['tickets'], reason: s);
    }
    expect(keys('/solutions/new'), ['knowledge_base']);
    expect(keys('/more/settings/help-center'), ['knowledge_base']);
    expect(keys('/timesheet/report'), ['timesheet']);
    expect(keys('/invoices/templates/:id/edit'), ['invoices']);
    expect(keys('/invoices/estimates'), ['invoices']);
    expect(keys('/accounts/:id/statement'), ['invoices']);
    expect(keys('/accounts/42/statement'), ['invoices']);
    expect(keys('/documents/new'), ['documents']);
    expect(needFor('/accounts/:id'), isNull);
    expect(needFor('/accounts'), isNull);
    expect(needFor('/accounts/:id/edit'), isNull);
    expect(needFor('/more/settings/web-forms'), isNull);
    expect(needFor('/more/settings/modules'), isNull);
    expect(needFor('/dashboard'), isNull);
    expect(needFor('/leadsx'), isNull);
    expect(needFor('/invoices/products')!.any, isTrue);
    expect(needFor('/invoices/products')!.keys, ['invoices', 'deals']);
  });

  test('names invoices for products only when both are off', () {
    final need = needFor(AppRoutes.products)!;
    expect(refusedModule(need, modulesAnswer(off: ['invoices'])), isNull);
    expect(refusedModule(need, modulesAnswer(off: ['deals'])), isNull);
    expect(
      refusedModule(need, modulesAnswer(off: ['invoices', 'deals'])),
      'invoices',
    );
    expect(refusedModule(need, null), isNull);
  });

  test('an all-need names its first module that is off', () {
    const need = ModuleNeed(['deals', 'tasks']);
    expect(refusedModule(need, modulesAnswer()), isNull);
    expect(refusedModule(need, modulesAnswer(off: ['tasks'])), 'tasks');
    expect(
      refusedModule(need, modulesAnswer(off: ['tasks', 'deals'])),
      'deals',
    );
  });

  test('every route in the router is classified', () {
    final container = ProviderContainer(
      overrides: [selectedOrgProvider.overrideWithValue(null)],
    );
    addTearDown(container.dispose);
    final paths = <String>[];
    _walk(container.read(appRouterProvider).configuration.routes, '/', paths);
    expect(paths.length, greaterThan(100));
    final unclassified = [
      for (final p in paths)
        if (needFor(p) == null && !corePaths.contains(p)) p,
    ];
    expect(unclassified, isEmpty);
    final stale = [
      for (final p in corePaths)
        if (!paths.contains(p)) p,
    ];
    expect(stale, isEmpty);
    expect(corePaths.where((p) => needFor(p) != null), isEmpty);
  });
}
