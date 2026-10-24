import 'package:flutter/widgets.dart';

import '../data/models/interaction.dart';

/// A tap on Call, WhatsApp, SMS or Email that may be logged once the app is
/// back in front.
class PendingTap {
  const PendingTap({
    required this.kind,
    required this.target,
    required this.personName,
    required this.tappedAt,
  });

  final InteractionKind kind;
  final InteractionTarget target;

  /// Who was called or written to, for "Log this call to Maria?".
  final String personName;
  final DateTime tappedAt;
}

/// Decides when a tap is offered for logging: on the first return to the app
/// after it left, within [window] of the tap, at most once, and only to the
/// screen that armed it.
class TapLogTracker {
  static const window = Duration(hours: 2);

  /// A resume this long after the tap, with no departure seen, means the tap
  /// went nowhere (a dismissed chooser or cancelled prompt).
  static const grace = Duration(seconds: 3);

  PendingTap? _pending;
  Object? _owner;
  bool _left = false;

  @visibleForTesting
  PendingTap? get pending => _pending;

  /// Replaces any earlier tap, wherever it was armed.
  void arm(PendingTap tap, {required Object owner}) {
    _pending = tap;
    _owner = owner;
    _left = false;
  }

  /// With an [owner], only drops a tap that owner armed.
  void disarm({Object? owner}) {
    if (owner != null && !identical(owner, _owner)) return;
    _pending = null;
    _owner = null;
    _left = false;
  }

  /// The tap to offer [owner] at this change of [state], or null.
  ///
  /// A resume without leaving (a chooser or a system dialog dismissed) keeps
  /// the tap waiting for [grace], then drops it. A return later than [window], or before the tap by the
  /// clock, drops it for good.
  PendingTap? onState(
    AppLifecycleState state,
    DateTime now, {
    required Object owner,
  }) {
    final tap = _pending;
    if (tap == null) return null;
    if (state == AppLifecycleState.hidden ||
        state == AppLifecycleState.paused) {
      _left = true;
      return null;
    }
    if (state != AppLifecycleState.resumed) return null;
    if (!_left) {
      if (now.difference(tap.tappedAt) > grace) disarm();
      return null;
    }
    if (!identical(owner, _owner)) return null;
    disarm();
    final away = now.difference(tap.tappedAt);
    if (away.isNegative || away > window) return null;
    return tap;
  }
}

/// `https://wa.me/<digits>?text=Hi%20<first name>%2C`, or null when there is
/// no E.164 number to send to. The same test as the web's `whatsappHref`.
Uri? whatsAppUri(String? phoneE164, String firstName) {
  final e164 = (phoneE164 ?? '').trim();
  if (!RegExp(r'^\+[1-9]\d{6,14}$').hasMatch(e164)) return null;
  final digits = e164.substring(1);
  final name = firstName.trim();
  final greeting = name.isEmpty ? 'Hi,' : 'Hi $name,';
  return Uri.parse(
    'https://wa.me/$digits?text=${Uri.encodeComponent(greeting)}',
  );
}
