import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../config/api_config.dart';
import '../../core/theme/theme.dart';
import '../../data/models/lead_source.dart';
import '../../data/models/mailbox.dart';
import '../../providers/lead_sources_provider.dart';
import '../../providers/lookup_provider.dart';

/// Add or edit an inbound address.
///
/// Returns the request body, or null if dismissed.
///
/// The webhook secret (Postmark's basic-auth password, Mailgun's signing key)
/// is write-only: the field is never prefilled, the sheet says only whether one
/// is stored, and a blank field sends nothing, so a save cannot blank it.
///
/// The SNS Topic ARN is a field. Only admins reach this sheet, and the server
/// sends the ARN to admins only; it is sent back only when changed
/// ([mailboxTopicArnEdit]).
///
/// [leadsOffered] and [generatedDomain] come from the list
/// ([MailboxesState]): an API without lead addresses gets the ticket form only,
/// and "Generate an address" appears only where the server makes them.
Future<Map<String, dynamic>?> showMailboxFormSheet(
  BuildContext context, {
  Mailbox? existing,
  bool leadsOffered = false,
  String? generatedDomain,
  bool startAsLeads = false,
}) {
  return showModalBottomSheet<Map<String, dynamic>>(
    context: context,
    isScrollControlled: true,
    builder: (context) => _MailboxFormSheet(
      existing: existing,
      leadsOffered: leadsOffered,
      generatedDomain: generatedDomain,
      startAsLeads: startAsLeads,
    ),
  );
}

class _MailboxFormSheet extends ConsumerStatefulWidget {
  const _MailboxFormSheet({
    this.existing,
    this.leadsOffered = false,
    this.generatedDomain,
    this.startAsLeads = false,
  });

  final Mailbox? existing;
  final bool leadsOffered;
  final String? generatedDomain;
  final bool startAsLeads;

  @override
  ConsumerState<_MailboxFormSheet> createState() => _MailboxFormSheetState();
}

class _MailboxFormSheetState extends ConsumerState<_MailboxFormSheet> {
  late final TextEditingController _address;
  late final TextEditingController _topicArn;
  final TextEditingController _secret = TextEditingController();
  late String _provider;
  late String _priority;
  String? _caseType;
  String? _assigneeId;
  String? _error;
  late String _creates;
  late String _leadSource;
  late final TextEditingController _leadSourceDetail;
  bool _generate = false;

  bool get _isCreate => widget.existing == null;
  bool get _leads => widget.leadsOffered && _creates == mailboxCreatesLeads;
  bool get _canGenerate => _isCreate && widget.generatedDomain != null;

  @override
  void initState() {
    super.initState();
    final mailbox = widget.existing;
    _address = TextEditingController(text: mailbox?.address ?? '');
    _topicArn = TextEditingController(text: mailbox?.topicArn ?? '');
    _provider = mailbox?.provider ?? 'ses';
    _priority = mailbox?.defaultPriority ?? 'Normal';
    _caseType = mailbox?.defaultCaseType;
    _assigneeId = mailbox?.defaultAssignee?.id;
    _creates =
        mailbox?.creates ??
        (widget.startAsLeads ? mailboxCreatesLeads : mailboxCreatesTickets);
    _leadSource = mailbox?.leadSource ?? 'email';
    _leadSourceDetail = TextEditingController(
      text: mailbox?.leadSourceDetail ?? '',
    );
  }

  @override
  void dispose() {
    _address.dispose();
    _topicArn.dispose();
    _secret.dispose();
    _leadSourceDetail.dispose();
    super.dispose();
  }

  /// On a create, or when changed; [mailboxPayload] leaves out a null.
  String? _changed(String value, String? loaded) =>
      _isCreate || value != loaded ? value : null;

  /// The server's own address: one to generate, or one it already made.
  bool get _serverAddress =>
      (_canGenerate && _generate) || (widget.existing?.isGenerated ?? false);

