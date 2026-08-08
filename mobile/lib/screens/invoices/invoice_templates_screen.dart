import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';

import '../../core/theme/theme.dart';
import '../../data/models/invoice_template.dart';
import '../../providers/auth_provider.dart';
import '../../providers/invoice_extras_provider.dart';
import '../../routes/app_router.dart';
import '../../widgets/common/badge.dart';
import 'invoice_shell.dart';
import 'invoice_template_form_screen.dart' show swatchColor;

/// PDF templates: the catalogue, and the writes an admin can make from a phone.
///
/// Reading is open to every member, since knowing which template an invoice
/// will print in is useful to whoever raised it. Creating, editing and
/// re-pointing the default are admin-only, which the API enforces
/// (`_forbid_non_admin_template`); the controls below are hidden from everyone
/// else as a courtesy, not as the check.
///
/// **The layout itself is still edited on the web.** A template's body is
/// org-authored HTML and CSS that WeasyPrint renders server-side, it never
/// leaves the admin-only editor route, and a two-pane markup editor is not a
/// 390px screen. Everything else about a template is ordinary form input, so
/// that is what the form screen owns, and a save from here leaves the markup
/// untouched.
class InvoiceTemplatesScreen extends ConsumerWidget {
  const InvoiceTemplatesScreen({super.key});

  Future<void> _setDefault(
    BuildContext context,
    WidgetRef ref,
    InvoiceTemplate template,
  ) async {
    final error = await ref
        .read(invoiceTemplatesProvider.notifier)
        .setDefault(template.id);
    if (!context.mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          error ?? '${template.name} is now the default for new invoices',
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(invoiceTemplatesProvider);
    final isAdmin = ref.watch(isOrgAdminProvider);

    return Scaffold(
      backgroundColor: AppColors.surfaceDim,
      appBar: AppBar(
        title: const Text('Templates'),
        backgroundColor: AppColors.surface,
        elevation: 0,
        scrolledUnderElevation: 1,
        actions: [
          if (isAdmin)
            IconButton(
              icon: const Icon(LucideIcons.plus),
              tooltip: 'New template',
              onPressed: () => context.push(AppRoutes.invoiceTemplateNew),
            ),
        ],
      ),
      body: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (_, _) => InvoiceErrorState(
          message: 'Could not load templates',
          onRetry: () => ref.read(invoiceTemplatesProvider.notifier).refresh(),
        ),
        data: (templates) {
          if (templates.isEmpty) {
            return InvoiceEmptyState(
              icon: LucideIcons.layoutTemplate,
              message: 'No templates yet',
              detail: isAdmin
                  ? 'Invoices use the built-in layout until one is added.'
                  : 'Invoices use the built-in layout. An administrator adds '
                        'these.',
            );
          }
          return RefreshIndicator(
            onRefresh: () =>
                ref.read(invoiceTemplatesProvider.notifier).refresh(),
            child: ListView(
              padding: const EdgeInsets.only(bottom: 96),
              children: [
                for (final t in templates)
                  _TemplateCard(
                    template: t,
                    canManage: isAdmin,
                    onEdit: () =>
                        context.push(AppRoutes.invoiceTemplateEditFor(t.id)),
                    onSetDefault: () => _setDefault(context, ref, t),
                  ),
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
                  child: Text(
                    'A template\'s PDF layout is HTML and CSS, and it is '
                    'edited on the web. The name, colours, logo and '
                    'boilerplate are editable here.',
                    style: AppTypography.caption.copyWith(
                      color: AppColors.textSecondary,
                    ),
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}

class _TemplateCard extends StatelessWidget {
  const _TemplateCard({
    required this.template,
    required this.canManage,
    required this.onEdit,
    required this.onSetDefault,
  });

  final InvoiceTemplate template;
  final bool canManage;
  final VoidCallback onEdit;
  final VoidCallback onSetDefault;

  @override
  Widget build(BuildContext context) {
    final primary = swatchColor(template.primaryColor);

    return Container(
      color: AppColors.surface,
      margin: const EdgeInsets.only(bottom: 1),
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              if (primary != null) ...[
                Container(
                  width: 18,
                  height: 18,
                  decoration: BoxDecoration(
                    color: primary,
                    borderRadius: BorderRadius.circular(4),
                    border: Border.all(color: AppColors.gray200),
                  ),
                ),
                const SizedBox(width: 10),
              ],
              Expanded(
                child: Text(
                  template.name,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: AppTypography.body.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              if (canManage)
                IconButton(
                  icon: const Icon(LucideIcons.pencil, size: 18),
                  tooltip: 'Edit template',
                  onPressed: onEdit,
                ),
            ],
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 4,
            crossAxisAlignment: WrapCrossAlignment.center,
            children: [
              if (template.isDefault)
                StatusBadge(label: 'Default', color: AppColors.success600),
              if (template.hasLogo)
                Text(
                  'logo',
                  style: AppTypography.caption.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
              // Whether custom markup exists, never what it says.
              if (template.hasCustomHtml)
                Text(
                  'custom layout',
                  style: AppTypography.caption.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
              Text(
                template.usedOnInvoices == 0
                    ? 'unused'
                    : 'on ${template.usedOnInvoices} invoice'
                          '${template.usedOnInvoices == 1 ? '' : 's'}',
                style: AppTypography.caption.copyWith(
                  color: AppColors.textTertiary,
                ),
              ),
            ],
          ),
          // Making a template the default is a swap, not a toggle: the model
          // clears the flag on every other row in one transaction. So the one
          // already holding it gets no control, because there is nothing to
          // offer that would not leave the org without a default.
          if (canManage && !template.isDefault) ...[
            const SizedBox(height: 8),
            SizedBox(
              height: 44,
              child: OutlinedButton(
                onPressed: onSetDefault,
                child: const Text('Use for new invoices'),
              ),
            ),
          ],
        ],
      ),
    );
  }
}
