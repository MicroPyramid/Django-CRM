import 'package:bottle_crm/data/models/lead_source.dart';
import 'package:bottle_crm/data/models/lookup_models.dart';
import 'package:bottle_crm/data/models/mailbox.dart';
import 'package:bottle_crm/providers/lead_sources_provider.dart';
import 'package:bottle_crm/providers/lookup_provider.dart';
import 'package:bottle_crm/screens/settings/mailbox_form_sheet.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

/// A mailbox whose default assignee was deactivated after being chosen.
///
/// The people picker lists active members only, so the stored assignee needs
/// an item of their own, and the server accepts that unchanged value back
/// (`InboundMailboxSerializer.validate_default_assignee_id`). Dropping it
/// would move the mailbox to unassigned as a side effect of editing anything
/// else on the sheet.
void main() {
  Mailbox mailbox({required bool active}) => Mailbox.fromJson({
    'id': 'm1',
    'address': 'help@acme.com',
    'provider': 'ses',
    'default_priority': 'Normal',
    'default_assignee': {
      'id': 'gone',
      'user_details': {'email': 'left@example.com', 'name': 'Left'},
      'role': 'USER',
      'is_active': active,
    },
  });

  Map<String, dynamic>? result;

  Widget app(Mailbox? existing) => ProviderScope(
    overrides: [
      usersProvider.overrideWithValue(const [
        UserLookup(
          id: 'p1',
          email: 'ada@example.com',
          name: 'Ada',
          role: 'ADMIN',
          isActive: true,
        ),
      ]),
    ],
    child: MaterialApp(
      home: Scaffold(
        body: Builder(
          builder: (context) => ElevatedButton(
            onPressed: () async {
              result = await showMailboxFormSheet(context, existing: existing);
            },
            child: const Text('open'),
          ),
        ),
      ),
    ),
  );

  Future<void> open(
    WidgetTester tester,
    Mailbox? existing, {
    double textScale = 1.0,
  }) async {
    result = null;
    tester.view.devicePixelRatio = 3.0;
    tester.view.physicalSize = const Size(390 * 3, 844 * 3);
    tester.platformDispatcher.textScaleFactorTestValue = textScale;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
    await tester.pumpWidget(app(existing));
    await tester.tap(find.text('open'));
    await tester.pumpAndSettle();
  }

  testWidgets('offers the deactivated assignee, labelled, with a note', (
    tester,
  ) async {
    await open(tester, mailbox(active: false));

    expect(tester.takeException(), isNull);
    expect(find.text('Left (deactivated)'), findsOneWidget);
    expect(
      find.textContaining('Deactivated users are not assigned'),
      findsOneWidget,
    );
  });

  testWidgets('the deactivated assignee survives a save', (tester) async {
    await open(tester, mailbox(active: false));

    await tester.ensureVisible(find.text('Save changes'));
    await tester.tap(find.text('Save changes'));
    await tester.pumpAndSettle();

    expect(result, isNotNull);
    expect(result!['default_assignee_id'], 'gone');
  });

  testWidgets('an active assignee missing from the list is not called '
      'deactivated', (tester) async {
    // What a picker that has not loaded yet looks like: the stored person is
    // absent from the list without having been deactivated.
    await open(tester, mailbox(active: true));

    expect(find.text('Left'), findsOneWidget);
    expect(find.text('Left (deactivated)'), findsNothing);
    expect(
      find.textContaining('Deactivated users are not assigned'),
      findsNothing,
    );
  });

  group('webhook secret', () {
    final secretField = find.byKey(const ValueKey('mailbox-webhook-secret'));

    Mailbox postmark({required bool stored}) => Mailbox.fromJson({
      'id': 'm1',
      'address': 'help@acme.com',
      'provider': 'postmark',
      'default_priority': 'Normal',
      'has_webhook_secret': stored,
    });

    testWidgets('is blank, says it is stored, and is not sent untouched', (
      tester,
    ) async {
      await open(tester, postmark(stored: true));
      expect(find.byKey(const ValueKey('mailbox-topic-arn')), findsNothing);
      expect(tester.widget<TextField>(secretField).controller!.text, '');
      expect(find.textContaining('A secret is stored'), findsOneWidget);

      await tester.ensureVisible(find.text('Save changes'));
      await tester.tap(find.text('Save changes'));
      await tester.pumpAndSettle();
      expect(result!.containsKey('webhook_secret'), isFalse);
    });

    testWidgets('sends what was typed, and shows the setup URL', (
      tester,
    ) async {
      await open(tester, postmark(stored: false));
      expect(find.textContaining('No secret is stored'), findsOneWidget);
      expect(find.byKey(const ValueKey('mailbox-setup-url')), findsOneWidget);
      expect(find.textContaining('postmark:<secret>@'), findsOneWidget);

      await tester.ensureVisible(secretField);
      await tester.enterText(secretField, ' s3cret ');
      await tester.ensureVisible(find.text('Save changes'));
      await tester.tap(find.text('Save changes'));
      await tester.pumpAndSettle();
      expect(result!['webhook_secret'], 's3cret');
    });
  });

  group('SNS Topic ARN', () {
    const arn = 'arn:aws:sns:us-east-1:123456789012:inbound';
    const other = 'arn:aws:sns:eu-west-1:123456789012:other';
    final topicField = find.byKey(const ValueKey('mailbox-topic-arn'));

    Mailbox pinned(String? topic) => Mailbox.fromJson({
      'id': 'm1',
      'address': 'help@acme.com',
      'provider': 'ses',
      'default_priority': 'Normal',
      'has_topic_arn': topic != null,
      'topic_arn': topic ?? '',
    });

    Future<void> save(WidgetTester tester, String label) async {
      await tester.ensureVisible(find.text(label));
      await tester.tap(find.text(label));
      await tester.pumpAndSettle();
    }

    testWidgets('is prefilled and left out of a save that did not touch it', (
      tester,
    ) async {
      await open(tester, pinned(arn));
      expect(find.widgetWithText(TextField, arn), findsOneWidget);

      await save(tester, 'Save changes');

      expect(result, isNotNull);
      expect(result!.containsKey('topic_arn'), isFalse);
    });

    testWidgets('sends a changed ARN', (tester) async {
      await open(tester, pinned(arn));
      await tester.enterText(topicField, ' $other ');
      await save(tester, 'Save changes');

      expect(result!['topic_arn'], other);
    });

    testWidgets('sends the empty string when cleared', (tester) async {
      await open(tester, pinned(arn));
      await tester.enterText(topicField, '');
      await save(tester, 'Save changes');

      expect(result!['topic_arn'], '');
    });

    testWidgets('a new address sends one only when entered', (tester) async {
      await open(tester, null);
      await tester.enterText(
        find.widgetWithText(TextField, 'Address'),
        'a@b.io',
      );
      await save(tester, 'Add address');
      expect(result!.containsKey('topic_arn'), isFalse);

      await tester.tap(find.text('open'));
      await tester.pumpAndSettle();
      await tester.enterText(
        find.widgetWithText(TextField, 'Address'),
        'a@b.io',
      );
      await tester.enterText(topicField, arn);
      await save(tester, 'Add address');
      expect(result!['topic_arn'], arn);
    });

    testWidgets('holds up at 390px and 1.3x text', (tester) async {
      await open(tester, pinned(arn), textScale: 1.3);

      expect(tester.takeException(), isNull);
      await tester.ensureVisible(topicField);
      await tester.pumpAndSettle();
      expect(tester.getSize(topicField).height, greaterThanOrEqualTo(44));
      expect(tester.getRect(topicField).right, lessThanOrEqualTo(390));
      expect(
        find.textContaining('Mail is accepted only from this exact topic'),
        findsOneWidget,
      );
      await save(tester, 'Save changes');
      expect(tester.takeException(), isNull);
      expect(result, isNotNull);
    });
  });

  group('lead addresses', () {
    Map<String, dynamic>? sent;

    Future<void> openLeads(
      WidgetTester tester, {
      Mailbox? existing,
      bool offered = true,
      String? domain,
      bool startAsLeads = false,
      double textScale = 1.0,
    }) async {
      sent = null;
      tester.view.devicePixelRatio = 3.0;
      tester.view.physicalSize = const Size(390 * 3, 844 * 3);
      tester.platformDispatcher.textScaleFactorTestValue = textScale;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            usersProvider.overrideWithValue(const []),
            leadSourcesProvider.overrideWith(_FakeSources.new),
          ],
          child: MaterialApp(
            home: Scaffold(
              body: Builder(
                builder: (context) => ElevatedButton(
                  onPressed: () async {
                    sent = await showMailboxFormSheet(
                      context,
                      existing: existing,
                      leadsOffered: offered,
                      generatedDomain: domain,
                      startAsLeads: startAsLeads,
                    );
                  },
                  child: const Text('open'),
                ),
              ),
            ),
          ),
        ),
      );
      await tester.tap(find.text('open'));
      await tester.pumpAndSettle();
    }

    Future<void> save(WidgetTester tester, String label) async {
      await tester.ensureVisible(find.text(label));
      await tester.tap(find.text(label));
      await tester.pumpAndSettle();
    }

    testWidgets('an older API gets the ticket form and no creates key', (
      tester,
    ) async {
      await openLeads(tester, offered: false);
      expect(find.byKey(const ValueKey('mailbox-creates')), findsNothing);
      await tester.enterText(
        find.widgetWithText(TextField, 'Address'),
        'help@acme.com',
      );
      await save(tester, 'Add address');
      expect(sent!.containsKey('creates'), isFalse);
      expect(sent!.containsKey('lead_source'), isFalse);
    });

    testWidgets('a new lead address sends creates and its source', (
      tester,
    ) async {
      await openLeads(tester, startAsLeads: true);
      expect(
        find.text('What a lead arrives with'.toUpperCase()),
        findsOneWidget,
      );
      expect(find.text('Priority'), findsNothing);
      await tester.enterText(
        find.widgetWithText(TextField, 'Address'),
        'leads@acme.com',
      );
      await tester.enterText(
        find.byKey(const ValueKey('mailbox-lead-source-detail')),
        'Zillow',
      );
      await save(tester, 'Add address');

      expect(sent!['creates'], 'leads');
      expect(sent!['lead_source'], 'email');
      expect(sent!['lead_source_detail'], 'Zillow');
      expect(sent!['address'], 'leads@acme.com');
    });

    testWidgets('Generate an address sends no address of its own', (
      tester,
    ) async {
      await openLeads(tester, startAsLeads: true, domain: 'in.example.com');
      expect(find.textContaining('in.example.com'), findsOneWidget);
      await tester.tap(find.text('Generate an address'));
      await tester.pumpAndSettle();
      expect(find.widgetWithText(TextField, 'Address'), findsNothing);
      await save(tester, 'Add address');

      expect(sent!['generate_address'], isTrue);
      expect(sent!.containsKey('address'), isFalse);
      expect(sent!.containsKey('topic_arn'), isFalse);
      expect(sent!['creates'], 'leads');
    });

    testWidgets('without a server domain there is nothing to generate', (
      tester,
    ) async {
      await openLeads(tester, startAsLeads: true);
      expect(find.text('Generate an address'), findsNothing);
    });

    testWidgets('an edit sends a source only when it changed', (tester) async {
      final existing = Mailbox.fromJson({
        'id': 'm1',
        'address': 'leads@acme.com',
        'provider': 'ses',
        'creates': 'leads',
        'lead_source': 'trade show',
        'lead_source_detail': 'Booth 4',
      });
      await openLeads(tester, existing: existing);
      // Kept as the server sent it, though the list does not have it.
      expect(find.text('trade show'), findsOneWidget);
      await save(tester, 'Save changes');

      expect(sent!.containsKey('creates'), isFalse);
      expect(sent!.containsKey('lead_source'), isFalse);
      expect(sent!.containsKey('lead_source_detail'), isFalse);
    });

    testWidgets('a server-made address is not editable and not sent', (
      tester,
    ) async {
      final existing = Mailbox.fromJson({
        'id': 'm1',
        'address': 'acme-x1y2z3@in.example.com',
        'provider': 'ses',
        'creates': 'leads',
        'lead_source': 'email',
        'is_generated': true,
      });
      await openLeads(tester, existing: existing, domain: 'in.example.com');
      expect(find.widgetWithText(TextField, 'Address'), findsNothing);
      await save(tester, 'Save changes');
      expect(sent!.containsKey('address'), isFalse);
      expect(sent!.containsKey('generate_address'), isFalse);
    });

    testWidgets('fits 390px at 1.3x text as a lead address', (tester) async {
      await openLeads(
        tester,
        startAsLeads: true,
        domain: 'in.example.com',
        textScale: 1.3,
      );
      expect(tester.takeException(), isNull);
      await save(tester, 'Add address');
      expect(tester.takeException(), isNull);
    });
  });
}

class _FakeSources extends LeadSourcesNotifier {
  @override
  Future<LeadSourcesAnswer> build() async => const LeadSourcesAnswer(
    sources: [
      LeadSource(id: 's1', key: 'email', label: 'Email'),
      LeadSource(id: 's2', key: 'referral', label: 'Referral'),
    ],
  );
}
