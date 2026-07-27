import 'package:bottle_crm/core/theme/theme.dart';
import 'package:bottle_crm/data/models/auth_response.dart';
import 'package:bottle_crm/data/models/models.dart';
import 'package:bottle_crm/providers/auth_provider.dart';
import 'package:bottle_crm/providers/deals_provider.dart';
import 'package:bottle_crm/screens/deals/deals_list_screen.dart';
import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('DealsListScreen', () {
    testWidgets('shows closed lost deals in list view', (tester) async {
      final dealsNotifier = _FakeDealsNotifier(
        DealsListData(deals: [_deal(stage: DealStage.closedLost)]),
      );

      await tester.pumpWidget(_testApp(dealsNotifier));
      await _switchToListView(tester);

      expect(find.text('Closed Lost'), findsOneWidget);
      expect(find.text('Closed Lost Deal'), findsOneWidget);
    });

    testWidgets('updates the deal stage when a card is dropped on a column', (
      tester,
    ) async {
      tester.view.physicalSize = const Size(1600, 1000);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);

      final dealsNotifier = _FakeDealsNotifier(
        DealsListData(deals: [_deal(stage: DealStage.prospecting)]),
      );

      await tester.pumpWidget(_testApp(dealsNotifier));
      await tester.pumpAndSettle();

      await _dragDealToStage(tester, 'Prospecting Deal', DealStage.qualified);

      expect(dealsNotifier.stageUpdates, [
        ('deal-prospecting', DealStage.qualified),
      ]);
    });

    testWidgets('clears the selection after a successful move', (tester) async {
      tester.view.physicalSize = const Size(1600, 1000);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);

      final dealsNotifier = _FakeDealsNotifier(
        DealsListData(deals: [_deal(stage: DealStage.prospecting)]),
      );

      await tester.pumpWidget(_testApp(dealsNotifier));
      await tester.pumpAndSettle();

      // Picking a card up selects it (LongPressDraggable.onDragStarted), so a
      // completed move must not leave the selection app bar stranded.
      await _dragDealToStage(tester, 'Prospecting Deal', DealStage.qualified);

      expect(dealsNotifier.stageUpdates, [
        ('deal-prospecting', DealStage.qualified),
      ]);
      expect(find.text('1 selected'), findsNothing);
    });

    testWidgets('keeps the selection when a move fails', (tester) async {
      tester.view.physicalSize = const Size(1600, 1000);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);

      final dealsNotifier = _FakeDealsNotifier(
        DealsListData(deals: [_deal(stage: DealStage.prospecting)]),
        updateError: 'Network unreachable',
      );

      await tester.pumpWidget(_testApp(dealsNotifier));
      await tester.pumpAndSettle();

      await _dragDealToStage(tester, 'Prospecting Deal', DealStage.qualified);

      expect(find.text('1 selected'), findsOneWidget);
    });

    testWidgets('loads the next page when list view is scrolled near the end', (
      tester,
    ) async {
      final dealsNotifier = _FakeDealsNotifier(
        DealsListData(
          deals: List.generate(
            20,
            (index) => _deal(
              id: 'deal-$index',
              title: 'Prospecting Deal $index',
              stage: DealStage.prospecting,
            ),
          ),
          totalCount: 40,
          hasMore: true,
          currentOffset: 20,
        ),
      );

      await tester.pumpWidget(_testApp(dealsNotifier));
      await _switchToListView(tester);

      await tester.drag(find.byType(ListView), const Offset(0, -3000));
      await tester.pumpAndSettle();

      expect(dealsNotifier.loadMoreCalls, 1);
    });
  });
}

Widget _testApp(_FakeDealsNotifier dealsNotifier) {
  return ProviderScope(
    overrides: [
      authProvider.overrideWith(() => _FakeAuthNotifier()),
      dealsProvider.overrideWith(() => dealsNotifier),
    ],
    child: MaterialApp(theme: AppTheme.light, home: const DealsListScreen()),
  );
}

Future<void> _switchToListView(WidgetTester tester) async {
  await tester.tap(find.byType(IconButton).at(1));
  await tester.pumpAndSettle();
}

Future<void> _dragDealToStage(
  WidgetTester tester,
  String dealTitle,
  DealStage targetStage,
) async {
  final dealCenter = tester.getCenter(find.text(dealTitle));
  final targetRect = tester.getRect(
    find.byType(DragTarget<Deal>).at(targetStage.stageIndex),
  );
  final targetPoint = Offset(targetRect.left + 48, targetRect.top + 120);

  final gesture = await tester.startGesture(dealCenter);
  await tester.pump(kLongPressTimeout + const Duration(milliseconds: 100));
  await gesture.moveTo(targetPoint);
  await tester.pump();
  await gesture.up();
  await tester.pumpAndSettle();
}

Deal _deal({String? id, String? title, required DealStage stage}) {
  final suffix = stage.label.replaceAll(' ', '-').toLowerCase();
  return Deal(
    id: id ?? 'deal-$suffix',
    title: title ?? '${stage.label} Deal',
    value: 100000,
    stage: stage,
    probability: stage.defaultProbability,
    closeDate: DateTime(2026, 6, 1),
    companyName: 'Acme Inc',
    assignedTo: 'user-1',
    priority: Priority.medium,
    createdAt: DateTime(2026, 5, 1),
    updatedAt: DateTime(2026, 5, 1),
  );
}

class _FakeDealsNotifier extends DealsNotifier {
  _FakeDealsNotifier(this.initialData, {this.updateError});

  final DealsListData initialData;
  final String? updateError;
  final List<(String id, DealStage stage)> stageUpdates = [];
  int loadMoreCalls = 0;

  @override
  Future<DealsListData> build() async => initialData;

  @override
  Future<void> refresh({String? search, String? stage}) async {}

  @override
  Future<void> loadMore({String? search, String? stage}) async {
    loadMoreCalls += 1;
  }

  @override
  Future<({String? error, bool success})> updateDealStage(
    String id,
    DealStage stage,
  ) async {
    stageUpdates.add((id, stage));
    if (updateError != null) {
      return (success: false, error: updateError);
    }
    return (success: true, error: null);
  }
}

class _FakeAuthNotifier extends AuthNotifier {
  @override
  AuthState build() {
    const org = Organization(
      id: 'org-1',
      name: 'Test Org',
      currencySymbol: r'$',
    );

    return AuthState(
      user: const AuthUser(id: 'user-1', email: 'user@example.com'),
      organizations: [org],
      selectedOrganization: org,
      isAuthenticated: true,
    );
  }
}
