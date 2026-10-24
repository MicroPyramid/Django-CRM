import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../config/api_config.dart';
import '../data/api_envelope.dart';
import '../data/models/lead_intake.dart';
import '../services/api_service.dart';

/// The list answered 404: this API predates lead webhooks.
class LeadIntakesNotOffered implements Exception {
  const LeadIntakesNotOffered();

  @override
  String toString() => 'Lead webhooks are not available here.';
}

/// A key replace: the new key, shown once by the caller, or the error.
typedef IntakeKeyResult = ({String? key, String? error});

/// Lead webhooks. Every route is admin-only server-side, reads included, so
/// the screens never ask for a member. Creating one and editing its field
/// mapping are web only (`mobile/docs/PARITY.md`).
class LeadIntakesNotifier extends AsyncNotifier<List<LeadIntake>> {
  final ApiService _api = ApiService();

  @override
  Future<List<LeadIntake>> build() => _fetch();

  Future<List<LeadIntake>> _fetch() async {
    final response = await _api.get(ApiConfig.leadIntakes);
    if (response.statusCode == 404) throw const LeadIntakesNotOffered();
    final data = response.data;
    if (!response.success || data == null) {
      throw Exception(response.message ?? 'Could not load the webhooks.');
    }
    return listFromEnvelope(data, const [
      'intakes',
      'results',
    ]).map(LeadIntake.fromJson).toList(growable: false);
  }

  Future<void> refresh() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(_fetch);
  }

  /// Only `is_active` is sent. Null on success, else the sentence to show.
  Future<String?> setActive(String id, bool active) async {
    final response = await _api.patch(ApiConfig.leadIntake(id), {
      'is_active': active,
    });
    if (!response.success) {
      return response.message ?? 'Could not change the webhook.';
    }
    await refresh();
    return null;
  }

  /// The old key keeps working for seven days, server-side.
  Future<IntakeKeyResult> replaceKey(String id) async {
    final response = await _api.post(ApiConfig.leadIntakeKey(id), const {});
    final key = response.data?['key']?.toString();
    if (!response.success || key == null || key.isEmpty) {
      return (
        key: null,
        error: response.message ?? 'Could not replace the key.',
      );
    }
    await refresh();
    return (key: key, error: null);
  }
}

// No automatic retry: a 404 is an answer, not a fault to retry.
final leadIntakesProvider =
    AsyncNotifierProvider<LeadIntakesNotifier, List<LeadIntake>>(
      LeadIntakesNotifier.new,
      retry: (_, _) => null,
    );

bool leadIntakesNotOffered(AsyncValue<List<LeadIntake>> v) =>
    v.error is LeadIntakesNotOffered;

/// One webhook's newest 50 deliveries, newest first.
final leadIntakeDeliveriesProvider = FutureProvider.autoDispose
    .family<List<IntakeDelivery>, String>((ref, id) async {
      final response = await ApiService().get(
        ApiConfig.leadIntakeDeliveries(id),
      );
      final data = response.data;
      if (!response.success || data == null) {
        throw Exception(response.message ?? 'Could not load the deliveries.');
      }
      return listFromEnvelope(data, const [
        'deliveries',
        'results',
      ]).map(IntakeDelivery.fromJson).toList(growable: false);
    }, retry: (_, _) => null);
