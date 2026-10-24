import 'package:bottle_crm/data/models/lead_source.dart';
import 'package:bottle_crm/providers/auth_provider.dart';
import 'package:bottle_crm/providers/lead_sources_provider.dart';
import 'package:bottle_crm/screens/settings/lead_sources_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

/// Settings, Lead sources: any member reads the list; an admin adds, renames,
/// retires and reorders. An older API's fixed list is shown read-only.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  const answer = LeadSourcesAnswer(
    sources: [
      LeadSource(id: 's1', key: 'call', label: 'Call', order: 1),
      LeadSource(
        id: 's2',
        key: 'directory or marketplace',
        label: 'Directory or marketplace, the long kind of label',
        order: 2,
      ),
      LeadSource(id: 's3', key: 'fax', label: 'Fax', isActive: false, order: 3),
    ],
  );

  Future<_FakeSources> pump(
    WidgetTester tester, {
    bool admin = true,
    LeadSourcesAnswer given = answer,
    double textScale = 1.0,
    Size size = const Size(390, 844),
  }) async {
    final fake = _FakeSources(given);
    tester.view.devicePixelRatio = 3.0;
    tester.view.physicalSize = Size(size.width * 3, size.height * 3);
    tester.platformDispatcher.textScaleFactorTestValue = textScale;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          isOrgAdminProvider.overrideWithValue(admin),
          leadSourcesProvider.overrideWith(() => fake),
        ],
        child: const MaterialApp(home: LeadSourcesScreen()),
      ),
    );
    await tester.pumpAndSettle();
    return fake;
  }

  for (final scale in [1.0, 1.3]) {
    testWidgets('fits a 390px phone at ${scale}x text', (tester) async {
      await pump(tester, textScale: scale);
      expect(tester.takeException(), isNull);
      expect(find.text('Call'), findsOneWidget);
      expect(find.text('Retired'), findsOneWidget);
      expect(find.text('Restore'), findsOneWidget);
    });
  }

  testWidgets('holds up at tablet width', (tester) async {
    await pump(tester, size: const Size(834, 1112), textScale: 1.3);
    expect(tester.takeException(), isNull);
  });

  testWidgets('an admin adds a source by label', (tester) async {
    final fake = await pump(tester);
    await tester.tap(find.byTooltip('New source'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField), '  Spring fair ');
    await tester.tap(find.text('Save'));
    await tester.pumpAndSettle();

    expect(fake.added, ['Spring fair']);
    expect(find.text('Source added'), findsOneWidget);
  });

  testWidgets('a label stops at the 64 characters the API takes', (
    tester,
  ) async {
    final fake = await pump(tester);
    await tester.tap(find.byTooltip('New source'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField), 'x' * 80);
    await tester.tap(find.text('Save'));
    await tester.pumpAndSettle();

    expect(fake.added, ['x' * 64]);
  });

  testWidgets('an admin retires and moves one', (tester) async {
    final fake = await pump(tester);
    await tester.tap(find.text('Retire').first);
    await tester.pumpAndSettle();
    expect(fake.activations, [('s1', false)]);

    await tester.tap(find.byTooltip('Move Call down'));
    await tester.pumpAndSettle();
    expect(fake.moves, [('call', 1)]);
  });

  testWidgets('a member reads the list and is offered no write', (
    tester,
  ) async {
    await pump(tester, admin: false);
    expect(find.text('Call'), findsOneWidget);
    expect(find.byTooltip('New source'), findsNothing);
    expect(find.text('Rename'), findsNothing);
    expect(find.text('Retire'), findsNothing);
  });

  testWidgets('an older API shows its fixed list and no controls', (
    tester,
  ) async {
    await pump(tester, given: const LeadSourcesAnswer.legacy());
    expect(find.textContaining('fixed list of lead sources'), findsOneWidget);
    expect(find.text('Campaign'), findsOneWidget);
    expect(find.byTooltip('New source'), findsNothing);
    expect(find.text('Rename'), findsNothing);
  });
}

class _FakeSources extends LeadSourcesNotifier {
  _FakeSources(this.answer);

  final LeadSourcesAnswer answer;
  final List<String> added = [];
  final List<(String, bool)> activations = [];
  final List<(String, int)> moves = [];

  @override
  Future<LeadSourcesAnswer> build() async => answer;

  @override
  Future<String?> add(String label) async {
    added.add(label);
    return null;
  }

  @override
  Future<String?> setActive(String id, bool active) async {
    activations.add((id, active));
    return null;
  }

  @override
  Future<String?> move(String key, int step) async {
    moves.add((key, step));
    return null;
  }
}
