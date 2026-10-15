import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../config/api_config.dart';
import '../data/models/account_statement.dart';
import '../services/api_service.dart';

/// The account, and the period to show, or nulls for the server's default
/// (this month so far, in the org's day).
typedef StatementRequest = ({String accountId, String? start, String? end});

/// The server refused: 403 to a member (statements are admin-only), 400 for a
/// period it will not cover, 404 for an account this org does not have.
/// [message] is the server's own sentence.
class StatementRefusal implements Exception {
  const StatementRefusal(this.statusCode, this.message);

  final int statusCode;
  final String message;

  /// Retrying cannot turn this into a statement, so the screen offers none.
  bool get forbidden => statusCode == 403;

  @override
  String toString() => message;
}

/// A refusal is never retried: Riverpod's default would ask again up to ten
/// times for an answer that cannot change. Anything else (offline, a 500)
/// keeps the default backoff.
Duration? _retry(int count, Object error) => error is StatementRefusal
    ? null
    : ProviderContainer.defaultRetry(count, error);

final accountStatementProvider = FutureProvider.autoDispose
    .family<AccountStatement, StatementRequest>(retry: _retry, (
      ref,
      request,
    ) async {
      final response = await ApiService().get(
        ApiConfig.accountStatement(
          request.accountId,
          start: request.start,
          end: request.end,
        ),
      );
      if (response.success && response.data != null) {
        return AccountStatement.fromJson(response.data!);
      }
      if (const {400, 403, 404}.contains(response.statusCode)) {
        throw StatementRefusal(
          response.statusCode,
          response.message ?? 'Could not load the statement',
        );
      }
      throw Exception(response.message ?? 'Could not load the statement');
    });
