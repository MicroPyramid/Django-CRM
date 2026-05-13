import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../config/api_config.dart';
import '../data/models/approval.dart';
import '../services/api_service.dart';

/// Filter bundle for the approvals inbox.
class ApprovalsQuery {
  final String state; // pending, approved, rejected, cancelled, all
  final bool mine;
  final String? caseId;

  const ApprovalsQuery({
    this.state = 'pending',
    this.mine = false,
    this.caseId,
  });
}

/// Approvals (Tier 3) — fetched on demand. Used by both the per-case panel
/// and the inbox screen.
class ApprovalsNotifier extends Notifier<List<Approval>> {
  final ApiService _api = ApiService();

  @override
  List<Approval> build() => const [];

  Future<void> fetch(ApprovalsQuery query) async {
    final params = <String, String>{};
    if (query.state.isNotEmpty) params['state'] = query.state;
    if (query.mine) params['mine'] = 'true';
    if (query.caseId != null) params['case'] = query.caseId!;

    final url = params.isEmpty
        ? ApiConfig.approvals
        : Uri.parse(ApiConfig.approvals)
            .replace(queryParameters: params)
            .toString();
    final response = await _api.get(url);
    if (!response.success || response.data == null) {
      state = const [];
      return;
    }
    final list = response.data!['approvals'] as List<dynamic>? ?? [];
    state = list
        .whereType<Map<String, dynamic>>()
        .map(Approval.fromJson)
        .toList();
  }

  Future<ApiResponse<Map<String, dynamic>>> requestApproval(
    String ticketId, {
    String note = '',
    String? ruleId,
  }) async {
    final body = <String, dynamic>{'note': note};
    if (ruleId != null) body['rule_id'] = ruleId;
    return _api.post(ApiConfig.ticketRequestApproval(ticketId), body);
  }

  Future<ApiResponse<Map<String, dynamic>>> approve(String id) {
    return _api.post(ApiConfig.approvalApprove(id), const {});
  }

  Future<ApiResponse<Map<String, dynamic>>> reject(
    String id,
    String reason,
  ) {
    return _api.post(ApiConfig.approvalReject(id), {'reason': reason});
  }

  Future<ApiResponse<Map<String, dynamic>>> cancel(String id) {
    return _api.post(ApiConfig.approvalCancel(id), const {});
  }
}

final approvalsProvider =
    NotifierProvider<ApprovalsNotifier, List<Approval>>(
      ApprovalsNotifier.new,
    );
