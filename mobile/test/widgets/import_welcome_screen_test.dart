import 'dart:convert';
import 'dart:typed_data';

import 'package:bottle_crm/data/models/dashboard_data.dart';
import 'package:bottle_crm/providers/contacts_provider.dart';
import 'package:bottle_crm/providers/dashboard_provider.dart';
import 'package:bottle_crm/providers/leads_provider.dart';
import 'package:bottle_crm/routes/app_router.dart';
import 'package:bottle_crm/screens/onboarding/import_welcome_screen.dart';
import 'package:bottle_crm/services/api_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:http/http.dart' as http;
import '../helpers/fake_platform_file.dart';

/// The first screen after creating a workspace (the web's `/welcome`).
class _QueueClient extends http.BaseClient {
  final List<(int, String)> replies = [];
  final List<http.BaseRequest> requests = [];

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    requests.add(request);
    await request.finalize().toBytes();
    final (status, body) = replies.removeAt(0);
    return http.StreamedResponse(
      Stream.value(utf8.encode(body)),
      status,
      request: request,
    );
  }
}

String _mappedBody({
  int valid = 2,
  List<Map<String, Object?>> skipped = const [],
}) => jsonEncode({
  'columns': [
    {
      'index': 0,
      'header': 'Name',
      'field': 'full_name',
      'samples': ['Plato'],
    },
  ],
  'fields': [
    {'name': 'full_name', 'label': 'Full name', 'required': false},
  ],
  'valid': [
    for (var i = 1; i <= valid; i++)
      {'row': i, 'first_name': 'Person', 'last_name': '$i'},
  ],
  'skipped': skipped,
  'dropped': [],
  'summary': {
    'total': valid + skipped.length,
    'valid': valid,
    'skipped': skipped.length,
  },
});

const _created = '{"error": false, "created": 2, "ids": ["a", "b"]}';

int _contactsBuilds = 0;
int _leadsBuilds = 0;
int _dashboardBuilds = 0;

class _Contacts extends ContactsNotifier {
  @override
  Future<ContactsListData> build() async {
    _contactsBuilds++;
    return const ContactsListData();
  }
}

class _Leads extends LeadsNotifier {
  @override
  Future<LeadsListData> build() async {
    _leadsBuilds++;
    return const LeadsListData(hasMore: false);
  }
}

class _Dashboard extends DashboardNotifier {
  @override
  Future<DashboardData> build() async {
    _dashboardBuilds++;
    return const DashboardData();
  }
}

/// Stands in for a real screen, and watches its provider the way that
/// screen does, so a refresh shows up as a rebuild.
class _Stub extends ConsumerWidget {
  const _Stub(this.label, this.watch);

  final String label;
  final void Function(WidgetRef ref) watch;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    watch(ref);
    return Scaffold(appBar: AppBar(), body: Text(label));
  }
}

