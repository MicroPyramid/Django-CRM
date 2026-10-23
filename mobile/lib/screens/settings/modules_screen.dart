import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';

import '../../core/theme/theme.dart';
import '../../data/models/org_module.dart';
import '../../providers/auth_provider.dart';
import '../../providers/org_modules_provider.dart';
import '../../routes/app_router.dart';

const _groupTitles = {'sell': 'Sell', 'serve': 'Serve', 'bill': 'Bill'};

/// Switches the organization's modules off and on and orders them. Admin
/// only; the server refuses anyone else, so a member is told without asking.
class ModulesScreen extends ConsumerStatefulWidget {
  const ModulesScreen({super.key});

  @override
  ConsumerState<ModulesScreen> createState() => _ModulesScreenState();
}

class _ModulesScreenState extends ConsumerState<ModulesScreen> {
  bool _saving = false;
  List<String> _refusals = const [];
  String? _refusedKey;

  Future<void> _save(
    String key,
    ({List<String> off, List<String> order})? body,
  ) async {
    if (body == null || _saving) return;
    setState(() {
      _saving = true;
      _refusals = const [];
      _refusedKey = null;
    });
    final messages = await ref
        .read(orgModulesProvider.notifier)
        .save(off: body.off, order: body.order);
    if (!mounted) return;
    setState(() {
      _saving = false;
      _refusals = messages;
      _refusedKey = key;
    });
  }

  Future<void> _switchOff(OrgModulesAnswer answer, OrgModule m) async {
    final sure = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Switch off ${m.label}?'),
        content: Text(m.stops),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Keep it on'),
          ),
          TextButton(
            style: TextButton.styleFrom(foregroundColor: AppColors.danger600),
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Switch off'),
          ),
        ],
      ),
    );
    if (sure != true || !mounted) return;
    await _save(m.key, answer.switchBody(m.key, false));
  }

  @override
  Widget build(BuildContext context) {
    final isAdmin = ref.watch(isOrgAdminProvider);
    return Scaffold(
      backgroundColor: AppColors.surfaceDim,
      appBar: AppBar(
        title: const Text('Modules'),
        backgroundColor: AppColors.surface,
        elevation: 0,
        scrolledUnderElevation: 1,
      ),
      body: isAdmin ? _body() : const _Notice(_memberText),
    );
  }

  Widget _body() {
    final async = ref.watch(orgModulesProvider);
    final answer = ref.watch(shownModulesProvider);
    if (answer == null) {
      if (async.isLoading) {
        return const Center(child: CircularProgressIndicator());
      }
      if (async.hasError) {
        return _ErrorState(
          message: 'Could not load modules',
          onRetry: () => ref.invalidate(orgModulesProvider),
        );
      }
      return const _Notice('This server does not offer modules yet.');
    }
    if (!answer.canEdit) return const _Notice(_memberText);
    final children = <Widget>[
      if (_saving) const LinearProgressIndicator(minHeight: 2),
      Padding(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
        child: Text(
          'Switch off what this organization does not use. Nothing is '
          'deleted: switching a module back on brings everything back as it '
          'was.',
          style: AppTypography.body.copyWith(color: AppColors.textSecondary),
        ),
      ),
      if (_refusals.isNotEmpty)
        _RefusalBox(
          messages: _refusals,
          moduleKey: _refusedKey,
          onWebForms: () => context.push(AppRoutes.settingsWebForms),
          onInboundEmail: () => context.push(AppRoutes.settingsInboundEmail),
        ),
      for (final group in moduleGroups) ...[
        _SectionHeader(_groupTitles[group] ?? group),
        for (final m in answer.modules)
          if (m.group == group)
            _ModuleCard(
              module: m,
              answer: answer,
              saving: _saving,
              canUp: answer.moveBody(m.key, 'up') != null,
              canDown: answer.moveBody(m.key, 'down') != null,
              onSwitchOff: () => _switchOff(answer, m),
              onSwitchOn: () => _save(m.key, answer.switchBody(m.key, true)),
              onMove: (d) => _save(m.key, answer.moveBody(m.key, d)),
            ),
      ],
    ];
    return ListView(
      padding: const EdgeInsets.only(bottom: 48),
      children: children,
    );
  }
}

const _memberText = 'Only an organization admin can switch modules on or off.';

class _ModuleCard extends StatelessWidget {
  const _ModuleCard({
    required this.module,
    required this.answer,
    required this.saving,
    required this.canUp,
    required this.canDown,
    required this.onSwitchOff,
    required this.onSwitchOn,
    required this.onMove,
  });

