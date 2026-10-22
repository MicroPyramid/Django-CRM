import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';

import '../../../core/theme/theme.dart';
import '../../../data/models/automation.dart';
import '../../../providers/auth_provider.dart';
import '../../../providers/automation_provider.dart';
import '../../../routes/app_router.dart';
import '../../../services/automation_text.dart';
import '../../../widgets/forms/unsaved_changes.dart';
import '../../../widgets/objects/link_field_picker.dart';
import 'action_sheet.dart';
import 'condition_sheet.dart';
import 'status_pill.dart';
import 'trigger_sheet.dart';
import 'try_rule_sheet.dart';

/// Creates a rule ([ruleId] null) or edits one, read top to bottom as When,
/// Only if, Then. The draft lives here; each sheet edits one row and returns
/// it, and nothing reaches the server until Save.
class AutomationRuleScreen extends ConsumerStatefulWidget {
  const AutomationRuleScreen({super.key, this.ruleId});

  final String? ruleId;

  @override
  ConsumerState<AutomationRuleScreen> createState() =>
      _AutomationRuleScreenState();
}

class _AutomationRuleScreenState extends ConsumerState<AutomationRuleScreen> {
  final _name = TextEditingController();
  final _firstError = GlobalKey();
  bool _firstErrorPlaced = false;

  AutomationRule? _saved;
  RuleDraft? _draft;
  RuleDraft? _baseline;
  RuleErrors _errors = RuleErrors();
  bool _saving = false;
  bool _busy = false;

  bool get _isNew => widget.ruleId == null;

  @override
  void dispose() {
    _name.dispose();
    super.dispose();
  }

  /// What a save would send differs from what is saved. [ruleBody] drops what
  /// the server ignores, so a stale key alone never counts as a change.
  bool get _dirty {
    final d = _draft;
    final b = _baseline;
    if (d == null || b == null) return false;
    return jsonEncode(ruleBody(d, create: true)) !=
        jsonEncode(ruleBody(b, create: true));
  }

  void _seed(AutomationRule rule) {
    _saved = rule;
    _draft = RuleDraft.from(rule);
    _baseline = RuleDraft.from(rule);
    if (_name.text != rule.name) _name.text = rule.name;
  }

  @override
  Widget build(BuildContext context) {
    if (!ref.watch(isOrgAdminProvider)) {
      return _shell(const _MemberNotice());
    }
    final id = widget.ruleId;
    final loaded = ref.watch(automationCatalogueProvider);
    final catalogue = loaded.isLoading || loaded.hasError ? null : loaded.value;
    final ruleAsync = id == null ? null : ref.watch(automationRuleProvider(id));
    final rows = id == null
        ? null
        : shownAutomationRules(ref.watch(automationRulesProvider));
    AutomationRuleRow? row;
    for (final r in rows?.rules ?? const <AutomationRuleRow>[]) {
      if (r.id == id) row = r;
    }

    if (catalogue == null) {
      return loaded.hasError && !loaded.isLoading
          ? _shell(_ErrorState(message: _loadFailed, onRetry: _retry))
          : _shell(const Center(child: CircularProgressIndicator()));
    }
    if (_draft == null) {
      if (ruleAsync == null) {
        if (catalogue.objects.isEmpty) {
          return _shell(_ErrorState(message: _loadFailed, onRetry: _retry));
        }
        _draft = RuleDraft.blank(catalogue.objects.first.key);
        _baseline = _draft!.copy();
      } else {
        if (ruleAsync.hasError && !ruleAsync.isLoading) {
          return _shell(_ErrorState(message: _loadFailed, onRetry: _retry));
        }
        final rule = ruleAsync.isLoading ? null : ruleAsync.value;
        if (rule == null) {
          return _shell(const Center(child: CircularProgressIndicator()));
        }
        _seed(rule);
      }
    }
    return _form(
      catalogue,
      _isNew ? 'new' : ruleStatus(ruleAsync?.value ?? _saved, row),
      row,
    );
  }

  void _retry() {
    ref.invalidate(automationCatalogueProvider);
    final id = widget.ruleId;
    if (id != null) ref.invalidate(automationRuleProvider(id));
  }

  String get _loadFailed =>
      _isNew ? 'Could not load the rule editor.' : 'Could not load the rule';

  String get _title {
    if (_isNew) return 'New rule';
    final name = _saved?.name ?? '';
    return name.isEmpty ? 'Rule' : name;
  }

