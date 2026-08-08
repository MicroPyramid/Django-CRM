import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';

import '../../core/theme/theme.dart';
import '../../data/models/routing_rule.dart';
import '../../providers/lookup_provider.dart';

/// Write or edit a routing rule.
///
/// Returns the request body, or `null` if dismissed. Create and edit send the
/// same shape (nothing on this resource is frozen after creation) but not the
/// same rules: see [routingWriteProblem] for the one asymmetry, which exists
/// because the backend's own guard is create-only.
Future<Map<String, dynamic>?> showRoutingRuleFormSheet(
  BuildContext context, {
  RoutingRule? existing,
}) {
  return showModalBottomSheet<Map<String, dynamic>>(
    context: context,
    isScrollControlled: true,
    builder: (context) => _RoutingRuleFormSheet(existing: existing),
  );
}

class _RoutingRuleFormSheet extends ConsumerStatefulWidget {
  const _RoutingRuleFormSheet({this.existing});

  final RoutingRule? existing;

  @override
  ConsumerState<_RoutingRuleFormSheet> createState() =>
      _RoutingRuleFormSheetState();
}

class _RoutingRuleFormSheetState extends ConsumerState<_RoutingRuleFormSheet> {
  late final TextEditingController _name;
  late final TextEditingController _priority;
  late String _strategy;
  late bool _stopProcessing;
  late List<RoutingConditionDraft> _conditions;
  late List<String> _assigneeIds;
  String? _teamId;
  String? _error;

  bool get _isCreate => widget.existing == null;

  /// People chosen who are not in the picker's list, which offers active
  /// profiles only. A deactivated assignee stays on the rule server-side, so
  /// dropping them from the selection here would delete part of the rule as a
  /// side effect of opening the form. Kept, labelled, and removable on purpose.
  Map<String, String> get _offListNames => {
    for (final p in widget.existing?.targetAssignees ?? const <RoutingTarget>[])
      if (!p.isActive) p.id: p.name,
  };

  @override
  void initState() {
    super.initState();
    final rule = widget.existing;
    _name = TextEditingController(text: rule?.name ?? '');
    _priority = TextEditingController(text: '${rule?.priorityOrder ?? 100}');
    _strategy = rule?.strategy ?? RoutingRule.strategyDirect;
    // On by default for a new rule, matching the model. It is the setting that
    // turns an empty pool from "falls through" into "swallows the ticket", so
    // the form says what it does rather than hiding it.
    _stopProcessing = rule?.stopProcessing ?? true;
    _conditions = [
      for (final c in rule?.conditions ?? const <RoutingCondition>[])
        RoutingConditionDraft.from(c),
    ];
    _assigneeIds = [for (final p in rule?.targetAssignees ?? const []) p.id];
    _teamId = rule?.targetTeam?.id;
  }

  @override
  void dispose() {
    _name.dispose();
    _priority.dispose();
    super.dispose();
  }

