import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../config/api_config.dart';
import '../data/models/estimate.dart';
import '../data/models/invoice_report.dart';
import '../data/models/invoice_template.dart';
import '../data/models/product.dart';
import '../data/models/recurring_invoice.dart';
import '../services/api_service.dart';

/// The five smaller invoice surfaces: estimates, recurring schedules, the
/// product catalogue, PDF templates and the reports.
///
/// One file because each is a thin list over one endpoint sharing the same
/// `{count, next, results}` envelope and the same error handling. Splitting
/// them into five near-identical providers would be five copies of `_rows`
/// and `_message` to keep in step. Invoices itself stays separate: it has
/// paging, filters, totals and four writes.

/// The server's own message where there is one, since these endpoints refuse
/// for reasons the user can act on ("Only an administrator can change the
/// product catalog", "Estimate already converted to invoice").
String _message(dynamic response) {
  final errors = response.data?['errors'];
  if (errors is Map) {
    for (final value in errors.values) {
      if (value is List && value.isNotEmpty) return value.first.toString();
      if (value is String && value.trim().isNotEmpty) return value;
    }
  }
  final detail = response.data?['message'];
  if (detail is String && detail.trim().isNotEmpty) return detail;
  final raw = response.message as String?;
  return (raw == null || raw.trim().isEmpty) ? 'Something went wrong' : raw;
}

List<Map<String, dynamic>> _rows(Map<String, dynamic> body) {
  final results = body['results'];
  if (results is! List) return const [];
  return results.whereType<Map<String, dynamic>>().toList();
}

// ---------------------------------------------------------------------------
// Estimates
// ---------------------------------------------------------------------------

class EstimatesNotifier extends AsyncNotifier<List<Estimate>> {
  final ApiService _api = ApiService();

  String _search = '';
  EstimateStatus? _status;

  EstimateStatus? get status => _status;

  @override
  Future<List<Estimate>> build() => _fetch();

  Future<void> refresh() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(_fetch);
  }

  Future<void> search(String term) async {
    _search = term.trim();
    await refresh();
  }

  Future<void> filterByStatus(EstimateStatus? status) async {
    _status = status;
    await refresh();
  }

  Future<List<Estimate>> _fetch() async {
    final params = <String, String>{'limit': '50'};
    if (_search.isNotEmpty) params['search'] = _search;
    if (_status != null) params['status'] = _status!.value;

    final url = Uri.parse(
      ApiConfig.estimates,
    ).replace(queryParameters: params).toString();
    final response = await _api.get(url);
    if (!response.success || response.data == null) {
      throw Exception(response.message ?? 'Failed to load estimates');
    }
    return _rows(response.data!).map(Estimate.fromJson).toList(growable: false);
  }

  /// Raises an invoice from the estimate. Returns the new invoice's id on
  /// success so the caller can navigate straight to it, since converting and
  /// then hunting for the invoice is the whole point of the action.
  Future<({String? invoiceId, String? error})> convert(String id) async {
    final response = await _api.post(ApiConfig.estimateConvert(id), const {});
    if (!response.success) return (invoiceId: null, error: _message(response));
    await refresh();
    final invoice = response.data?['invoice'];
    final invoiceId = invoice is Map<String, dynamic>
        ? invoice['id']?.toString()
        : null;
    return (invoiceId: invoiceId, error: null);
  }

  Future<String?> send(String id) async {
    final response = await _api.post(ApiConfig.estimateSend(id), const {});
    if (!response.success) return _message(response);
    await refresh();
    return null;
  }
}

final estimatesProvider =
    AsyncNotifierProvider<EstimatesNotifier, List<Estimate>>(
      EstimatesNotifier.new,
    );

// ---------------------------------------------------------------------------
// Recurring schedules
// ---------------------------------------------------------------------------

class RecurringNotifier extends AsyncNotifier<List<RecurringInvoice>> {
  final ApiService _api = ApiService();

  /// Null shows both. The endpoint reads `is_active=true|false`.
  bool? _active;

  bool? get activeFilter => _active;

  @override
  Future<List<RecurringInvoice>> build() => _fetch();

  Future<void> refresh() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(_fetch);
  }

  Future<void> filterByActive(bool? active) async {
    _active = active;
    await refresh();
  }

  Future<List<RecurringInvoice>> _fetch() async {
    final params = <String, String>{'limit': '50'};
    if (_active != null) params['is_active'] = _active! ? 'true' : 'false';

    final url = Uri.parse(
      ApiConfig.recurringInvoices,
    ).replace(queryParameters: params).toString();
    final response = await _api.get(url);
    if (!response.success || response.data == null) {
      throw Exception(response.message ?? 'Failed to load schedules');
    }
    return _rows(
      response.data!,
    ).map(RecurringInvoice.fromJson).toList(growable: false);
  }

  /// Pauses a running schedule or resumes a paused one.
  ///
  /// The endpoint takes no target state, it flips whatever is stored, so this
  /// is not idempotent and a retry after an ambiguous failure would undo the
  /// change rather than repeat it. It is called from a single tap for that
  /// reason, never from a retry loop.
  Future<String?> toggle(String id) async {
    final response = await _api.post(ApiConfig.recurringToggle(id), const {});
    if (!response.success) return _message(response);
    await refresh();
    return null;
  }

  /// Creates a schedule. Returns null on success, the server's message
  /// otherwise.
  ///
  /// [payload] is passed through as built rather than reshaped here:
  /// `RecurringInvoiceCreateSerializer` is the only definition of what it
  /// accepts, and a second copy of that shape would drift from it.
  Future<String?> createSchedule(Map<String, dynamic> payload) async {
    final response = await _api.post(ApiConfig.recurringInvoices, payload);
    if (!response.success) return _message(response);
    await refresh();
    return null;
  }
}

