import 'package:flutter/material.dart';

import '../../core/theme/theme.dart';
import '../../data/models/access_token.dart';

/// What the create form collected. The payload itself is built in the provider
/// from `tokenCreatePayload`, so the sheet never decides the wire format.
typedef TokenDraft = ({String name, String expiryChoice, String accessChoice});

/// Create a personal access token.
///
/// Returns the draft, or null if dismissed. **Self-scoped underneath**: the
/// server sets the owner from the caller's own profile, so there is no owner
/// field here and no way to mint a token for someone else.
Future<TokenDraft?> showApiTokenFormSheet(BuildContext context) {
  return showModalBottomSheet<TokenDraft>(
    context: context,
    isScrollControlled: true,
    builder: (context) => const _ApiTokenFormSheet(),
  );
}

class _ApiTokenFormSheet extends StatefulWidget {
  const _ApiTokenFormSheet();

  @override
  State<_ApiTokenFormSheet> createState() => _ApiTokenFormSheetState();
}

class _ApiTokenFormSheetState extends State<_ApiTokenFormSheet> {
  final TextEditingController _name = TextEditingController();

  /// 90 days, the first entry, so the default is an expiry rather than never.
  String _expiry = expiryChoices.first.value;
  String _access = accessChoices.first.value;
  String? _error;

  @override
  void dispose() {
    _name.dispose();
    super.dispose();
  }

  void _submit() {
    final problem = tokenNameProblem(_name.text);
    if (problem != null) {
      setState(() => _error = problem);
      return;
    }
    Navigator.of(context).pop((
      name: _name.text.trim(),
      expiryChoice: _expiry,
      accessChoice: _access,
    ));
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
              'New token',
              style: AppTypography.h3.copyWith(fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 4),
            Text(
              'The token is created for you and authenticates as you. The '
              'value is shown once, on the next screen.',
              style: AppTypography.caption.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
            const SizedBox(height: 14),
            TextField(
              controller: _name,
              autofocus: true,
              maxLength: 255,
              textCapitalization: TextCapitalization.sentences,
              decoration: const InputDecoration(
                labelText: 'What is this token for?',
                hintText: 'e.g. Nightly export job',
                helperText: 'Names what breaks if you revoke it later',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 4),
            DropdownButtonFormField<String>(
              initialValue: _access,
              isExpanded: true,
              decoration: const InputDecoration(
                labelText: 'Access',
                helperText: 'Finer scopes are available through the API',
                border: OutlineInputBorder(),
              ),
              items: [
                for (final choice in accessChoices)
                  DropdownMenuItem(
                    value: choice.value,
                    child: Text(choice.label),
                  ),
              ],
              onChanged: (v) => setState(() => _access = v ?? _access),
            ),
            const SizedBox(height: 14),
            DropdownButtonFormField<String>(
              initialValue: _expiry,
              isExpanded: true,
              decoration: const InputDecoration(
                labelText: 'Expires',
                border: OutlineInputBorder(),
              ),
              items: [
                for (final choice in expiryChoices)
                  DropdownMenuItem(
                    value: choice.value,
                    child: Text(choice.label),
                  ),
              ],
              onChanged: (v) => setState(() => _expiry = v ?? _expiry),
            ),
            if (_expiry == 'never') ...[
              const SizedBox(height: 8),
              Text(
                'A token that never expires has to be revoked by hand to ever '
                'stop working.',
                style: AppTypography.caption.copyWith(
                  color: AppColors.warning600,
                ),
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
                      child: const Text('Create token'),
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
