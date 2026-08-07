import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';

import '../../core/theme/theme.dart';
import '../../data/models/deal.dart' show Currency;
import '../../data/models/product.dart';
import '../../providers/auth_provider.dart';
import '../../providers/invoice_extras_provider.dart';
import '../../widgets/common/badge.dart';
import 'invoice_format.dart';
import 'invoice_shell.dart';
import 'product_form_sheet.dart';

/// The product catalogue.
///
/// Read is open to every member because building a line item needs it; create,
/// edit and delete are admin-only and `ProductListView` / `ProductDetailView`
/// answer 403 to anyone else. The buttons follow that rule so a member is not
/// offered an action that cannot work, which is UX rather than a guard.
class ProductsListScreen extends ConsumerStatefulWidget {
  const ProductsListScreen({super.key});

  @override
  ConsumerState<ProductsListScreen> createState() => _ProductsListScreenState();
}

class _ProductsListScreenState extends ConsumerState<ProductsListScreen> {
  final _searchController = TextEditingController();
  Timer? _debounce;

  @override
  void dispose() {
    _debounce?.cancel();
    _searchController.dispose();
    super.dispose();
  }

  void _onSearchChanged(String value) {
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 300), () {
      ref.read(productsProvider.notifier).search(value);
    });
  }

  Future<void> _edit(Product? existing) async {
    final saved = await showProductFormSheet(context, existing);
    if (saved == null || !mounted) return;
    final notifier = ref.read(productsProvider.notifier);
    final error = existing == null
        ? await notifier.createProduct(saved)
        : await notifier.updateProduct(existing.id, saved);
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          error ?? (existing == null ? 'Product added' : 'Product saved'),
        ),
      ),
    );
  }

  Future<void> _delete(Product product) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Delete ${product.name}?'),
        content: Text(
          product.usedOn > 0
              // Line items denormalise their own name and price, and the FK is
              // SET_NULL, so history survives. Saying so stops a needless
              // hesitation, and deactivating is usually what was wanted.
              ? 'It is on ${product.usedOn} invoice${product.usedOn == 1 ? '' : 's'}. '
                    'Those keep the name and price they were billed at. '
                    'Deactivating it instead keeps it out of new invoices.'
              : 'It is not on any invoice yet.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Keep it'),
          ),
          TextButton(
            onPressed: () => Navigator.of(context).pop(true),
            style: TextButton.styleFrom(foregroundColor: AppColors.danger600),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;
    final error = await ref
        .read(productsProvider.notifier)
        .deleteProduct(product.id);
    if (!mounted) return;
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(error ?? 'Product deleted')));
  }

  @override
  Widget build(BuildContext context) {
    final async = ref.watch(productsProvider);
    final isAdmin = ref.watch(isOrgAdminProvider);

    return Scaffold(
      backgroundColor: AppColors.surfaceDim,
      appBar: AppBar(
        title: const Text('Products'),
        backgroundColor: AppColors.surface,
        elevation: 0,
        scrolledUnderElevation: 1,
        actions: [
          if (isAdmin)
            IconButton(
              icon: const Icon(LucideIcons.plus),
              tooltip: 'New product',
              onPressed: () => _edit(null),
            ),
        ],
      ),
      body: Column(
        children: [
          Container(
            color: AppColors.surface,
            padding: const EdgeInsets.fromLTRB(12, 8, 12, 8),
            child: TextField(
              controller: _searchController,
              onChanged: _onSearchChanged,
              textInputAction: TextInputAction.search,
              decoration: const InputDecoration(
                hintText: 'Search the catalogue',
                prefixIcon: Icon(LucideIcons.search, size: 18),
                isDense: true,
                border: OutlineInputBorder(),
              ),
            ),
          ),
          Expanded(
            child: async.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (_, _) => InvoiceErrorState(
                message: 'Could not load the catalogue',
                onRetry: () => ref.read(productsProvider.notifier).refresh(),
              ),
              data: (products) {
                if (products.isEmpty) {
                  return InvoiceEmptyState(
                    icon: LucideIcons.package,
                    message: _searchController.text.isEmpty
                        ? 'Nothing in the catalogue yet'
                        : 'No products match that search',
                    detail: isAdmin || _searchController.text.isNotEmpty
                        ? null
                        : 'An administrator adds these.',
                  );
                }
                return RefreshIndicator(
                  onRefresh: () =>
                      ref.read(productsProvider.notifier).refresh(),
                  child: ListView.builder(
                    padding: const EdgeInsets.only(bottom: 96),
                    itemCount: products.length,
                    itemBuilder: (context, i) => _ProductRow(
                      product: products[i],
                      canEdit: isAdmin,
                      onEdit: () => _edit(products[i]),
                      onDelete: () => _delete(products[i]),
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _ProductRow extends StatelessWidget {
  const _ProductRow({
    required this.product,
    required this.canEdit,
    required this.onEdit,
    required this.onDelete,
  });

  final Product product;
  final bool canEdit;
  final VoidCallback onEdit;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    return Container(
      color: AppColors.surface,
      margin: const EdgeInsets.only(bottom: 1),
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Text(
                  product.name,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: AppTypography.body.copyWith(
                    fontWeight: FontWeight.w600,
                    color: product.isActive
                        ? AppColors.textPrimary
                        : AppColors.textSecondary,
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Text(
                money(
                  product.price,
                  Currency.fromString(product.currency).symbol,
                ),
                style: AppTypography.body.copyWith(fontWeight: FontWeight.w600),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Wrap(
            spacing: 8,
            runSpacing: 4,
            crossAxisAlignment: WrapCrossAlignment.center,
            children: [
              if (!product.isActive)
                StatusBadge(label: 'Retired', color: AppColors.gray500),
              if (product.sku?.isNotEmpty == true)
                Text(
                  product.sku!,
                  style: AppTypography.caption.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
              if (product.category?.isNotEmpty == true)
                Text(
                  product.category!,
                  style: AppTypography.caption.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
              Text(
                product.usedOn == 0
                    ? 'not billed yet'
                    : 'on ${product.usedOn} invoice${product.usedOn == 1 ? '' : 's'}',
                style: AppTypography.caption.copyWith(
                  color: AppColors.textTertiary,
                ),
              ),
            ],
          ),
          if (canEdit) ...[
            const SizedBox(height: 10),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                SizedBox(
                  height: 40,
                  child: OutlinedButton(
                    onPressed: onEdit,
                    child: const Text('Edit'),
                  ),
                ),
                SizedBox(
                  height: 40,
                  child: OutlinedButton(
                    onPressed: onDelete,
                    style: OutlinedButton.styleFrom(
                      foregroundColor: AppColors.danger600,
                    ),
                    child: const Text('Delete'),
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}
