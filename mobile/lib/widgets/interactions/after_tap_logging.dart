import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../data/models/interaction.dart';
import '../../providers/interactions_provider.dart';
import '../../services/after_tap.dart';
import 'log_interaction_sheet.dart';

/// Call, WhatsApp, SMS and Email taps that offer "Log this call to Maria?"
/// when the app comes back, for a screen holding such buttons.
///
/// The length of a call is an estimate from the time away: Android's call log
/// is off limits under Google Play policy.
mixin AfterTapLogging<T extends ConsumerStatefulWidget> on ConsumerState<T> {
  late final TapLogTracker _tapTracker;
  late final AppLifecycleListener _tapLifecycle;

  @override
  void initState() {
    super.initState();
    _tapTracker = ref.read(tapLogTrackerProvider);
    _tapLifecycle = AppLifecycleListener(onStateChange: _onTapLifecycle);
  }

  @override
  void dispose() {
    _tapLifecycle.dispose();
    _tapTracker.disarm(owner: this);
    super.dispose();
  }

  /// Runs once a logged interaction is saved, for the screen to reload.
  void onInteractionLogged() {}

  Future<void> launchAndOfferLog(
    Uri uri, {
    required InteractionKind kind,
    required InteractionTarget target,
    required String personName,
    LaunchMode mode = LaunchMode.platformDefault,
  }) async {
    // Armed before the launch, since the app can leave before it returns.
    _tapTracker.arm(
      PendingTap(
        kind: kind,
        target: target,
        personName: personName,
        tappedAt: ref.read(clockProvider)(),
      ),
      owner: this,
    );
    var opened = false;
    try {
      opened = await launchUrl(uri, mode: mode);
    } catch (_) {}
    if (opened) return;
    _tapTracker.disarm(owner: this);
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Could not open ${uri.scheme}'),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  void _onTapLifecycle(AppLifecycleState state) {
    final now = ref.read(clockProvider)();
    final tap = _tapTracker.onState(state, now, owner: this);
    if (tap != null) _offerLog(tap, now.difference(tap.tappedAt));
  }

  Future<void> _offerLog(PendingTap tap, Duration away) async {
    // Under another route or in a background tab, the tap is dropped unseen.
    if (!mounted || !TickerMode.valuesOf(context).enabled) return;
    final keepAlive = ref.listenManual(
      recordInteractionsProvider(tap.target),
      (_, _) {},
    );
    RecordInteractions? answer;
    try {
      answer = await ref.read(recordInteractionsProvider(tap.target).future);
    } catch (_) {
      // Not knowing is not a "no": a failed save says what went wrong.
    } finally {
      keepAlive.close();
    }
    if (!mounted || answer?.offered == false) return;
    final saved = await showLogInteractionSheet(
      context,
      target: tap.target,
      save: (draft) => saveInteraction(ref, draft),
      clock: ref.read(clockProvider),
      tap: tap,
      away: away,
    );
    if (saved && mounted) onInteractionLogged();
  }
}

/// "Log activity" from a record's timeline, for something done elsewhere.
Future<bool> logActivity(
  BuildContext context,
  WidgetRef ref,
  InteractionTarget target,
) {
  return showLogInteractionSheet(
    context,
    target: target,
    save: (draft) => saveInteraction(ref, draft),
    clock: ref.read(clockProvider),
  );
}