  Widget _shell(Widget body) => Scaffold(
    backgroundColor: AppColors.surfaceDim,
    appBar: AppBar(
      title: Text(_isNew ? 'New rule' : 'Rule'),
      backgroundColor: AppColors.surface,
      elevation: 0,
      scrolledUnderElevation: 1,
    ),
    body: body,
  );

  AutomationObject _objectOf(AutomationCatalogue c, String key) =>
      objectOf(c, key) ??
      AutomationObject(key: key, label: key, labelPlural: key);

  void _switchObject(AutomationCatalogue c, String key) {
    final d = _draft!;
    if (key == d.objectKey) return;
    final next = objectOf(c, key);
    final offered = {for (final r in recipientsFor(next)) r.value};
    final offeredTypes = actionTypes(c, next);
    final hasParent = taskParentLabel(next) != null;
    setState(() {
      d.objectKey = key;
      d.trigger = TriggerDraft(event: d.trigger.event);
      d.conditions = [];
      d.actions = [
        for (final a in d.actions)
          if (!offeredTypes.contains(a.type))
            ...const <ActionDraft>[]
          else if (a.type == 'set_field')
            blankAction('set_field')
          else if (a.type == 'create_task' &&
              a.values['assign_to'] == 'parent' &&
              !hasParent)
            (a.copy()..values['assign_to'] = 'record')
          else if (a.type == 'notify' && a.values['to'] is List)
            (a.copy()
              ..values['to'] = [
                for (final v in a.values['to'] as List)
                  if (offered.contains(v)) v,
              ])
          else
            a,
      ];
      _errors = RuleErrors(general: _errors.general);
    });
  }

  Future<void> _editTrigger(AutomationCatalogue c, AutomationObject o) async {
    final next = await showTriggerSheet(
      context,
      catalogue: c,
      object: o,
      draft: _draft!.trigger,
    );
    if (next == null || !mounted) return;
    setState(() {
      _draft!.trigger = next;
      _errors.rows.remove('trigger');
    });
  }

  Future<void> _editCondition(
    AutomationCatalogue c,
    AutomationObject o, [
    int? index,
  ]) async {
    final d = _draft!;
    final next = await showConditionSheet(
      context,
      catalogue: c,
      object: o,
      event: d.trigger.event,
      draft: index == null ? null : d.conditions[index],
    );
    if (next == null || !mounted) return;
    setState(() {
      if (index == null) {
        d.conditions.add(next);
      } else {
        d.conditions[index] = next;
        _errors.rows.remove('conditions.$index');
      }
      _errors.rows.remove('conditions');
    });
  }

  void _removeCondition(int index) => setState(() {
    _draft!.conditions.removeAt(index);
    // The rows after it move up a place, so their marks no longer fit.
    _errors.rows.removeWhere((k, _) => k.startsWith('conditions'));
  });

  Future<void> _save({required bool switchOn}) async {
    final d = _draft;
    if (d == null || _saving) return;
    setState(() => _saving = true);
    final api = ref.read(automationApiProvider);
    final body = ruleBody(d, create: _isNew, switchOn: switchOn);
    final id = widget.ruleId;
    final result = id == null
        ? await api.create(body)
        : await api.update(id, body);
    if (!mounted) return;
    final saved = result.rule;
    if (saved == null) {
      setState(() {
        _saving = false;
        _errors =
            result.errors ?? RuleErrors(general: 'Could not save the rule.');
      });
      WidgetsBinding.instance.addPostFrameCallback((_) {
        final at = _firstError.currentContext;
        if (at != null && at.mounted) {
          Scrollable.ensureVisible(
            at,
            alignment: 0.3,
            duration: const Duration(milliseconds: 200),
          );
        }
      });
      return;
    }
    ref.invalidate(automationRulesProvider);
    ref.invalidate(automationRuleProvider(saved.id));
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(const SnackBar(content: Text('Saved.')));
    if (id == null) {
      context.replace(AppRoutes.settingsAutomationRule(saved.id));
      return;
    }
    setState(() {
      _saving = false;
      _errors = RuleErrors();
      _seed(saved);
    });
  }

  /// The second button: switching on a rule that is off or new, or taking
  /// over a paused one. A rule that is already on has nothing to switch.
  static String? _switchLabel(String? status) => switch (status) {
    'new' || 'off' => 'Save and switch on',
    'paused' => 'Save and take over',
    _ => null,
  };

