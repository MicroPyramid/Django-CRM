import 'package:bottle_crm/providers/contacts_provider.dart';
import 'package:bottle_crm/providers/leads_provider.dart';
import 'package:bottle_crm/routes/app_router.dart';
import 'package:bottle_crm/screens/contacts/contacts_list_screen.dart';
import 'package:bottle_crm/screens/leads/leads_list_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

/// An empty Contacts or Leads list is where a new workspace looks first, so
/// both offer the import there, as the web's empty states do. A list that is
/// only empty because of a search or a filter does not: importing is not the
/// answer to "nothing matches".
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  Future<void> pump(WidgetTester tester, Widget screen) async {
    tester.view.devicePixelRatio = 3.0;
    tester.view.physicalSize = const Size(390 * 3, 844 * 3);
    tester.platformDispatcher.textScaleFactorTestValue = 1.3;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          contactsProvider.overrideWith(_NoContacts.new),
          leadsProvider.overrideWith(_NoLeads.new),
        ],
        child: MaterialApp(home: screen),
      ),
    );
    await tester.pumpAndSettle();
  }

  testWidgets('an empty contacts list offers the import', (tester) async {
    await pump(tester, const ContactsListScreen());

    expect(tester.takeException(), isNull);
    expect(find.text('No contacts yet'), findsOneWidget);
    final button = find.ancestor(
      of: find.text('Import contacts'),
      matching: find.byWidgetPredicate((w) => w is ButtonStyleButton),
    );
    expect(tester.getSize(button).height, greaterThanOrEqualTo(44));

    await tester.tap(find.text('Import contacts'));
    await tester.pumpAndSettle();

    expect(find.text('Choose a spreadsheet'), findsOneWidget);
  });

  testWidgets('a contacts search with no matches does not', (tester) async {
    await pump(tester, const ContactsListScreen());

    await tester.enterText(find.byType(TextField), 'zz');
    await tester.pump(const Duration(milliseconds: 300));
    await tester.pumpAndSettle();

    expect(find.text('No contacts match that search'), findsOneWidget);
    expect(find.text('Import contacts'), findsNothing);
  });

  testWidgets('an empty leads list offers the import beside Add Lead', (
    tester,
  ) async {
    await pump(tester, const LeadsListScreen());

    expect(tester.takeException(), isNull);
    expect(find.text('No leads yet'), findsOneWidget);
    expect(find.text('Add Lead'), findsOneWidget);
    final button = find.ancestor(
      of: find.text('Import'),
      matching: find.byWidgetPredicate((w) => w is ButtonStyleButton),
    );
    expect(tester.getSize(button).height, greaterThanOrEqualTo(44));

    await tester.tap(find.text('Import'));
    await tester.pumpAndSettle();

    expect(find.text('Import leads'), findsOneWidget);
    expect(find.text('Choose a spreadsheet'), findsOneWidget);
  });

  testWidgets('a filtered leads list with no matches does not', (tester) async {
    await pump(tester, const LeadsListScreen(initialView: AppRoutes.viewHot));

    expect(find.text('No leads match'), findsOneWidget);
    expect(find.text('Clear filters'), findsOneWidget);
    expect(find.text('Import'), findsNothing);
  });
}

class _NoContacts extends ContactsNotifier {
  @override
  Future<ContactsListData> build() async => const ContactsListData();

  // A new value rather than the const one, as a real fetch makes, so the
  // screen hears about it.
  @override
  Future<void> search(String term) async =>
      state = AsyncData(ContactsListData(offset: term.length));
}

class _NoLeads extends LeadsNotifier {
  @override
  Future<LeadsListData> build() async => const LeadsListData(hasMore: false);

  @override
  Future<void> setFilters(LeadFilters filters) async {}
}
