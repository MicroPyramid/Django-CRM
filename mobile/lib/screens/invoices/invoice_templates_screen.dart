import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';

import '../../core/theme/theme.dart';
import '../../data/models/invoice_template.dart';
import '../../providers/invoice_extras_provider.dart';
import '../../widgets/common/badge.dart';
import 'invoice_shell.dart';

/// PDF templates, read-only by design.
///
/// The web has three pages here: a list, a create form and an editor. Only the
/// list is on mobile, and that is a decision rather than a gap. A template's
/// body is raw HTML and CSS that WeasyPrint renders server-side, so the editor
/// is admin-only and the markup never leaves the editor endpoint. Shipping a
/// markup editor to a phone would mean pulling that markup onto the device to
/// no benefit, and a two-pane HTML editor is not a 390px screen either.
///
/// What is useful on a phone is knowing which template an invoice will come
/// out in and which is the default, so that is what this shows.
class InvoiceTemplatesScreen extends ConsumerWidget {
  const InvoiceTemplatesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(invoiceTemplatesProvider);

    return Scaffold(
      backgroundColor: AppColors.surfaceDim,
      appBar: AppBar(
        title: const Text('Templates'),
        backgroundColor: AppColors.surface,
        elevation: 0,
        scrolledUnderElevation: 1,
      ),
      body: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (_, _) => InvoiceErrorState(
          message: 'Could not load templates',
          onRetry: () => ref.invalidate(invoiceTemplatesProvider),
        ),
        data: (templates) {
          if (templates.isEmpty) {
            return const InvoiceEmptyState(
              icon: LucideIcons.layoutTemplate,
              message: 'No templates yet',
              detail: 'Invoices use the built-in layout until one is added.',
            );
          }
          return RefreshIndicator(
            onRefresh: () async => ref.invalidate(invoiceTemplatesProvider),
            child: ListView(
              padding: const EdgeInsets.only(bottom: 96),
              children: [
                for (final t in templates) _TemplateCard(template: t),
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
                  child: Text(
                    'Templates are edited on the web. The layout is HTML and '
                    'CSS that renders into the PDF, and only an administrator '
                    'can change it.',
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
  const _TemplateCard({required this.template});

  final InvoiceTemplate template;

  /// `#RRGGBB` to a swatch, falling back to grey rather than throwing on
  /// anything unexpected: the value is org-authored free text.
  Color? _swatch(String? hex) {
    final value = hex?.replaceAll('#', '').trim() ?? '';
    if (value.length != 6) return null;
    final parsed = int.tryParse(value, radix: 16);
    return parsed == null ? null : Color(0xFF000000 | parsed);
  }

  @override
  Widget build(BuildContext context) {
    final primary = _swatch(template.primaryColor);

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
        ],
      ),
    );
  }
}