  void _submit() {
    final problem = routingWriteProblem(
      isCreate: _isCreate,
      name: _name.text,
      strategy: _strategy,
      assigneeIds: _assigneeIds,
      teamId: _teamId,
      conditions: _conditions,
    );
    if (problem != null) {
      setState(() => _error = problem);
      return;
    }
    Navigator.of(context).pop(
      routingRulePayload(
        name: _name.text,
        priorityOrder: int.tryParse(_priority.text.trim()) ?? 0,
        strategy: _strategy,
        stopProcessing: _stopProcessing,
        conditions: _conditions,
        assigneeIds: _assigneeIds,
        teamId: _teamId,
        // Only the create form carries this. On an edit the row's own Turn off
        // and Turn on controls own the state, and resending it from here would
        // let a form opened before a toggle undo it.
        isActive: _isCreate ? true : null,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final people = ref.watch(usersProvider);
    final teams = ref.watch(teamsProvider);
    final offList = _offListNames;

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
              _isCreate ? 'New routing rule' : 'Edit ${widget.existing!.name}',
              style: AppTypography.h3.copyWith(fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _name,
              textCapitalization: TextCapitalization.sentences,
              maxLength: 255,
              decoration: const InputDecoration(
                labelText: 'Rule name',
                border: OutlineInputBorder(),
                counterText: '',
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _priority,
              keyboardType: TextInputType.number,
              inputFormatters: [FilteringTextInputFormatter.digitsOnly],
              decoration: const InputDecoration(
                labelText: 'Order',
                helperText: 'Lower runs first',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 16),
            const _SectionLabel('When a ticket matches'),
            for (final (index, row) in _conditions.indexed)
              _ConditionRow(
                key: ValueKey(index),
                draft: row,
                onChanged: () => setState(() {}),
                onRemove: () => setState(() => _conditions.removeAt(index)),
              ),
            if (_conditions.isEmpty)
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Text(
                  'With no conditions this rule matches every new ticket.',
                  style: AppTypography.caption.copyWith(
                    color: AppColors.warning600,
                  ),
                ),
              ),
            Align(
              alignment: Alignment.centerLeft,
              child: TextButton.icon(
                onPressed: () =>
                    setState(() => _conditions.add(RoutingConditionDraft())),
                icon: const Icon(LucideIcons.plus, size: 16),
                label: const Text('Add a condition'),
              ),
            ),
            if (_conditions.length > 1)
              Text(
                'All of these have to be true.',
                style: AppTypography.caption.copyWith(
                  color: AppColors.textSecondary,
                ),
              ),
            const SizedBox(height: 16),
            const _SectionLabel('Assign it'),
            DropdownButtonFormField<String>(
              initialValue: _strategy,
              isExpanded: true,
              decoration: const InputDecoration(
                labelText: 'How',
                border: OutlineInputBorder(),
              ),
              items: [
                for (final entry in routingStrategyLabels.entries)
                  DropdownMenuItem(value: entry.key, child: Text(entry.value)),
              ],
              onChanged: (v) => setState(() => _strategy = v ?? _strategy),
            ),
            const SizedBox(height: 12),
            if (_strategy == RoutingRule.strategyByTeam)
              DropdownButtonFormField<String>(
                initialValue: teams.any((t) => t.id == _teamId)
                    ? _teamId
                    : null,
                isExpanded: true,
                decoration: const InputDecoration(
                  labelText: 'Team',
                  border: OutlineInputBorder(),
                ),
                items: [
                  for (final team in teams)
                    DropdownMenuItem(value: team.id, child: Text(team.name)),
                ],
                onChanged: (v) => setState(() => _teamId = v),
              )
            else ...[
              Text(
                _strategy == RoutingRule.strategyDirect
                    ? 'Everyone picked here is assigned.'
                    : 'Picked one at a time, in turn.',
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
                      selected: _assigneeIds.contains(person.id),
                      onSelected: (on) => setState(() {
                        on
                            ? _assigneeIds.add(person.id)
                            : _assigneeIds.remove(person.id);
                      }),
                    ),
                  for (final entry in offList.entries)
                    if (_assigneeIds.contains(entry.key))
                      FilterChip(
                        label: Text('${entry.value} (deactivated)'),
                        selected: true,
                        onSelected: (_) =>
                            setState(() => _assigneeIds.remove(entry.key)),
                      ),
                ],
              ),
              if (people.isEmpty && offList.isEmpty)
                Text(
                  'Nobody to pick yet. Invite someone from Team first.',
                  style: AppTypography.caption.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
            ],
            const SizedBox(height: 8),
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              value: _stopProcessing,
              onChanged: (v) => setState(() => _stopProcessing = v),
              title: const Text('Stop after this rule'),
              subtitle: Text(
                _stopProcessing
                    ? 'No rule below this one gets a turn, even if this one '
                          'assigns nobody.'
                    : 'A ticket this rule cannot assign falls through to the '
                          'rules below.',
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

/// One condition, as three controls that stack rather than sit in a row: a
/// field select, an operator select and a value at 390px do not fit on one
/// line, and the value is the one that needs the width.
class _ConditionRow extends StatelessWidget {
  const _ConditionRow({
    super.key,
    required this.draft,
    required this.onChanged,
    required this.onRemove,
  });

  final RoutingConditionDraft draft;
  final VoidCallback onChanged;
  final VoidCallback onRemove;

  @override
  Widget build(BuildContext context) {
    // A stored field the label map does not carry (a custom field, or one
    // added to the backend since) gets its own entry, so opening the form
    // cannot rewrite a condition nobody touched. A select with no matching
    // option is how the web lost condition rows before it read them by index.
    final options = <String, String>{
      ...routingConditionFields,
      if (draft.field.isNotEmpty &&
          !routingConditionFields.containsKey(draft.field))
        draft.field: routingConditionFieldLabel(draft.field),
    };
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.gray50,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: AppColors.gray200),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: DropdownButtonFormField<String>(
                  initialValue: draft.field.isEmpty ? null : draft.field,
                  isExpanded: true,
                  isDense: true,
                  decoration: const InputDecoration(
                    labelText: 'Field',
                    border: OutlineInputBorder(),
                  ),
                  items: [
                    for (final entry in options.entries)
                      DropdownMenuItem(
                        value: entry.key,
                        child: Text(entry.value),
                      ),
                  ],
                  onChanged: (v) {
                    draft.field = v ?? draft.field;
                    onChanged();
                  },
                ),
              ),
              IconButton(
                icon: const Icon(LucideIcons.x, size: 18),
                tooltip: 'Remove this condition',
                onPressed: onRemove,
              ),
            ],
          ),
          const SizedBox(height: 8),
          DropdownButtonFormField<String>(
            initialValue: draft.op,
            isExpanded: true,
            isDense: true,
            decoration: const InputDecoration(
              labelText: 'Test',
              border: OutlineInputBorder(),
            ),
            items: [
              for (final entry in routingConditionOps.entries)
                DropdownMenuItem(value: entry.key, child: Text(entry.value)),
            ],
            onChanged: (v) {
              draft.op = v ?? draft.op;
              onChanged();
            },
          ),
          const SizedBox(height: 8),
          TextFormField(
            initialValue: draft.value,
            decoration: InputDecoration(
              labelText: 'Value',
              helperText: draft.op == 'in' ? 'Separate with commas' : null,
              border: const OutlineInputBorder(),
            ),
            onChanged: (v) => draft.value = v,
          ),
        ],
      ),
    );
  }
}
