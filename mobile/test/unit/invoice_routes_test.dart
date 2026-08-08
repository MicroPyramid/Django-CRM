import 'package:bottle_crm/routes/app_router.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

/// The five sibling invoice pages sit UNDER `/invoices/`, alongside the
/// `/invoices/:id` detail route.
///
/// go_router matches in declaration order, so `/invoices/:id` declared first
/// would match `/invoices/estimates` with `id == "estimates"`. That does not
/// fail loudly: the detail screen opens, asks the API for an invoice with the
/// id "estimates", gets a 404 and shows "Could not load this invoice". Every
/// sibling page would be quietly unreachable while the menu still linked to
/// them.
///
/// This pins the paths and their ordering in the route table so the next
/// person to add an `/invoices/<something>` page sees why the order matters.
void main() {
  const siblings = <String>[
    AppRoutes.invoiceNew,
    AppRoutes.estimates,
    AppRoutes.recurring,
    AppRoutes.products,
    AppRoutes.invoiceTemplates,
    AppRoutes.invoiceReports,
  ];

  group('the sibling paths', () {
    test('all sit under the invoices path', () {
      for (final path in siblings) {
        expect(path, startsWith('${AppRoutes.invoices}/'), reason: path);
      }
    });

    test('none of them contains a path parameter', () {
      // A literal segment is what makes the ordering rule work at all.
      for (final path in siblings) {
        expect(path, isNot(contains(':')), reason: path);
      }
    });

    test('each would otherwise be matched by the detail route', () {
      // The failure this ordering prevents, stated as an assertion: every one
      // of these is exactly one segment past /invoices, which is the shape
      // `/invoices/:id` matches.
      for (final path in siblings) {
        final tail = path.substring('${AppRoutes.invoices}/'.length);
        expect(tail, isNot(contains('/')), reason: path);
        expect(tail, isNotEmpty, reason: path);
      }
    });

    test('they are distinct from each other', () {
      expect(siblings.toSet(), hasLength(siblings.length));
    });
  });

  group('the nested new-schedule route', () {
    test('sits two segments deep, so /invoices/:id cannot shadow it', () {
      // Unlike the five single-segment siblings, `/invoices/recurring/new`
      // cannot be mistaken for an invoice id: `:id` matches one segment. It is
      // still declared above the detail route for consistency, but this is why
      // it is not in the `siblings` list above.
      final tail = AppRoutes.recurringNew.substring(
        '${AppRoutes.invoices}/'.length,
      );

      expect(tail.split('/'), hasLength(2));
      expect(AppRoutes.recurringNew, startsWith('${AppRoutes.recurring}/'));
    });

    test('is distinct from the recurring list it hangs off', () {
      expect(AppRoutes.recurringNew, isNot(AppRoutes.recurring));
    });
  });

  group('the template form routes', () {
    test('sit under the catalogue, two segments past /invoices', () {
      // Same reasoning as `recurring/new`: `:id` matches one segment, so
      // neither of these can be mistaken for an invoice id. That is why they
      // are absent from `siblings` rather than an oversight.
      for (final path in [
        AppRoutes.invoiceTemplateNew,
        AppRoutes.invoiceTemplateEdit,
      ]) {
        expect(
          path,
          startsWith('${AppRoutes.invoiceTemplates}/'),
          reason: path,
        );
      }
    });

    test('the create and edit paths cannot match each other', () {
      // `/invoices/templates/new` is two segments and
      // `/invoices/templates/:id/edit` is three, so declaration order between
      // the two does not matter. If the edit path ever loses its `/edit` tail,
      // it would swallow `new` as an id and this fails.
      expect(
        AppRoutes.invoiceTemplateNew.split('/'),
        isNot(hasLength(AppRoutes.invoiceTemplateEdit.split('/').length)),
      );
      expect(AppRoutes.invoiceTemplateEdit, endsWith('/edit'));
    });

    test('the helper builds the path the route declares', () {
      // A hand-built string here is how a link goes to a 404 that nothing
      // catches, since go_router answers an unmatched path at runtime.
      expect(
        AppRoutes.invoiceTemplateEditFor('abc-123'),
        AppRoutes.invoiceTemplateEdit.replaceFirst(':id', 'abc-123'),
      );
    });

    test('both are in the real router', () {
      final container = ProviderContainer();
      addTearDown(container.dispose);
      final order = _invoicePaths(
        container.read(appRouterProvider).configuration.routes,
      );

      expect(order, contains(AppRoutes.invoiceTemplateNew));
      expect(order, contains(AppRoutes.invoiceTemplateEdit));
    });
  });

  group('the detail route', () {
    test('takes a single :id segment', () {
      expect(AppRoutes.invoiceDetail, '${AppRoutes.invoices}/:id');
    });

    test('is declared after every sibling in the real router', () {
      // Read out of the GoRouter the app actually builds, not a hand-kept
      // list. A copy of the order would drift from the router and then assert
      // that the bug is absent while it is present.
      final container = ProviderContainer();
      addTearDown(container.dispose);
      final order = _invoicePaths(
        container.read(appRouterProvider).configuration.routes,
      );

      final detailAt = order.indexOf(AppRoutes.invoiceDetail);
      expect(
        detailAt,
        isNot(-1),
        reason: 'detail route missing from the table',
      );

      for (final path in siblings) {
        final siblingAt = order.indexOf(path);
        expect(siblingAt, isNot(-1), reason: '$path missing from the table');
        expect(
          siblingAt,
          lessThan(detailAt),
          reason:
              '$path is declared after /invoices/:id, so go_router would '
              'match it as an invoice id and the page would be unreachable',
        );
      }
    });
  });
}

/// Every `/invoices...` path in the route tree, in declaration order.
///
/// Walks nested routes too, so a sibling moved under a shell is still seen.
List<String> _invoicePaths(List<RouteBase> routes) {
  final found = <String>[];
  void walk(List<RouteBase> nodes) {
    for (final node in nodes) {
      if (node is GoRoute && node.path.startsWith(AppRoutes.invoices)) {
        found.add(node.path);
      }
      walk(node.routes);
    }
  }

  walk(routes);
  return found;
}