final recurringProvider =
    AsyncNotifierProvider<RecurringNotifier, List<RecurringInvoice>>(
      RecurringNotifier.new,
    );

// ---------------------------------------------------------------------------
// Product catalogue
// ---------------------------------------------------------------------------

class ProductsNotifier extends AsyncNotifier<List<Product>> {
  final ApiService _api = ApiService();

  String _search = '';

  @override
  Future<List<Product>> build() => _fetch();

  Future<void> refresh() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(_fetch);
  }

  Future<void> search(String term) async {
    _search = term.trim();
    await refresh();
  }

  Future<List<Product>> _fetch() async {
    final params = <String, String>{'limit': '100'};
    if (_search.isNotEmpty) params['search'] = _search;

    final url = Uri.parse(
      ApiConfig.products,
    ).replace(queryParameters: params).toString();
    final response = await _api.get(url);
    if (!response.success || response.data == null) {
      throw Exception(response.message ?? 'Failed to load products');
    }
    return _rows(response.data!).map(Product.fromJson).toList(growable: false);
  }

  /// Writes are admin-only server-side. The screen hides the buttons from
  /// everyone else, and a non-admin who reaches them anyway gets the 403's own
  /// message rather than a generic failure.
  Future<String?> createProduct(Product product) async {
    final response = await _api.post(ApiConfig.products, product.toPayload());
    if (!response.success) return _message(response);
    await refresh();
    return null;
  }

  Future<String?> updateProduct(String id, Product product) async {
    final response = await _api.put(ApiConfig.product(id), product.toPayload());
    if (!response.success) return _message(response);
    await refresh();
    return null;
  }

  Future<String?> deleteProduct(String id) async {
    final response = await _api.delete(ApiConfig.product(id));
    if (!response.success) return _message(response);
    await refresh();
    return null;
  }
}

final productsProvider = AsyncNotifierProvider<ProductsNotifier, List<Product>>(
  ProductsNotifier.new,
);

// ---------------------------------------------------------------------------
// PDF templates, read-only
// ---------------------------------------------------------------------------

/// The catalogue only. There is no create, update or delete here on purpose:
/// a template's body is raw HTML and CSS that renders into a PDF server-side,
/// editing it is admin-only, and a two-pane markup editor is not a phone
/// screen. Mobile shows which templates exist and which is the default.
final invoiceTemplatesProvider = FutureProvider<List<InvoiceTemplate>>((
  ref,
) async {
  final response = await ApiService().get(
    '${ApiConfig.invoiceTemplates}?limit=50',
  );
  if (!response.success || response.data == null) {
    throw Exception(response.message ?? 'Failed to load templates');
  }
  return _rows(
    response.data!,
  ).map(InvoiceTemplate.fromJson).toList(growable: false);
});

// ---------------------------------------------------------------------------
// Reports
// ---------------------------------------------------------------------------

/// Both report calls together, since the screen shows both and neither is
/// useful alone.
class InvoiceReports {
  const InvoiceReports({required this.dashboard, required this.aging});

  final InvoiceDashboard dashboard;
  final AgingReport aging;
}

/// Thrown when the server refuses because the caller is not an admin, so the
/// screen can say that rather than showing a generic "could not load".
class ReportsForbidden implements Exception {
  const ReportsForbidden(this.message);
  final String message;

  @override
  String toString() => message;
}

final invoiceReportsProvider = FutureProvider<InvoiceReports>((ref) async {
  final api = ApiService();
  final dashboard = await api.get(ApiConfig.invoiceReportDashboard);
  if (dashboard.statusCode == 403) {
    throw ReportsForbidden(_message(dashboard));
  }
  if (!dashboard.success || dashboard.data == null) {
    throw Exception(dashboard.message ?? 'Failed to load reports');
  }

  final aging = await api.get(ApiConfig.invoiceReportAging);
  if (aging.statusCode == 403) {
    throw ReportsForbidden(_message(aging));
  }
  if (!aging.success || aging.data == null) {
    throw Exception(aging.message ?? 'Failed to load the ageing report');
  }

  return InvoiceReports(
    dashboard: InvoiceDashboard.fromJson(dashboard.data!),
    aging: AgingReport.fromJson(aging.data!),
  );
});
