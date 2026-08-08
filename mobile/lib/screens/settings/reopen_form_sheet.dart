import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../core/theme/theme.dart';
import '../../data/models/reopen_policy.dart';

/// Edit the org's reopen policy.
///
/// Returns the request body, or `null` if dismissed. All four fields go every
/// time: the form edits all four at once, and a partial body would make
/// "switched off" and "not sent" the same thing for the two booleans.
Future<Map<String, dynamic>?> showReopenFormSheet(
  BuildContext context,
  ReopenPolicy policy,
) {
  return showModalBottomSheet<Map<String, dynamic>>(
    context: context,
    isScrollControlled: true,
    builder: (context) => _ReopenFormSheet(policy: policy),
  );
}

class _ReopenFormSheet extends StatefulWidget {
  const _ReopenFormSheet({required this.policy});

  final ReopenPolicy policy;

  @override
  State<_ReopenFormSheet> createState() => _ReopenFormSheetState();
}

class _ReopenFormSheetState extends State<_ReopenFormSheet> {
  late final TextEditingController _window;
  late bool _isEnabled;
  late bool _notifyAssigned;
  late String _status;
  String? _error;

  @override
  void initState() {
    super.initState();
    _window = TextEditingController(text: '${widget.policy.windowDays}');
    _isEnabled = widget.policy.isEnabled;
    _notifyAssigned = widget.policy.notifyAssigned;
    _status = widget.policy.reopenToStatus;
  }

  @override
  void dispose() {
    _window.dispose();
    super.dispose();
  }

  void _submit() {
    final days = int.tryParse(_window.text.trim());
    final problem = reopenPolicyProblem(
      windowDays: days,
      reopenToStatus: _status,
    );
    if (problem != null) {
      setState(() => _error = problem);
      return;
    }
    Navigator.of(context).pop(
      reopenPolicyPayload(
        isEnabled: _isEnabled,
        windowDays: days!,
        reopenToStatus: _status,
        notifyAssigned: _notifyAssigned,
      ),
    );
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
              'Reopen policy',
              style: AppTypography.h3.copyWith(fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 12),
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              value: _isEnabled,
              onChanged: (v) => setState(() => _isEnabled = v),
              title: const Text('Reopen on customer reply'),
              subtitle: Text(
                _isEnabled
                    ? 'A reply inside the window puts the ticket back in the '
                          'queue.'
                    : 'A reply is filed on the closed ticket and nothing else '
                          'happens. Nothing counts those replies either, so '
                          'the missed-window figure reads zero while it is '
                          'off.',
                style: AppTypography.caption.copyWith(
                  color: _isEnabled
                      ? AppColors.textSecondary
                      : AppColors.warning600,
                ),
              ),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _window,
              keyboardType: TextInputType.number,
              inputFormatters: [FilteringTextInputFormatter.digitsOnly],
              decoration: InputDecoration(
                labelText: 'Window, in days',
                helperText:
                    'Calendar days from when the ticket closed, '
                    '$reopenWindowMin to $reopenWindowMax',
                border: const OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              initialValue: _status,
              isExpanded: true,
              decoration: const InputDecoration(
                labelText: 'Comes back as',
                helperText: 'Only a status that counts as open',
                border: OutlineInputBorder(),
              ),
              items: [
                for (final status in reopenToStatuses)
                  DropdownMenuItem(value: status, child: Text(status)),
              ],
              onChanged: (v) => setState(() => _status = v ?? _status),
            ),
            const SizedBox(height: 8),
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              value: _notifyAssigned,
              onChanged: (v) => setState(() => _notifyAssigned = v),
              title: const Text('Tell the assignee'),
              subtitle: Text(
                'The person the ticket was assigned to when it closed.',
                style: AppTypography.caption.copyWith(
                  color: AppColors.textSecondary,
                ),
              ),
            ),
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
                      child: const Text('Save policy'),
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