  void _submit() {
    final problem = _serverAddress
        ? null
        : mailboxAddressProblem(_address.text);
    if (problem != null) {
      setState(() => _error = problem);
      return;
    }
    final existing = widget.existing;
    Navigator.of(context).pop(
      mailboxPayload(
        address: _serverAddress ? null : _address.text,
        provider: _provider,
        defaultPriority: _priority,
        defaultCaseType: _caseType,
        defaultAssigneeId: _assigneeId,
        // Only the create form carries this. On an edit the row's own Turn off
        // and Turn on controls own the state, and resending it from here would
        // let a form opened before a toggle undo it.
        isActive: _isCreate ? true : null,
        topicArn: mailboxTopicArnEdit(
          _topicArn.text,
          widget.existing?.topicArn,
        ),
        webhookSecret: secretMailboxProviders.contains(_provider)
            ? _secret.text
            : null,
        generateAddress: _canGenerate && _generate,
        creates: widget.leadsOffered
            ? _changed(_creates, existing?.creates)
            : null,
        leadSource: _leads ? _changed(_leadSource, existing?.leadSource) : null,
        leadSourceDetail: _leads
            ? _changed(
                _leadSourceDetail.text.trim(),
                existing?.leadSourceDetail,
              )
            : null,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final people = ref.watch(usersProvider);
    // The stored assignee when the picker cannot offer them, because the
    // profile has been deactivated since it was chosen (or the list has not
    // loaded yet). Dropping them here would move the mailbox back to
    // unassigned as a side effect of editing the address, so they get an entry
    // of their own, labelled deactivated only when they are.
    final stored = widget.existing?.defaultAssignee;
    final offList = stored != null && !people.any((p) => p.id == stored.id)
        ? stored
        : null;
    final made = _leads ? 'leads' : 'tickets';

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
              _isCreate ? 'New address' : 'Edit ${widget.existing!.address}',
              style: AppTypography.h3.copyWith(fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 16),
            if (widget.leadsOffered) ...[
              DropdownButtonFormField<String>(
                key: const ValueKey('mailbox-creates'),
                initialValue: _creates,
                isExpanded: true,
                decoration: const InputDecoration(
                  labelText: 'Mail here creates',
                  border: OutlineInputBorder(),
                ),
                items: const [
                  DropdownMenuItem(
                    value: mailboxCreatesTickets,
                    child: Text('Tickets'),
                  ),
                  DropdownMenuItem(
                    value: mailboxCreatesLeads,
                    child: Text('Leads'),
                  ),
                ],
                onChanged: (v) => setState(() => _creates = v ?? _creates),
              ),
              const SizedBox(height: 12),
            ],
            if (_canGenerate) ...[
              SwitchListTile.adaptive(
                contentPadding: EdgeInsets.zero,
                value: _generate,
                onChanged: (v) => setState(() => _generate = v),
                title: const Text('Generate an address'),
                subtitle: Text(
                  'A new address at ${widget.generatedDomain}, ready to use. '
                  'Nothing to set up with a mail provider.',
                ),
              ),
              const SizedBox(height: 12),
            ],
            if (!_serverAddress) ...[
              TextField(
                controller: _address,
                keyboardType: TextInputType.emailAddress,
                autocorrect: false,
                decoration: InputDecoration(
                  labelText: 'Address',
                  helperText: _isCreate
                      ? null
                      : 'Mail to the old address stops becoming $made.',
                  helperMaxLines: 2,
                  border: const OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                initialValue: _provider,
                isExpanded: true,
                decoration: const InputDecoration(
                  labelText: 'Provider',
                  helperText:
                      'AWS SES, Postmark and Mailgun deliver. Mail to an IMAP '
                      'address becomes nothing until that integration exists.',
                  helperMaxLines: 4,
                  border: OutlineInputBorder(),
                ),
                items: [
                  for (final provider in mailboxProviderLabels.keys)
                    DropdownMenuItem(
                      value: provider,
                      child: Text(mailboxProviderLabel(provider)),
                    ),
                ],
                onChanged: (v) => setState(() => _provider = v ?? _provider),
              ),
              const SizedBox(height: 12),
              if (secretMailboxProviders.contains(_provider))
                ..._secretFields()
              else
                TextField(
                  key: const ValueKey('mailbox-topic-arn'),
                  controller: _topicArn,
                  keyboardType: TextInputType.url,
                  autocorrect: false,
                  enableSuggestions: false,
                  decoration: const InputDecoration(
                    labelText: 'SNS Topic ARN',
                    hintText: 'arn:aws:sns:us-east-1:123456789012:inbound-mail',
                    helperText:
                        'Mail is accepted only from this exact topic. Left blank, '
                        'it is set by the first subscription AWS confirms from an '
                        'AWS account this server allows. Clearing it stops mail '
                        'until it is set again.',
                    helperMaxLines: 5,
                    border: OutlineInputBorder(),
                  ),
                ),
            ],
            const SizedBox(height: 16),
            if (_leads) ...[
              const _SectionLabel('What a lead arrives with'),
              _leadSourceField(),
              const SizedBox(height: 12),
              TextField(
                key: const ValueKey('mailbox-lead-source-detail'),
                controller: _leadSourceDetail,
                maxLength: 100,
                decoration: const InputDecoration(
                  labelText: 'Sub-source (optional)',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 12),
            ] else ...[
              const _SectionLabel('What a ticket opens as'),
              DropdownButtonFormField<String>(
                initialValue: _priority,
                isExpanded: true,
                decoration: const InputDecoration(
                  labelText: 'Priority',
                  border: OutlineInputBorder(),
                ),
                items: [
                  for (final priority in mailboxPriorities)
                    DropdownMenuItem(value: priority, child: Text(priority)),
                ],
                onChanged: (v) => setState(() => _priority = v ?? _priority),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String?>(
                initialValue: _caseType,
                isExpanded: true,
                decoration: const InputDecoration(
                  labelText: 'Type',
                  border: OutlineInputBorder(),
                ),
                items: [
                  const DropdownMenuItem(value: null, child: Text('None')),
                  for (final type in mailboxCaseTypes)
                    DropdownMenuItem(value: type, child: Text(type)),
                ],
                onChanged: (v) => setState(() => _caseType = v),
              ),
              const SizedBox(height: 12),
            ],
            DropdownButtonFormField<String?>(
              initialValue: _assigneeId,
              isExpanded: true,
              decoration: InputDecoration(
                labelText: 'Assigned to',
                helperText: _leads
                    ? 'Owns every lead this address makes.'
                    : 'Where a ticket goes after that is decided by routing, '
                          'not by this.',
                helperMaxLines: 3,
                border: const OutlineInputBorder(),
              ),
              items: [
                DropdownMenuItem(
                  value: null,
                  child: Text(
                    _leads ? 'Unassigned' : 'Unassigned, then routed',
                  ),
                ),
                if (offList != null)
                  DropdownMenuItem(
                    value: offList.id,
                    child: Text(
                      offList.isActive
                          ? offList.displayName
                          : '${offList.displayName} (deactivated)',
                    ),
                  ),
                for (final person in people)
                  DropdownMenuItem(
                    value: person.id,
                    child: Text(person.displayName),
                  ),
              ],
              onChanged: (v) => setState(() => _assigneeId = v),
            ),
            if (offList != null &&
                !offList.isActive &&
                _assigneeId == offList.id) ...[
              const SizedBox(height: 8),
              Text(
                _leads
                    ? 'Deactivated users are not assigned. New leads from this '
                          'address stay unassigned until you choose someone '
                          'else.'
                    : 'Deactivated users are not assigned. New tickets from '
                          'this address go to routing until you choose someone '
                          'else.',
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
                      child: Text(_isCreate ? 'Add address' : 'Save changes'),
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

  /// The write-only credential for Postmark or Mailgun, and the URL to give
  /// the provider. A new address has no id yet, so no URL.
  List<Widget> _secretFields() {
    final existing = widget.existing;
    final stored = existing?.hasWebhookSecret ?? false;
    final postmark = _provider == 'postmark';
    final url = existing == null
        ? null
        : mailboxSetupUrl(_provider, existing.id, ApiConfig.baseUrl);
    return [
      TextField(
        key: const ValueKey('mailbox-webhook-secret'),
        controller: _secret,
        obscureText: true,
        autocorrect: false,
        enableSuggestions: false,
        decoration: InputDecoration(
          labelText: postmark ? 'Basic-auth password' : 'Webhook signing key',
          helperText:
              '${stored ? 'A secret is stored. It is never shown; leave blank to keep it.' : 'No secret is stored, so every post to this address is refused.'} '
              '${postmark ? 'Postmark sends it as the basic-auth password in the webhook URL.' : "This is your Mailgun account's HTTP webhook signing key."}',
          helperMaxLines: 5,
          border: const OutlineInputBorder(),
        ),
      ),
      const SizedBox(height: 8),
      if (url != null)
        SelectableText(
          '${postmark ? 'Inbound webhook URL' : 'Route action'}: $url',
          key: const ValueKey('mailbox-setup-url'),
          style: AppTypography.caption,
        )
      else
        Text(
          'The setup URL appears here once the address is saved.',
          style: AppTypography.caption,
        ),
    ];
  }

  Widget _leadSourceField() {
    final async = ref.watch(leadSourcesProvider);
    final answer = shownLeadSources(async);
    final options = pickableSources(answer?.sources ?? const [], _leadSource);
    return DropdownButtonFormField<String>(
      key: const ValueKey('mailbox-lead-source'),
      initialValue: _leadSource.isEmpty ? null : _leadSource,
      isExpanded: true,
      decoration: InputDecoration(
        labelText: 'Lead source',
        helperText: async.hasError
            ? 'Could not load the sources. Close this and try again.'
            : answer == null
            ? 'Loading the sources.'
            : null,
        border: const OutlineInputBorder(),
      ),
      items: [
        for (final source in options)
          DropdownMenuItem(value: source.key, child: Text(source.pickerLabel)),
      ],
      onChanged: (v) => setState(() => _leadSource = v ?? _leadSource),
    );
  }
}

class _SectionLabel extends StatelessWidget {
  const _SectionLabel(this.text);

  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Text(
        text.toUpperCase(),
        style: AppTypography.overline.copyWith(
          color: AppColors.textSecondary,
          letterSpacing: 1.2,
        ),
      ),
    );
  }
}