void main() {
  late _QueueClient client;

  setUp(() {
    client = _QueueClient();
    ApiService().setClientForTesting(client);
    _contactsBuilds = 0;
    _leadsBuilds = 0;
    _dashboardBuilds = 0;
  });

  void useSize(WidgetTester tester, Size size, {double textScale = 1.0}) {
    tester.view.devicePixelRatio = 3.0;
    tester.view.physicalSize = size * 3;
    tester.platformDispatcher.textScaleFactorTestValue = textScale;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
  }

  /// The screen at its route, with the three places it can send someone.
  Future<(GoRouter, ProviderContainer)> pumpWelcome(
    WidgetTester tester, {
    Size size = const Size(390, 844),
    double textScale = 1.0,
    String fileName = 'people.xlsx',
  }) async {
    useSize(tester, size, textScale: textScale);
    final bytes = Uint8List.fromList(utf8.encode('Name\nPlato\n'));
    final router = GoRouter(
      initialLocation: AppRoutes.importWelcome,
      routes: [
        GoRoute(
          path: AppRoutes.dashboard,
          builder: (_, _) =>
              _Stub('the dashboard', (ref) => ref.watch(dashboardProvider)),
        ),
        GoRoute(
          path: AppRoutes.importWelcome,
          builder: (_, _) => ImportWelcomeScreen(
            pickFile: () async => FakePlatformFile(
              name: fileName,
              size: bytes.length,
              bytes: bytes,
            ),
          ),
        ),
        GoRoute(
          path: AppRoutes.contacts,
          builder: (_, _) =>
              _Stub('the contacts list', (ref) => ref.watch(contactsProvider)),
        ),
        GoRoute(
          path: AppRoutes.leads,
          builder: (_, _) =>
              _Stub('the leads list', (ref) => ref.watch(leadsProvider)),
        ),
      ],
    );
    final container = ProviderContainer(
      overrides: [
        contactsProvider.overrideWith(_Contacts.new),
        leadsProvider.overrideWith(_Leads.new),
        dashboardProvider.overrideWith(_Dashboard.new),
      ],
    );
    addTearDown(container.dispose);
    await tester.pumpWidget(
      UncontrolledProviderScope(
        container: container,
        child: MaterialApp.router(routerConfig: router),
      ),
    );
    await tester.pumpAndSettle();
    return (router, container);
  }

  const contactsChoice = 'Customers and people you work with';
  const leadsChoice = "People you're trying to sell to";

  testWidgets('both choices open the import sheet for the right target', (
    tester,
  ) async {
    await pumpWelcome(tester);

    expect(find.text('Bring in your contacts'), findsOneWidget);
    expect(
      find.text('Upload a spreadsheet and we will match its columns for you.'),
      findsOneWidget,
    );
    expect(find.text('Import them as contacts.'), findsOneWidget);
    expect(find.text('Import them as leads to follow up.'), findsOneWidget);

    await tester.tap(find.text(contactsChoice));
    await tester.pumpAndSettle();
    expect(find.text('Import contacts'), findsOneWidget);
    expect(find.text('Choose a spreadsheet'), findsOneWidget);
    await tester.tap(find.byTooltip('Close'));
    await tester.pumpAndSettle();

    await tester.tap(find.text(leadsChoice));
    await tester.pumpAndSettle();
    expect(find.text('Import leads'), findsOneWidget);
    expect(find.text('Import contacts'), findsNothing);
  });

  testWidgets('Skip for now goes to the dashboard', (tester) async {
    final (router, _) = await pumpWelcome(tester);

    await tester.tap(find.text('Skip for now'));
    await tester.pumpAndSettle();

    expect(find.text('the dashboard'), findsOneWidget);
    expect(
      router.routerDelegate.currentConfiguration.uri.path,
      AppRoutes.dashboard,
    );
    expect(client.requests, isEmpty);
  });

  for (final (name, size) in [
    ('phone', const Size(390, 844)),
    ('small phone', const Size(320, 640)),
    ('tablet', const Size(1024, 768)),
  ]) {
    testWidgets('the screen fits at 1.3x text on a $name', (tester) async {
      await pumpWelcome(tester, size: size, textScale: 1.3);

      expect(tester.takeException(), isNull);
      for (final label in [contactsChoice, leadsChoice, 'Skip for now']) {
        expect(find.text(label), findsOneWidget);
        final box = tester.getRect(find.text(label));
        expect(box.right, lessThanOrEqualTo(size.width), reason: label);
      }
      // Each choice is a full tap target.
      for (final label in [contactsChoice, leadsChoice, 'Skip for now']) {
        final target = find.ancestor(
          of: find.text(label),
          matching: find.byWidgetPredicate(
            (w) => w is InkWell || w is ButtonStyleButton,
          ),
        );
        expect(
          tester.getSize(target.first).height,
          greaterThanOrEqualTo(44),
          reason: label,
        );
      }
      // A phone uses its width; a tablet keeps a readable column instead of
      // stretching the choices across the screen.
      final choice = tester.getSize(
        find
            .ancestor(
              of: find.text(contactsChoice),
              matching: find.byType(InkWell),
            )
            .first,
      );
      expect(
        choice.width,
        size.width > 600
            ? lessThanOrEqualTo(560)
            : greaterThan(size.width - 40),
      );
    });
  }

  testWidgets('importing contacts lands on the refreshed contacts list, with '
      'the dashboard behind it', (tester) async {
    final (router, container) = await pumpWelcome(tester);
    // Lists cached from before the import, which must not be shown as they
    // were.
    await container.read(contactsProvider.future);
    await container.read(dashboardProvider.future);
    client.replies
      ..add((200, _mappedBody()))
      ..add((200, _created));

    await tester.tap(find.text(contactsChoice));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Choose a spreadsheet'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Import 2 contacts'));
    await tester.pumpAndSettle();

    expect(
      client.requests.last.url.path,
      endsWith('/api/contacts/import/commit/'),
    );
    // The sheet says what was imported, and moves on only once it is closed.
    expect(find.text('Imported 2 contacts.'), findsOneWidget);
    expect(find.text('the contacts list'), findsNothing);

    await tester.tap(find.text('Done'));
    await tester.pumpAndSettle();

    expect(find.text('the contacts list'), findsOneWidget);
    expect(find.byType(SnackBar), findsNothing);
    expect(_contactsBuilds, 2);
    expect(_dashboardBuilds, 2);
    expect(router.canPop(), isTrue);

    router.pop();
    await tester.pumpAndSettle();
    expect(find.text('the dashboard'), findsOneWidget);
  });

  testWidgets('a contacts file with one-word names can go in as leads '
      'instead, and lands on the leads list', (tester) async {
    final (router, container) = await pumpWelcome(tester);
    await container.read(leadsProvider.future);
    client.replies
      ..add((
        200,
        _mappedBody(
          valid: 0,
          skipped: [
            {
              'row': 1,
              'field': 'last_name',
              'message': 'A contact needs a first and a last name.',
              'cells': ['Plato'],
              'kind': 'row',
            },
          ],
        ),
      ))
      ..add((200, _mappedBody(valid: 1)))
      ..add((200, '{"error": false, "created": 1, "ids": ["a"]}'));

    await tester.tap(find.text(contactsChoice));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Choose a spreadsheet'));
    await tester.pumpAndSettle();

    expect(
      find.textContaining('so this file could go in as leads instead'),
      findsOneWidget,
    );
    await tester.ensureVisible(find.text('Import as leads instead'));
    await tester.tap(find.text('Import as leads instead'));
    await tester.pumpAndSettle();

    // The same file, previewed again as leads, with a fresh guess.
    expect(client.requests[1].url.path, endsWith('/api/leads/import/preview/'));
    expect(
      (client.requests[1] as http.MultipartRequest).fields['mapping'],
      'auto',
    );
    expect(find.text('Import leads'), findsOneWidget);

    await tester.tap(find.text('Import 1 lead'));
    await tester.pumpAndSettle();

    expect(
      client.requests.last.url.path,
      endsWith('/api/leads/import/commit/'),
    );
    expect(find.text('Imported 1 lead.'), findsOneWidget);
    expect(find.text('the leads list'), findsNothing);

    await tester.tap(find.text('Done'));
    await tester.pumpAndSettle();

    expect(find.text('the leads list'), findsOneWidget);
    expect(find.byType(SnackBar), findsNothing);
    expect(_leadsBuilds, 2);
    expect(
      router.routerDelegate.currentConfiguration.uri.path,
      AppRoutes.leads,
    );
  });
}