  Widget _errorLine(String? message) {
    if (message == null || message.isEmpty) return const SizedBox.shrink();
    final key = _firstErrorPlaced ? null : _firstError;
    _firstErrorPlaced = true;
    return Padding(
      key: key,
      padding: const EdgeInsets.only(top: 6, left: 2),
      child: Text(
        message,
        style: AppTypography.caption.copyWith(color: AppColors.danger600),
      ),
    );
  }

  Widget _form(
    AutomationCatalogue catalogue,
    String? status,
    AutomationRuleRow? row,
  ) {
    _firstErrorPlaced = false;
    final d = _draft!;
    final object = _objectOf(catalogue, d.objectKey);
    final switchLabel = _switchLabel(status);
    return UnsavedChangesGuard(
      hasUnsavedChanges: () => _dirty,
      isSaving: _saving || _busy,
      child: Scaffold(
        backgroundColor: AppColors.surfaceDim,
        appBar: AppBar(
          title: Text(_title, maxLines: 1, overflow: TextOverflow.ellipsis),
          backgroundColor: AppColors.surface,
          elevation: 0,
          scrolledUnderElevation: 1,
          leading: IconButton(
            icon: const Icon(LucideIcons.chevronLeft),
            tooltip: 'Back',
            onPressed: _saving || _busy
                ? null
                : () => leaveForm(context, hasUnsavedChanges: _dirty),
          ),
        ),
        body: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 72),
          // A successful save reseeds the draft from the answer, so an edit
          // made while the request is out would be lost without a word.
          child: AbsorbPointer(
            absorbing: _saving || _busy,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                if (!_isNew) ...[_statusStrip(row), const SizedBox(height: 12)],
                TextField(
                  controller: _name,
                  readOnly: _saving,
                  maxLength: 120,
                  textCapitalization: TextCapitalization.sentences,
                  decoration: const InputDecoration(
                    labelText: 'Name',
                    border: OutlineInputBorder(),
                    filled: true,
                    fillColor: AppColors.surface,
                  ),
                  onChanged: (v) {
                    // Rebuilds so Try reflects whether the draft still matches.
                    setState(() {
                      d.name = v;
                      _errors.rows.remove('name');
                    });
                  },
                ),
                _errorLine(_errors.rows['name']),
                const SizedBox(height: 12),
                _whenCard(catalogue, object),
                _errorLine(_errors.rows['trigger']),
                const SizedBox(height: 12),
                _onlyIfCard(catalogue, object),
                _errorLine(_errors.rows['match']),
                _errorLine(_errors.rows['conditions']),
                const SizedBox(height: 12),
                _thenCard(catalogue, object),
                _errorLine(_errors.rows['actions']),
                const SizedBox(height: 12),
                _tryCard(object),
                const SizedBox(height: 20),
                if (_errors.general != null) ...[
                  _GeneralError(
                    key: _firstErrorPlaced ? null : _firstError,
                    message: _errors.general!,
                  ),
                  const SizedBox(height: 12),
                ],
                SizedBox(
                  height: 48,
                  child: switchLabel == null
                      ? FilledButton(
                          onPressed: _saving
                              ? null
                              : () => _save(switchOn: false),
                          child: const Text('Save'),
                        )
                      : OutlinedButton(
                          onPressed: _saving
                              ? null
                              : () => _save(switchOn: false),
                          child: const Text('Save'),
                        ),
                ),
                if (switchLabel != null) ...[
                  const SizedBox(height: 8),
                  SizedBox(
                    height: 48,
                    child: FilledButton(
                      onPressed: _saving ? null : () => _save(switchOn: true),
                      child: Text(switchLabel),
                    ),
                  ),
                ],
                if (!_isNew) ...[
                  const SizedBox(height: 20),
                  SizedBox(
                    height: 48,
                    child: TextButton(
                      style: TextButton.styleFrom(
                        foregroundColor: AppColors.danger600,
                      ),
                      onPressed: _saving || _busy ? null : _delete,
                      child: const Text('Delete rule'),
                    ),
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _statusStrip(AutomationRuleRow? row) {
    final id = widget.ruleId!;
    final saved = ref.watch(automationRuleProvider(id)).value ?? _saved;
    final shown =
        row ??
        AutomationRuleRow(
          id: id,
          trigger: TriggerDraft(),
          status: ruleStatus(saved, null) ?? 'off',
        );
    final text = statusText(shown);
    final owner = saved?.owner;
    final ownerName = owner?.name.trim() ?? '';
    return _Section(
      label: 'STATUS',
      children: [
        Align(
          alignment: Alignment.centerLeft,
          child: AutomationStatusPill(status: shown.status),
        ),
        if (text != null) ...[
          const SizedBox(height: 6),
          Text(text, style: AppTypography.body),
        ],
        if (owner != null) ...[
          const SizedBox(height: 6),
          Text(
            ownerName.isEmpty ? 'Switched on' : 'Switched on by $ownerName',
            style: AppTypography.caption.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
        ],
        const SizedBox(height: 10),
        SizedBox(
          height: 48,
          child: OutlinedButton(
            onPressed: _saving || _busy
                ? null
                : () => context.push(AppRoutes.settingsAutomationRuns(id)),
            child: const Text('Run history'),
          ),
        ),
        if (saved?.isActive == true) ...[
          const SizedBox(height: 8),
          SizedBox(
            height: 48,
            child: OutlinedButton(
              onPressed: _saving || _busy ? null : _switchOff,
              child: const Text('Switch off'),
            ),
          ),
        ],
      ],
    );
  }

  Widget _tryCard(AutomationObject object) {
    final String? hint = _isNew
        ? 'Save the rule to try it on a record.'
        : _dirty
        ? 'Save first: Try uses the saved rule.'
        : null;
    return _Section(
      label: 'TRY IT',
      children: [
        SizedBox(
          height: 48,
          child: OutlinedButton(
            onPressed: hint != null || _saving || _busy ? null : _try,
            child: const Text('Try it on a record'),
          ),
        ),
        if (hint != null) ...[
          const SizedBox(height: 6),
          Text(
            hint,
            style: AppTypography.caption.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
        ],
      ],
    );
  }

  void _toast(String message) => ScaffoldMessenger.of(
    context,
  ).showSnackBar(SnackBar(content: Text(message)));

  void _refresh(String id) {
    ref.invalidate(automationRulesProvider);
    ref.invalidate(automationRuleProvider(id));
  }

  Future<void> _try() async {
    final id = widget.ruleId;
    final saved = _saved;
    if (id == null || saved == null || _busy) return;
    final picked = await showLinkSearchSheet(
      context,
      title: 'Try it on a record',
      target: saved.objectKey,
    );
    if (picked == null || !mounted) return;
    setState(() => _busy = true);
    final result = await ref.read(automationApiProvider).tryRule(id, picked.id);
    if (!mounted) return;
    setState(() => _busy = false);
    await showTryResults(
      context,
      recordName: picked.name.isEmpty ? picked.id : picked.name,
      steps: result.steps,
      error: result.error,
    );
  }

  Future<void> _switchOff() async {
    final id = widget.ruleId;
    if (id == null || _busy) return;
    setState(() => _busy = true);
    final error = await ref.read(automationApiProvider).switchOff(id);
    if (!mounted) return;
    setState(() => _busy = false);
    if (error != null) {
      _toast(error);
      return;
    }
    _refresh(id);
    _toast('Switched off.');
  }

  Future<void> _delete() async {
    final id = widget.ruleId;
    if (id == null || _busy) return;
    final sure = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Delete this rule?'),
        content: const Text('Its run history goes too.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Keep it'),
          ),
          TextButton(
            style: TextButton.styleFrom(foregroundColor: AppColors.danger600),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Delete permanently'),
          ),
        ],
      ),
    );
    if (sure != true || !mounted) return;
    setState(() => _busy = true);
    final error = await ref.read(automationApiProvider).delete(id);
    if (!mounted) return;
    setState(() => _busy = false);
    if (error != null) {
      _toast(error);
      return;
    }
    // Only the list: the rule's own provider is still watched here and would
    // refetch a 404.
    ref.invalidate(automationRulesProvider);
    // A direct pop, so the unsaved-changes guard does not ask about a rule
    // that no longer exists.
    context.pop();
  }

  Widget _whenCard(AutomationCatalogue catalogue, AutomationObject object) {
    final d = _draft!;
    final t = d.trigger;
    final field = t.field;
    final String text;
    if (t.event == 'created') {
      text = '${object.label} created';
    } else if (field == null || field.isEmpty) {
      text = '${object.label} updated';
    } else {
      final sentence = triggerSentence(
        AutomationRule(id: '', objectKey: d.objectKey, trigger: t),
        catalogue,
      );
      text = '${object.label} updated: $sentence';
    }
    return _Section(
      label: 'WHEN',
      children: [
        if (_isNew) ...[
          DropdownButtonFormField<String>(
            initialValue: d.objectKey,
            isExpanded: true,
            decoration: const InputDecoration(
              labelText: 'Object',
              border: OutlineInputBorder(),
            ),
            items: [
              for (final o in catalogue.objects)
                DropdownMenuItem(
                  value: o.key,
                  child: Text(o.label, overflow: TextOverflow.ellipsis),
                ),
            ],
            onChanged: (v) {
              if (v != null) _switchObject(catalogue, v);
            },
          ),
          const SizedBox(height: 8),
        ],
        _Row(
          onTap: () => _editTrigger(catalogue, object),
          child: Row(
            children: [
              Expanded(child: Text(text, style: AppTypography.body)),
              const SizedBox(width: 8),
              Text(
                'Edit',
                style: AppTypography.label.copyWith(
                  color: AppColors.primary600,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _onlyIfCard(AutomationCatalogue catalogue, AutomationObject object) {
    final d = _draft!;
    final atLimit = d.conditions.length >= catalogue.maxConditions;
    return _Section(
      label: 'ONLY IF',
      children: [
        SegmentedButton<String>(
          showSelectedIcon: false,
          segments: const [
            ButtonSegment(value: 'all', label: Text('All of these')),
            ButtonSegment(value: 'any', label: Text('Any of these')),
          ],
          selected: {d.match},
          onSelectionChanged: (s) => setState(() {
            d.match = s.first;
            _errors.rows.remove('match');
          }),
        ),
        for (var i = 0; i < d.conditions.length; i++) ...[
          const SizedBox(height: 8),
          _Row(
            bordered: true,
            onTap: () => _editCondition(catalogue, object, i),
            child: Row(
              children: [
                Expanded(
                  child: Text(
                    conditionSentence(d.conditions[i], object, catalogue),
                    style: AppTypography.body,
                  ),
                ),
                IconButton(
                  tooltip: 'Remove condition ${i + 1}',
                  icon: const Icon(LucideIcons.x, size: 18),
                  constraints: const BoxConstraints(
                    minWidth: 44,
                    minHeight: 44,
                  ),
                  padding: EdgeInsets.zero,
                  onPressed: () => _removeCondition(i),
                ),
              ],
            ),
          ),
          _errorLine(_errors.rows['conditions.$i']),
        ],
        const SizedBox(height: 4),
        Align(
          alignment: Alignment.centerLeft,
          child: TextButton.icon(
            style: TextButton.styleFrom(minimumSize: const Size(44, 44)),
            onPressed: atLimit ? null : () => _editCondition(catalogue, object),
            icon: const Icon(LucideIcons.plus, size: 16),
            label: const Text('Add condition'),
          ),
        ),
        if (atLimit)
          Text(
            'A rule can have at most ${catalogue.maxConditions} conditions.',
            style: AppTypography.caption.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
      ],
    );
  }

  Widget _thenCard(AutomationCatalogue catalogue, AutomationObject object) {
    final d = _draft!;
    final atLimit = d.actions.length >= catalogue.maxActions;
    final canAdd = actionTypes(catalogue, object).isNotEmpty;
    return _Section(
      label: 'THEN',
      children: [
        for (var i = 0; i < d.actions.length; i++) ...[
          if (i > 0) const SizedBox(height: 8),
          _Row(
            bordered: true,
            onTap: () => _editAction(catalogue, object, i),
            child: Row(
              children: [
                Expanded(
                  child: Text(
                    '${i + 1}. ${actionSentence(d.actions[i], object, catalogue)}',
                    style: AppTypography.body,
                  ),
                ),
                _iconButton(
                  'Move action ${i + 1} up',
                  LucideIcons.arrowUp,
                  i == 0 ? null : () => _moveAction(i, -1),
                ),
                _iconButton(
                  'Move action ${i + 1} down',
                  LucideIcons.arrowDown,
                  i == d.actions.length - 1 ? null : () => _moveAction(i, 1),
                ),
                _iconButton(
                  'Remove action ${i + 1}',
                  LucideIcons.x,
                  () => _removeAction(i),
                ),
              ],
            ),
          ),
          _errorLine(_errors.rows['actions.$i']),
        ],
        if (d.actions.isEmpty)
          Text(
            'Add at least one action.',
            style: AppTypography.caption.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
        const SizedBox(height: 4),
        Align(
          alignment: Alignment.centerLeft,
          child: TextButton.icon(
            style: TextButton.styleFrom(minimumSize: const Size(44, 44)),
            onPressed: atLimit || !canAdd
                ? null
                : () => _editAction(catalogue, object),
            icon: const Icon(LucideIcons.plus, size: 16),
            label: const Text('Add action'),
          ),
        ),
        if (atLimit)
          Text(
            'A rule can have at most ${catalogue.maxActions} actions.',
            style: AppTypography.caption.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
      ],
    );
  }

  Widget _iconButton(String tooltip, IconData icon, VoidCallback? onPressed) =>
      IconButton(
        tooltip: tooltip,
        icon: Icon(icon, size: 18),
        constraints: const BoxConstraints(minWidth: 44, minHeight: 44),
        padding: EdgeInsets.zero,
        onPressed: onPressed,
      );

  Future<void> _editAction(
    AutomationCatalogue c,
    AutomationObject o, [
    int? index,
  ]) async {
    final d = _draft!;
    final next = await showActionSheet(
      context,
      catalogue: c,
      object: o,
      draft: index == null ? null : d.actions[index],
    );
    if (next == null || !mounted) return;
    setState(() {
      if (index == null) {
        d.actions.add(next);
      } else {
        d.actions[index] = next;
        _errors.rows.remove('actions.$index');
      }
      _errors.rows.remove('actions');
    });
  }

  void _moveAction(int index, int by) => setState(() {
    final actions = _draft!.actions;
    final to = index + by;
    if (to < 0 || to >= actions.length) return;
    actions.insert(to, actions.removeAt(index));
    _errors.rows.removeWhere((k, _) => k.startsWith('actions.'));
  });

  void _removeAction(int index) => setState(() {
    _draft!.actions.removeAt(index);
    // The rows after it move up a place, so their marks no longer fit.
    _errors.rows.removeWhere((k, _) => k.startsWith('actions.'));
  });
}

class _Section extends StatelessWidget {
  const _Section({required this.label, required this.children});

  final String label;
  final List<Widget> children;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.fromLTRB(12, 10, 12, 12),
    decoration: BoxDecoration(
      color: AppColors.surface,
      borderRadius: BorderRadius.circular(8),
      border: Border.all(color: AppColors.border),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          label,
          style: AppTypography.overline.copyWith(
            color: AppColors.textSecondary,
            letterSpacing: 1.2,
          ),
        ),
        const SizedBox(height: 8),
        ...children,
      ],
    ),
  );
}

/// A tappable line: the trigger, or one condition's card.
class _Row extends StatelessWidget {
  const _Row({required this.onTap, required this.child, this.bordered = false});

  final VoidCallback onTap;
  final Widget child;
  final bool bordered;

  @override
  Widget build(BuildContext context) => Material(
    color: bordered ? AppColors.gray50 : Colors.transparent,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(8),
      side: bordered ? BorderSide(color: AppColors.border) : BorderSide.none,
    ),
    clipBehavior: Clip.antiAlias,
    child: InkWell(
      onTap: onTap,
      child: ConstrainedBox(
        constraints: const BoxConstraints(minHeight: 48),
        child: Padding(
          padding: EdgeInsets.fromLTRB(bordered ? 12 : 0, 4, 4, 4),
          child: Align(alignment: Alignment.centerLeft, child: child),
        ),
      ),
    ),
  );
}

class _GeneralError extends StatelessWidget {
  const _GeneralError({super.key, required this.message});

  final String message;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(12),
    decoration: BoxDecoration(
      color: AppColors.danger50,
      border: Border.all(color: AppColors.danger500),
      borderRadius: BorderRadius.circular(8),
    ),
    child: Text(
      message,
      style: AppTypography.body.copyWith(color: AppColors.danger600),
    ),
  );
}

class _MemberNotice extends StatelessWidget {
  const _MemberNotice();

  @override
  Widget build(BuildContext context) => Center(
    child: Padding(
      padding: const EdgeInsets.all(32),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(LucideIcons.lock, size: 40, color: AppColors.textTertiary),
          const SizedBox(height: 16),
          Text(
            'Only an organization admin can see automation rules.',
            style: AppTypography.body,
            textAlign: TextAlign.center,
          ),
        ],
      ),
    ),
  );
}

class _ErrorState extends StatelessWidget {
  const _ErrorState({required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) => Center(
    child: Padding(
      padding: const EdgeInsets.all(32),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            LucideIcons.triangleAlert,
            size: 40,
            color: AppColors.textTertiary,
          ),
          const SizedBox(height: 16),
          Text(message, style: AppTypography.body, textAlign: TextAlign.center),
          const SizedBox(height: 16),
          OutlinedButton(onPressed: onRetry, child: const Text('Try again')),
        ],
      ),
    ),
  );
}
