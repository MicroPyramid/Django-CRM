import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';

import '../../core/theme/theme.dart';
import '../../data/models/support_ticket.dart';
import '../../providers/support_provider.dart';
import '../../services/attachment_upload.dart';

class SupportCreateScreen extends ConsumerStatefulWidget {
  const SupportCreateScreen({super.key});

  @override
  ConsumerState<SupportCreateScreen> createState() =>
      _SupportCreateScreenState();
}

class _SupportCreateScreenState extends ConsumerState<SupportCreateScreen> {
  final _formKey = GlobalKey<FormState>();
  final _subject = TextEditingController();
  final _body = TextEditingController();
  SupportCategory? _category;
  PlatformFile? _attachment;
  bool _submitting = false;

  @override
  void dispose() {
    _subject.dispose();
    _body.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    backgroundColor: AppColors.surfaceDim,
    appBar: AppBar(
      title: const Text('New support ticket'),
      backgroundColor: AppColors.surface,
      elevation: 0,
    ),
    body: SafeArea(
      child: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            TextFormField(
              controller: _subject,
              maxLength: 200,
              textInputAction: TextInputAction.next,
              decoration: const InputDecoration(
                labelText: 'Subject',
                hintText: 'A short summary of the problem',
              ),
              validator: (value) =>
                  (value ?? '').trim().isEmpty ? 'Add a subject.' : null,
            ),
            const SizedBox(height: 16),
            DropdownButtonFormField<SupportCategory>(
              initialValue: _category,
              decoration: const InputDecoration(labelText: 'Category'),
              items: SupportCategory.values
                  .map(
                    (category) => DropdownMenuItem(
                      value: category,
                      child: Text(category.label),
                    ),
                  )
                  .toList(),
              onChanged: (value) => setState(() => _category = value),
              validator: (value) => value == null ? 'Choose a category.' : null,
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _body,
              minLines: 7,
              maxLines: 12,
              maxLength: 10000,
              decoration: const InputDecoration(
                labelText: 'What do you need help with?',
                alignLabelWithHint: true,
                hintText:
                    'Include what you tried, what you expected, and the exact error you saw.',
              ),
              validator: (value) => (value ?? '').trim().isEmpty
                  ? 'Describe what happened.'
                  : null,
            ),
            const SizedBox(height: 8),
            OutlinedButton.icon(
              onPressed: _submitting ? null : _pickAttachment,
              icon: const Icon(LucideIcons.paperclip),
              label: Text(_attachment?.name ?? 'Attach a file (optional)'),
            ),
            const SizedBox(height: 6),
            Text(
              'Up to 25 MB. Remove secrets and personal data before uploading.',
              style: AppTypography.caption.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
            const SizedBox(height: 24),
            FilledButton(
              onPressed: _submitting ? null : _submit,
              child: Text(_submitting ? 'Opening…' : 'Open ticket'),
            ),
          ],
        ),
      ),
    ),
  );

  Future<void> _pickAttachment() async {
    final result = await selectAttachment();
    if (!mounted || result.cancelled) return;
    if (result.error != null) {
      _snack(result.error!);
      return;
    }
    setState(() => _attachment = result.file);
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _submitting = true);
    final result = await ref
        .read(supportTicketsProvider.notifier)
        .create(
          subject: _subject.text,
          category: _category!,
          body: _body.text,
          attachment: _attachment,
        );
    await clearAttachmentPickerCache();
    if (!mounted) return;
    setState(() => _submitting = false);
    if (!result.success) {
      _snack(result.error ?? 'Could not open this ticket.');
      return;
    }
    Navigator.of(context).pop(true);
  }

  void _snack(String message) => ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(content: Text(message), behavior: SnackBarBehavior.floating),
  );
}
