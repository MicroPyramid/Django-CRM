import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/theme/theme.dart';
import '../../data/models/approval_rule.dart';
import '../../data/models/lookup_models.dart';
import '../../providers/lookup_provider.dart';

/// Write or edit an approval rule.
///
/// Returns the request body, or null if dismissed. Create and edit send the
/// same shape: nothing on this resource is frozen after creation.
Future<Map<String, dynamic>?> showApprovalRuleFormSheet(
  BuildContext context, {
  ApprovalRule? existing,
}) {
  return showModalBottomSheet<Map<String, dynamic>>(
    context: context,
    isScrollControlled: true,
    builder: (context) => _ApprovalRuleFormSheet(existing: existing),
  );
}

class _ApprovalRuleFormSheet extends ConsumerStatefulWidget {
  const _ApprovalRuleFormSheet({this.existing});

  final ApprovalRule? existing;

  @override
  ConsumerState<_ApprovalRuleFormSheet> createState() =>
      _ApprovalRuleFormSheetState();
}

class _ApprovalRuleFormSheetState
    extends ConsumerState<_ApprovalRuleFormSheet> {
  late final TextEditingController _name;
  late String _role;
  late List<String> _approverIds;
  String? _priority;
  String? _caseType;
  String? _teamId;
  String? _error;

  bool get _isCreate => widget.existing == null;

  /// Approvers named on the rule who are not in the picker, which offers active
  /// profiles only. Dropping them would narrow the rule as a side effect of
  /// opening the form, and on a manager rule that leaves it clearable by
  /// nobody. Kept, labelled, and removable on purpose.
  Map<String, String> get _offListNames => {
    for (final person in widget.existing?.approvers ?? const <UserLookup>[])
      if (!person.isActive) person.id: person.displayName,
  };

  @override
  void initState() {
    super.initState();
    final rule = widget.existing;
    _name = TextEditingController(text: rule?.name ?? '');
    _role = rule?.approverRole ?? 'ADMIN';
    _approverIds = [
      for (final person in rule?.approvers ?? const []) person.id,
    ];
    _priority = rule?.matchPriority;
    _caseType = rule?.matchCaseType;
    _teamId = rule?.matchTeam?.id;
  }

  @override
  void dispose() {
    _name.dispose();
    super.dispose();
  }

  void _submit() {
    final problem = approvalRuleNameProblem(_name.text);
    if (problem != null) {
      setState(() => _error = problem);
      return;
    }
    Navigator.of(context).pop(
      approvalRulePayload(
        name: _name.text,
        approverRole: _role,
        approverIds: _approverIds,
        matchPriority: _priority,
        matchCaseType: _caseType,
        matchTeamId: _teamId,
        // Only the create form carries this. On an edit the row's own Turn off
        // and Turn on controls own the state.
        isActive: _isCreate ? true : null,
      ),
    );
  }

  /// Who could clear the rule as the form currently stands, so the answer is
  /// visible before saving rather than on the row afterwards.
  String get _clearedBy {
    final named = [
      for (final person in ref.read(usersProvider))
        if (_approverIds.contains(person.id)) person.displayName,
      for (final entry in _offListNames.entries)
        if (_approverIds.contains(entry.key)) entry.value,
    ];
    if (rolesThatExist.contains(_role)) {
      return named.isEmpty
          ? 'any admin'
          : 'any admin, or ${named.join(' or ')}';
    }
    return named.isEmpty ? 'nobody' : named.join(' or ');
  }

  @override
  Widget build(BuildContext context) {
    final people = ref.watch(usersProvider);
    final teams = ref.watch(teamsProvider);
    final offList = _offListNames;
    final strandsTickets = _clearedBy == 'nobody';

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
              _isCreate ? 'New approval rule' : 'Edit ${widget.existing!.name}',
              style: AppTypography.h3.copyWith(fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _name,
              textCapitalization: TextCapitalization.sentences,
              maxLength: 128,
              decoration: const InputDecoration(
                labelText: 'Rule name',
                border: OutlineInputBorder(),
                counterText: '',
              ),
            ),
            const SizedBox(height: 16),
            const _SectionLabel('What it gates'),
            DropdownButtonFormField<String?>(
              initialValue: _priority,
              isExpanded: true,
              decoration: const InputDecoration(
                labelText: 'Priority',
                border: OutlineInputBorder(),
              ),
              items: [
                const DropdownMenuItem(value: null, child: Text('Any')),
                for (final priority in approvalPriorities)
                  DropdownMenuItem(value: priority, child: Text(priority)),
              ],
              onChanged: (v) => setState(() => _priority = v),
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String?>(
              initialValue: _caseType,
              isExpanded: true,
              decoration: const InputDecoration(
                labelText: 'Ticket type',
                border: OutlineInputBorder(),
              ),
              items: [
                const DropdownMenuItem(value: null, child: Text('Any')),
                for (final type in approvalCaseTypes)
                  DropdownMenuItem(value: type, child: Text(type)),
              ],
              onChanged: (v) => setState(() => _caseType = v),
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String?>(
              initialValue: teams.any((t) => t.id == _teamId) ? _teamId : null,
              isExpanded: true,
              decoration: InputDecoration(
                labelText: 'Team',
                helperText: teams.isEmpty ? 'No teams in this org yet.' : null,
                border: const OutlineInputBorder(),
              ),
              items: [
                const DropdownMenuItem(value: null, child: Text('Any team')),
                for (final team in teams)
                  DropdownMenuItem(value: team.id, child: Text(team.name)),
              ],
              onChanged: (v) => setState(() => _teamId = v),
            ),
            const SizedBox(height: 16),
            const _SectionLabel('Who can clear it'),
            DropdownButtonFormField<String>(
              initialValue: _role,
              isExpanded: true,
              decoration: const InputDecoration(
                labelText: 'Role',
                border: OutlineInputBorder(),
              ),
              items: [
                for (final choice in approverRoleChoices)
                  DropdownMenuItem(
                    value: choice.value,
                    child: Text(choice.label),
                  ),
              ],
              onChanged: (v) => setState(() => _role = v ?? _role),
            ),
            const SizedBox(height: 12),
            Text(
              'Anyone picked here can clear it as well as the role above, not '
              'instead of it.',
              style: AppTypography.caption.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                for (final person in people)
                  FilterChip(
                    label: Text(person.displayName),
                    selected: _approverIds.contains(person.id),
                    onSelected: (on) => setState(() {
                      on
                          ? _approverIds.add(person.id)
                          : _approverIds.remove(person.id);
                    }),
                  ),
                for (final entry in offList.entries)
                  if (_approverIds.contains(entry.key))
                    FilterChip(
                      label: Text('${entry.value} (deactivated)'),
                      selected: true,
                      onSelected: (_) =>
                          setState(() => _approverIds.remove(entry.key)),
                    ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              'Cleared by $_clearedBy',
              style: AppTypography.caption.copyWith(
                color: strandsTickets
                    ? AppColors.danger600
                    : AppColors.textSecondary,
                fontWeight: FontWeight.w600,
              ),
            ),
            if (strandsTickets) ...[
              const SizedBox(height: 6),
              Text(
                'This organization has admins and members. There is no manager '
                'role, so with nobody named here the first ticket this gates '
                'cannot be closed by anyone.',
                style: AppTypography.caption.copyWith(
                  color: AppColors.danger600,
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
                      child: Text(_isCreate ? 'Add rule' : 'Save changes'),
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