  final OrgModule module;
  final OrgModulesAnswer answer;
  final bool saving;
  final bool canUp;
  final bool canDown;
  final VoidCallback onSwitchOff;
  final VoidCallback onSwitchOn;
  final void Function(String direction) onMove;

  @override
  Widget build(BuildContext context) {
    final need = module.needs;
    final needOff = need != null && !answer.isOn(need);
    final needLabel = need == null ? '' : answer.labelOf(need);
    // Off when available; on only for a module switched off whose need is on.
    VoidCallback? action;
    if (!saving) {
      if (module.available) {
        action = onSwitchOff;
      } else if (!module.enabled && !needOff) {
        action = onSwitchOn;
      }
    }
    return Container(
      margin: const EdgeInsets.fromLTRB(16, 0, 16, 10),
      padding: const EdgeInsets.fromLTRB(14, 8, 4, 8),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: AppColors.border),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Padding(
              padding: const EdgeInsets.only(top: 6),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    module.label,
                    style: AppTypography.body.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  if (module.covers.isNotEmpty) ...[
                    const SizedBox(height: 3),
                    Text(
                      module.covers,
                      style: AppTypography.caption.copyWith(
                        color: AppColors.textSecondary,
                      ),
                    ),
                  ],
                  if (needOff) ...[
                    const SizedBox(height: 6),
                    Text(
                      'Needs $needLabel.'
                      '${module.enabled ? ' It comes back when $needLabel is switched on.' : ''}',
                      style: AppTypography.caption.copyWith(
                        color: AppColors.warning700,
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
          const SizedBox(width: 4),
          Semantics(
            label: module.label,
            child: Switch(
              value: module.available,
              onChanged: action == null ? null : (_) => action!(),
            ),
          ),
          Column(
            children: [
              _MoveButton(
                tooltip: 'Move up',
                icon: LucideIcons.chevronUp,
                onPressed: canUp && !saving ? () => onMove('up') : null,
              ),
              _MoveButton(
                tooltip: 'Move down',
                icon: LucideIcons.chevronDown,
                onPressed: canDown && !saving ? () => onMove('down') : null,
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _MoveButton extends StatelessWidget {
  const _MoveButton({
    required this.tooltip,
    required this.icon,
    required this.onPressed,
  });

  final String tooltip;
  final IconData icon;
  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) => IconButton(
    tooltip: tooltip,
    onPressed: onPressed,
    icon: Icon(icon, size: 20),
    constraints: const BoxConstraints(minWidth: 44, minHeight: 44),
    padding: EdgeInsets.zero,
  );
}

class _RefusalBox extends StatelessWidget {
  const _RefusalBox({
    required this.messages,
    required this.moduleKey,
    required this.onWebForms,
    required this.onInboundEmail,
  });

  final List<String> messages;
  final String? moduleKey;
  final VoidCallback onWebForms;
  final VoidCallback onInboundEmail;

  @override
  Widget build(BuildContext context) {
    final forms = moduleKey == 'leads' || moduleKey == 'tickets';
    final mail = moduleKey == 'tickets';
    return Container(
      margin: const EdgeInsets.fromLTRB(16, 12, 16, 0),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.danger50,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: AppColors.danger100),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          for (final m in messages)
            Padding(
              padding: const EdgeInsets.only(bottom: 4),
              child: Text(
                m,
                style: AppTypography.caption.copyWith(
                  color: AppColors.danger700,
                ),
              ),
            ),
          if (forms || mail)
            Wrap(
              spacing: 8,
              children: [
                if (forms)
                  OutlinedButton(
                    onPressed: onWebForms,
                    child: const Text('Web forms'),
                  ),
                if (mail)
                  OutlinedButton(
                    onPressed: onInboundEmail,
                    child: const Text('Inbound email'),
                  ),
              ],
            ),
        ],
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  const _SectionHeader(this.title);

  final String title;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.fromLTRB(16, 20, 16, 8),
    child: Text(
      title.toUpperCase(),
      style: AppTypography.overline.copyWith(
        color: AppColors.textSecondary,
        letterSpacing: 1.2,
      ),
    ),
  );
}

class _Notice extends StatelessWidget {
  const _Notice(this.message);

  final String message;

  @override
  Widget build(BuildContext context) => Center(
    child: Padding(
      padding: const EdgeInsets.all(32),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(LucideIcons.lock, size: 40, color: AppColors.textTertiary),
          const SizedBox(height: 16),
          Text(message, style: AppTypography.body, textAlign: TextAlign.center),
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
