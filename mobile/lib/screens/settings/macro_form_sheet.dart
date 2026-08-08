import 'package:flutter/material.dart';

import '../../core/theme/theme.dart';
import '../../data/models/macro.dart';
import '../../providers/settings_provider.dart';

/// Write or edit a saved reply.
///
/// Returns the request body, or `null` if dismissed. [canCreateOrg] only
/// decides whether the "Everyone" choice is offered.
/// `_resolve_scope_and_owner` re-derives admin status from `request.profile`
/// and is what actually turns a non-admin's org-scope attempt into a 403.
Future<Map<String, dynamic>?> showMacroFormSheet(
  BuildContext context, {
  Macro? existing,
  required bool canCreateOrg,
  required List<MacroPlaceholder> placeholders,
}) {
  return showModalBottomSheet<Map<String, dynamic>>(
    context: context,
    isScrollControlled: true,
    builder: (context) => _MacroFormSheet(
      existing: existing,
      canCreateOrg: canCreateOrg,
      placeholders: placeholders,
    ),
  );
}

class _MacroFormSheet extends StatefulWidget {
  const _MacroFormSheet({
    this.existing,
    required this.canCreateOrg,
    required this.placeholders,
  });

  final Macro? existing;
  final bool canCreateOrg;
  final List<MacroPlaceholder> placeholders;

  @override
  State<_MacroFormSheet> createState() => _MacroFormSheetState();
}

class _MacroFormSheetState extends State<_MacroFormSheet> {
  late final TextEditingController _title;
  late final TextEditingController _body;
  late String _scope;
  String? _error;

  bool get _isCreate => widget.existing == null;

  @override
  void initState() {
    super.initState();
    final m = widget.existing;
    _title = TextEditingController(text: m?.title ?? '');
    _body = TextEditingController(text: m?.body ?? '');
    // A member has one option, so default to it rather than to a scope the
    // server would refuse.
    _scope =
        m?.scope ??
        (widget.canCreateOrg ? Macro.scopeOrg : Macro.scopePersonal);
  }

  @override
  void dispose() {
    _title.dispose();
    _body.dispose();
    super.dispose();
  }

  /// Drop a token into the body at the cursor. Typing `%customer_name%` on a
  /// phone keyboard is four mode switches, and a typo is not caught at save
  /// time: an unknown token renders literally into a reply to a customer.
  void _insert(String token) {
    final selection = _body.selection;
    final text = _body.text;
    final at = selection.isValid ? selection.start : text.length;
    final end = selection.isValid ? selection.end : text.length;
    final next = text.replaceRange(at, end, token);
    _body.value = TextEditingValue(
      text: next,
      selection: TextSelection.collapsed(offset: at + token.length),
    );
  }

  void _submit() {
    final problem = validateMacroDraft(
      title: _title.text,
      body: _body.text,
      scope: _scope,
    );
    if (problem != null) {
      setState(() => _error = problem);
      return;
    }
    Navigator.of(
      context,
    ).pop(macroPayload(title: _title.text, body: _body.text, scope: _scope));
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        left: 16,
        right: 16,
        top: 16,
        bottom: MediaQuery.of(context).viewInsets.bottom + 16,
      ),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              _isCreate ? 'New saved reply' : 'Edit ${widget.existing!.title}',
              style: AppTypography.h3.copyWith(fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _title,
              textCapitalization: TextCapitalization.sentences,
              maxLength: 255,
              decoration: const InputDecoration(
                labelText: 'Title',
                helperText: 'What you will look for in the reply box',
                border: OutlineInputBorder(),
                counterText: '',
              ),
            ),
            const SizedBox(height: 12),
            if (widget.canCreateOrg)
              DropdownButtonFormField<String>(
                initialValue: _scope,
                isExpanded: true,
                decoration: const InputDecoration(
                  labelText: 'Who can use it',
                  border: OutlineInputBorder(),
                ),
                items: const [
                  DropdownMenuItem(
                    value: Macro.scopeOrg,
                    child: Text('Everyone in the organization'),
                  ),
                  DropdownMenuItem(
                    value: Macro.scopePersonal,
                    child: Text('Just you'),
                  ),
                ],
                onChanged: (v) => setState(() => _scope = v ?? _scope),
              )
            else
              // Not a disabled control: a member has exactly one option, and
              // showing a greyed "Everyone" would advertise an action the
              // server answers 403 to.
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppColors.gray100,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  'Saved for you alone. An administrator writes the replies '
                  'the whole organization shares.',
                  style: AppTypography.caption.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
              ),
            const SizedBox(height: 12),
            TextField(
              controller: _body,
              textCapitalization: TextCapitalization.sentences,
              minLines: 5,
              maxLines: 12,
              decoration: const InputDecoration(
                labelText: 'Reply',
                alignLabelWithHint: true,
                border: OutlineInputBorder(),
              ),
            ),
            if (widget.placeholders.isNotEmpty) ...[
              const SizedBox(height: 12),
              Text(
                'Tap to insert',
                style: AppTypography.caption.copyWith(
                  color: AppColors.textSecondary,
                ),
              ),
              const SizedBox(height: 6),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  for (final placeholder in widget.placeholders)
                    Tooltip(
                      message: placeholder.resolves,
                      child: ActionChip(
                        label: Text(placeholder.token),
                        onPressed: () => _insert(placeholder.token),
                      ),
                    ),
                ],
              ),
            ],
            if (_error != null) ...[
              const SizedBox(height: 8),
              Text(
                _error!,
                style: AppTypography.caption.copyWith(
                  color: AppColors.danger600,
                ),
              ),
            ],
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: SizedBox(
                    height: 48,
                    child: OutlinedButton(
                      onPressed: () => Navigator.of(context).pop(),
                      child: const Text('Cancel'),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: SizedBox(
                    height: 48,
                    child: FilledButton(
                      onPressed: _submit,
                      child: Text(_isCreate ? 'Save reply' : 'Save changes'),
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
