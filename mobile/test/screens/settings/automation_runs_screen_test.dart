import 'package:bottle_crm/core/theme/theme.dart';
import 'package:bottle_crm/data/models/auth_response.dart';
import 'package:bottle_crm/data/models/automation.dart';
import 'package:bottle_crm/providers/auth_provider.dart';
import 'package:bottle_crm/providers/automation_provider.dart';
import 'package:bottle_crm/screens/settings/automation/automation_runs_screen.dart';
import 'package:flutter/material.dart';
import '../../support/org_zone.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

const _id = '3f2b8c1e-7a4d-4e2b-9c1a-5d6e7f8a9b0c';

String _uuid(int n) =>
    '00000000-0000-4000-8000-${n.toString().padLeft(12, '0')}';

AutomationRun _run(
  int n, {
  String status = 'done',
  String name = '',
  String objectKey = 'lead',
  String recordId = '',
  String reason = '',
  List<RunStep> steps = const [],
  int skipped = 0,
  String? by,
}) => AutomationRun(
  id: 'run-$n',
  createdAt: DateTime.utc(2026, 1, 15, 10, 42).subtract(Duration(hours: n)),
  recordId: recordId.isEmpty ? _uuid(n) : recordId,
  recordName: name.isEmpty ? 'Record $n' : name,
  objectKey: objectKey,
  status: status,
  reason: reason,
  steps: steps,
  skippedCount: skipped,
  triggeredByRuleName: by,
);

class _Calls {
  final List<int> offsets = [];
  Object? fail;
  Future<RunPage> Function(int offset)? answer;
}

late _Calls _calls;

class _OrgNotifier extends Notifier<Organization?> {
  @override
  Organization? build() => const Organization(id: 'org-1', name: 'Acme');

  void switchTo(String id) => state = Organization(id: id, name: id);
}

final _orgProvider = NotifierProvider<_OrgNotifier, Organization?>(
  _OrgNotifier.new,
);

Future<GoRouter> _open(
  WidgetTester tester, {
  bool admin = true,
  List<AutomationRun>? runs,
  int? count,
  Future<RunPage> Function(int offset)? answer,
  double textScale = 1.0,
}) async {
  _calls = _Calls();
  tester.view.devicePixelRatio = 3.0;
  tester.view.physicalSize = const Size(390 * 3, 844 * 3);
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
  final router = GoRouter(
    initialLocation: '/runs',
    routes: [
      GoRoute(
        path: '/runs',
        builder: (_, _) => const AutomationRunsScreen(ruleId: _id),
      ),
      GoRoute(
        path: '/leads/:id',
        builder: (_, s) =>
            Scaffold(body: Text('lead page ${s.pathParameters['id']}')),
      ),
    ],
  );
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        isOrgAdminProvider.overrideWithValue(admin),
        selectedOrgProvider.overrideWith((ref) => ref.watch(_orgProvider)),
        automationRuleProvider.overrideWith(
          (ref, id) async => AutomationRule(
            id: id,
            name: 'New lead: rotate owners',
            objectKey: 'lead',
            trigger: TriggerDraft(),
          ),
        ),
        automationRunsProvider.overrideWith((ref, key) {
          _calls.offsets.add(key.offset);
          if (answer != null) return answer(key.offset);
          final list = runs ?? const <AutomationRun>[];
          return Future.value(
            RunPage(
              runs: list,
              count: count ?? list.length,
              offset: key.offset,
            ),
          );
        }),
      ],
      child: MaterialApp.router(
        theme: AppTheme.light,
        routerConfig: router,
        builder: (context, child) => MediaQuery(
          data: MediaQuery.of(
            context,
          ).copyWith(textScaler: TextScaler.linear(textScale)),
          child: child!,
        ),
      ),
    ),
  );
  await tester.pumpAndSettle();
  return router;
}

