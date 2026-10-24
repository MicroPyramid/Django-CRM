import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../config/api_config.dart';
import '../data/api_envelope.dart';
import '../data/models/interaction.dart';
import '../services/after_tap.dart';
import '../services/api_service.dart';
import 'dashboard_provider.dart';

class InteractionsApi {
  final ApiService _api = ApiService();

  /// The record's newest interactions (the API's default page of 50).
  Future<RecordInteractions> forRecord(InteractionTarget target) async {
    final response = await _api.get(
      ApiConfig.interactions,
      queryParams: {target.home.param: target.id},
    );
    if (response.statusCode == 404) {
      return const RecordInteractions.notOffered();
    }
    final data = response.data;
    if (!response.success || data == null) {
      throw Exception(response.message ?? 'Could not load the activity.');
    }
    final items = listFromEnvelope(data, const [
      'interactions',
      'results',
    ]).map(Interaction.fromJson).toList(growable: false);
    final count = data['count'];
    return RecordInteractions(
      items: items,
      count: count is num ? count.toInt() : items.length,
    );
  }

  /// Null when saved, else the sentence to show.
  Future<String?> log(InteractionDraft draft) async {
    final response = await _api.post(ApiConfig.interactions, draft.toJson());
    if (response.success) return null;
    if (response.statusCode == 404) {
      return 'This record is no longer available to you.';
    }
    return response.message ?? 'Could not log this. Try again.';
  }
}

final interactionsApiProvider = Provider<InteractionsApi>(
  (ref) => InteractionsApi(),
);

// No automatic retry: a 404 is an answer, not a fault to retry.
final recordInteractionsProvider = FutureProvider.autoDispose
    .family<RecordInteractions, InteractionTarget>(
      (ref, target) => ref.watch(interactionsApiProvider).forRecord(target),
      retry: (_, _) => null,
    );

/// Logs [draft], then has the record's timeline and the home screen's
/// unanswered count asked again. Null when saved, else the sentence to show.
Future<String?> saveInteraction(WidgetRef ref, InteractionDraft draft) async {
  final error = await ref.read(interactionsApiProvider).log(draft);
  if (error != null) return error;
  ref.invalidate(recordInteractionsProvider(draft.target));
  if (draft.target.home == InteractionHome.lead) {
    ref.invalidate(dashboardProvider);
  }
  return null;
}

/// The one tap waiting to be logged, app-wide, so a newer tap replaces it.
final tapLogTrackerProvider = Provider<TapLogTracker>((ref) => TapLogTracker());

/// The wall clock the after-tap sheet reads. Wall time on purpose: a phone
/// asleep through a long call still counts toward the two hours.
final clockProvider = Provider<DateTime Function()>((ref) => DateTime.now);
