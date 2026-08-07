import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/theme.dart';

/// Leaving a form that has been filled in.
///
/// THE TRAP THIS EXISTS TO CLOSE
/// Three screens already carried a discard prompt and it fired on none of
/// them. They wrote `canPop: !_hasUnsavedChanges`, which reads the flag once,
/// while `build` runs. Typing into a `TextFormField` rebuilds that field and
/// not its parent, so on a form that started empty `canPop` stays `true` for
/// the rest of its life and the system back gesture pops before
/// `onPopInvoked` is ever consulted. The dirty check was correct and simply
/// never ran.
///
/// So `canPop` is always `false` here and the decision happens in the
/// callback, where the state being read is the state as it is now. A form
/// cannot silently lose its guard by gaining a field that nobody remembered
/// to rebuild on.
///
/// The cost is the iOS interactive swipe-back and the Android predictive-back
/// preview on these five screens. Worth it: a form is exactly where an
/// accidental edge swipe is expensive.
///
/// Everything routes through `context.pop()`, which is a direct pop and so
/// bypasses `PopScope` entirely. That is what lets the AppBar chevron, the
/// Cancel link and a successful save all leave without re-asking.
class UnsavedChangesGuard extends StatelessWidget {
  const UnsavedChangesGuard({
    super.key,
    required this.hasUnsavedChanges,
    required this.child,
    this.isSaving = false,
  });

  /// Read when back is pressed, not when this widget builds. Pass a closure
  /// over the form's live state, never a captured bool.
  final bool Function() hasUnsavedChanges;

  /// While a save is in flight, back does nothing. Popping here would orphan
  /// the request and leave the user unsure whether the record was created.
  final bool isSaving;

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, result) async {
        if (didPop || isSaving) return;
        await leaveForm(context, hasUnsavedChanges: hasUnsavedChanges());
      },
      child: child,
    );
  }
}

/// Leaves the form, asking first if there is anything to lose.
///
/// Used by the AppBar chevron and the Cancel link as well as by the guard, so
/// all three routes out of a form behave the same. Before this, a screen could
/// prompt on the back gesture and discard silently on its own Cancel button.
Future<void> leaveForm(
  BuildContext context, {
  required bool hasUnsavedChanges,
}) async {
  if (!hasUnsavedChanges) {
    context.pop();
    return;
  }
  final discard = await confirmDiscard(context);
  if (discard && context.mounted) context.pop();
}

/// The prompt itself. Defaults to keeping the work: dismissing the dialog by
/// tapping outside returns null, which is read as "do not discard".
Future<bool> confirmDiscard(BuildContext context) async {
  final result = await showDialog<bool>(
    context: context,
    builder: (context) => AlertDialog(
      title: const Text('Discard changes?'),
      content: const Text(
        'You have unsaved changes. Are you sure you want to leave?',
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context, false),
          child: const Text('Cancel'),
        ),
        TextButton(
          onPressed: () => Navigator.pop(context, true),
          child: Text('Discard', style: TextStyle(color: AppColors.danger600)),
        ),
      ],
    ),
  );
  return result ?? false;
}