void main() {
  testWidgets('lists runs newest first with time, record and status', (
    tester,
  ) async {
    await _open(
      tester,
      runs: [
        _run(1, name: 'Sana Kapoor'),
        _run(2, name: 'Tom Reyes', status: 'failed'),
        _run(3, name: 'Wu Lin', status: 'skipped', skipped: 2),
      ],
    );
    expect(find.text('New lead: rotate owners'), findsOneWidget);
    expect(
      find.text('Runs from the last 30 days, newest first.'),
      findsOneWidget,
    );
    final a = tester.getTopLeft(find.text('Sana Kapoor')).dy;
    final b = tester.getTopLeft(find.text('Tom Reyes')).dy;
    final c = tester.getTopLeft(find.text('Wu Lin')).dy;
    expect(a < b && b < c, isTrue);
    expect(find.text('Done'), findsOneWidget);
    expect(find.text('Failed'), findsOneWidget);
    expect(find.text('Skipped'), findsOneWidget);
    expect(find.textContaining('09:42'), findsOneWidget);
  });

  testWidgets('a run opens to its steps, undone and failed included', (
    tester,
  ) async {
    await _open(
      tester,
      runs: [
        _run(
          1,
          status: 'failed',
          steps: const [
            RunStep(status: 'done', text: 'Assigned to Ravi'),
            RunStep(status: 'undone', text: 'Notified Ravi'),
            RunStep(status: 'failed', text: 'Email to Joe failed'),
            RunStep(status: 'skipped', text: 'Webhook not sent'),
          ],
        ),
      ],
    );
    expect(find.text('Assigned to Ravi'), findsNothing);
    await tester.tap(find.byType(ExpansionTile));
    await tester.pumpAndSettle();
    expect(find.text('Assigned to Ravi'), findsOneWidget);
    expect(find.text('Notified Ravi'), findsOneWidget);
    expect(find.text('Email to Joe failed'), findsOneWidget);
    expect(find.text('Webhook not sent'), findsOneWidget);
    expect(find.text('Undone'), findsOneWidget);
    expect(find.text('Skipped'), findsOneWidget);
    expect(find.text('Failed'), findsNWidgets(2));
    expect(
      find.byWidgetPredicate((w) => w is Icon && w.semanticLabel == 'Done'),
      findsOneWidget,
    );
  });

  testWidgets('a skipped run shows its count reason and no steps', (
    tester,
  ) async {
    await _open(
      tester,
      runs: [
        _run(
          1,
          status: 'skipped',
          skipped: 3,
          reason: 'The hourly run limit was reached 3 times.',
        ),
      ],
    );
    expect(
      find.text('The hourly run limit was reached 3 times.'),
      findsOneWidget,
    );
    expect(find.byType(ExpansionTile), findsNothing);
  });

  testWidgets('shows set off by the causing rule', (tester) async {
    await _open(tester, runs: [_run(1, by: 'Deal won: onboarding')]);
    expect(find.text('Set off by "Deal won: onboarding"'), findsOneWidget);
  });

  testWidgets('Older and Newer page by 20', (tester) async {
    await _open(
      tester,
      count: 45,
      answer: (offset) async => RunPage(
        runs: [_run(offset + 1, name: 'Row at $offset')],
        count: 45,
        offset: offset,
      ),
    );
    expect(find.text('Row at 0'), findsOneWidget);
    OutlinedButton btn(String t) =>
        tester.widget<OutlinedButton>(find.widgetWithText(OutlinedButton, t));
    expect(btn('Newer').onPressed, isNull);
    expect(btn('Older').onPressed, isNotNull);
    await tester.ensureVisible(find.text('Older'));
    await tester.tap(find.text('Older'));
    await tester.pumpAndSettle();
    expect(find.text('Row at 20'), findsOneWidget);
    expect(btn('Newer').onPressed, isNotNull);
    await tester.ensureVisible(find.text('Older'));
    await tester.tap(find.text('Older'));
    await tester.pumpAndSettle();
    expect(find.text('Row at 40'), findsOneWidget);
    expect(btn('Older').onPressed, isNull);
    await tester.ensureVisible(find.text('Newer'));
    await tester.tap(find.text('Newer'));
    await tester.pumpAndSettle();
    expect(find.text('Row at 20'), findsOneWidget);
    expect(_calls.offsets, containsAll([0, 20, 40]));
  });

  testWidgets('the record name opens the record', (tester) async {
    await _open(
      tester,
      runs: [
        _run(
          1,
          name: 'Sana Kapoor',
          recordId: '11111111-1111-4111-8111-111111111111',
        ),
        _run(2, name: 'Gone Thing', objectKey: 'unknown'),
      ],
    );
    final button = find.widgetWithText(TextButton, 'Sana Kapoor');
    expect(button, findsOneWidget);
    expect(tester.getSize(button).height, greaterThanOrEqualTo(44));
    expect(find.widgetWithText(TextButton, 'Gone Thing'), findsNothing);
    expect(find.text('Gone Thing'), findsOneWidget);
    await tester.tap(button);
    await tester.pumpAndSettle();
    expect(
      find.text('lead page 11111111-1111-4111-8111-111111111111'),
      findsOneWidget,
    );
  });

  testWidgets('shows the empty state', (tester) async {
    await _open(tester, runs: const []);
    expect(find.text('No runs yet'), findsOneWidget);
    expect(
      find.text(
        'When this rule runs, each run and what it did shows here for 30 days.',
      ),
      findsOneWidget,
    );
  });

  testWidgets('a member sees the notice and nothing is fetched', (
    tester,
  ) async {
    await _open(tester, admin: false);
    expect(
      find.text('Only an organization admin can see automation rules.'),
      findsOneWidget,
    );
    expect(_calls.offsets, isEmpty);
  });

  testWidgets('a failed load shows Try again, which reloads', (tester) async {
    var fail = true;
    await _open(
      tester,
      answer: (offset) async {
        if (fail) throw Exception('boom');
        return RunPage(runs: [_run(1, name: 'Back again')], count: 1);
      },
    );
    expect(find.text('Could not load the runs'), findsOneWidget);
    fail = false;
    await tester.tap(find.text('Try again'));
    await tester.pumpAndSettle();
    expect(find.text('Back again'), findsOneWidget);
  });

  testWidgets('holds at a phone width with large text', (tester) async {
    await _open(
      tester,
      textScale: 2.0,
      runs: [
        _run(
          1,
          name: 'A very long record name that has to wrap on a narrow phone',
          by: 'A long rule name that also has to wrap somewhere sensible',
          reason: 'A long reason that also wraps across several lines',
          steps: const [RunStep(status: 'done', text: 'Assigned to Ravi')],
        ),
      ],
    );
    await tester.tap(find.text('Done'));
    await tester.pumpAndSettle();
    expect(find.text('Assigned to Ravi'), findsOneWidget);
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
  });

  testWidgets('a record id that is not a UUID shows plain text', (
    tester,
  ) async {
    await _open(
      tester,
      runs: [
        _run(1, name: 'Slash Name', recordId: 'a/b'),
        _run(2, name: 'Short Name', recordId: 'abc'),
      ],
    );
    expect(find.text('Slash Name'), findsOneWidget);
    expect(find.text('Short Name'), findsOneWidget);
    expect(find.byType(TextButton), findsNothing);
  });

  testWidgets('run times follow the org zone', (tester) async {
    final api = await useOrgZone('Asia/Kolkata');
    addTearDown(api.uninstall);
    await _open(tester, runs: [_run(0)]);
    expect(find.textContaining('16:12'), findsOneWidget);
    expect(find.textContaining('10:42'), findsNothing);
  });

  testWidgets('Older is disabled at offset 20 of 40', (tester) async {
    await _open(
      tester,
      answer: (offset) async => RunPage(
        runs: [_run(offset + 1, name: 'Row at $offset')],
        count: 40,
        offset: offset,
      ),
    );
    await tester.ensureVisible(find.text('Older'));
    await tester.tap(find.text('Older'));
    await tester.pumpAndSettle();
    expect(find.text('Row at 20'), findsOneWidget);
    final older = tester.widget<OutlinedButton>(
      find.widgetWithText(OutlinedButton, 'Older'),
    );
    expect(older.onPressed, isNull);
    final newer = tester.widget<OutlinedButton>(
      find.widgetWithText(OutlinedButton, 'Newer'),
    );
    expect(newer.onPressed, isNotNull);
  });

  testWidgets('markup in server text renders literally', (tester) async {
    await _open(
      tester,
      runs: [
        _run(
          1,
          name: '<b>x</b>',
          reason: '[a](javascript:x)',
          steps: const [
            RunStep(status: 'done', text: '<b>x</b> [a](javascript:x)'),
          ],
        ),
      ],
    );
    expect(find.text('<b>x</b>'), findsOneWidget);
    expect(find.text('[a](javascript:x)'), findsOneWidget);
    await tester.tap(find.byType(ExpansionTile));
    await tester.pumpAndSettle();
    expect(find.text('<b>x</b> [a](javascript:x)'), findsOneWidget);
  });

  testWidgets('an org change returns to the first page', (tester) async {
    await _open(
      tester,
      answer: (offset) async => RunPage(
        runs: [_run(offset + 1, name: 'Row at $offset')],
        count: 45,
        offset: offset,
      ),
    );
    await tester.ensureVisible(find.text('Older'));
    await tester.tap(find.text('Older'));
    await tester.pumpAndSettle();
    expect(find.text('Row at 20'), findsOneWidget);
    final container = ProviderScope.containerOf(
      tester.element(find.byType(AutomationRunsScreen)),
    );
    container.read(_orgProvider.notifier).switchTo('org-2');
    await tester.pumpAndSettle();
    expect(find.text('Row at 0'), findsOneWidget);
  });

  testWidgets('an empty later page says so and keeps Newer', (tester) async {
    await _open(
      tester,
      answer: (offset) async => offset == 0
          ? RunPage(runs: [_run(1, name: 'First')], count: 25, offset: 0)
          : RunPage(runs: const [], count: 25, offset: offset),
    );
    await tester.ensureVisible(find.text('Older'));
    await tester.tap(find.text('Older'));
    await tester.pumpAndSettle();
    expect(find.text('No more runs.'), findsOneWidget);
    expect(find.text('No runs yet'), findsNothing);
    final newer = tester.widget<OutlinedButton>(
      find.widgetWithText(OutlinedButton, 'Newer'),
    );
    expect(newer.onPressed, isNotNull);
  });

  testWidgets('a failed later page keeps Newer beside Try again', (
    tester,
  ) async {
    await _open(
      tester,
      answer: (offset) async {
        if (offset == 0) {
          return RunPage(runs: [_run(1, name: 'First')], count: 45, offset: 0);
        }
        throw Exception('boom');
      },
    );
    await tester.ensureVisible(find.text('Older'));
    await tester.tap(find.text('Older'));
    await tester.pumpAndSettle();
    expect(find.text('Could not load the runs'), findsOneWidget);
    expect(find.text('Try again'), findsOneWidget);
    await tester.tap(find.text('Newer'));
    await tester.pumpAndSettle();
    expect(find.text('First'), findsOneWidget);
  });
}
