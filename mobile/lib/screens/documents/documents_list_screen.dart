import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';

import '../../config/api_config.dart';
import '../../core/theme/theme.dart';
import '../../data/models/crm_document.dart';
import '../../providers/auth_provider.dart';
import '../../providers/documents_provider.dart';
import '../../routes/app_router.dart';
import '../../services/attachment_upload.dart';
import '../../widgets/common/badge.dart';

/// Files shared across the org.
///
/// Read-only here. The server has already scoped the rows to the org and, for a
/// non-admin, to the documents they may open, so every row on this screen is
/// one the viewer is allowed to see. Uploading and editing live on their own
/// screen so a destructive path is a deliberate act rather than a mis-tap in a
/// list.
///
/// Tapping a row downloads the file through
/// `GET /api/documents/<id>/download/`, which is gated by the same read
/// predicate as the record, so a row that lists is a row that opens. The
/// stored `document_file` path is still never turned into a URL: it resolves
/// under `/media/`, which has no per-file authorization, so a link built from
/// it would be readable by other tenants and unusable by its owner.
///
/// Reading is the broad act and editing the narrow one, so the row itself is
/// the download and the pencil beside it is the edit, shown only to the
/// uploader and admins. That is the same split the web list uses.
class DocumentsListScreen extends ConsumerWidget {
  const DocumentsListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(documentsProvider);
    final isAdmin = ref.watch(isOrgAdminProvider);
    final myEmail = ref.watch(myEmailProvider);
    final includeArchived = ref.watch(documentsArchivedProvider);

    return Scaffold(
      backgroundColor: AppColors.surfaceDim,
      appBar: AppBar(
        title: const Text('Documents'),
        backgroundColor: AppColors.surface,
        elevation: 0,
        scrolledUnderElevation: 1,
        actions: [
          IconButton(
            icon: Icon(includeArchived ? LucideIcons.eyeOff : LucideIcons.eye),
            tooltip: includeArchived ? 'Hide archived' : 'Show archived',
            onPressed: () =>
                ref.read(documentsArchivedProvider.notifier).toggle(),
          ),
          // Not gated on role: `DocumentListView.post` checks authentication
          // and org context and nothing else, so any member may upload. A UI
          // claiming otherwise would be inventing a rule the server does not
          // enforce.
          IconButton(
            icon: const Icon(LucideIcons.upload),
            tooltip: 'Upload',
            onPressed: () => context.push(AppRoutes.documentNew),
          ),
        ],
      ),
      body: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (_, _) => _ErrorState(
          onRetry: () => ref.read(documentsProvider.notifier).refresh(),
        ),
        data: (data) {
          if (data.documents.isEmpty) {
            return _EmptyState(includeArchived: includeArchived);
          }
          return RefreshIndicator(
            onRefresh: () => ref.read(documentsProvider.notifier).refresh(),
            child: ListView(
              padding: const EdgeInsets.only(bottom: 96),
              children: [
                _Summary(
                  totals: data.totals,
                  includeArchived: data.includeArchived,
                ),
                for (final doc in data.documents)
                  _DocumentRow(
                    doc: doc,
                    canWrite: canWriteDocument(
                      isAdmin: isAdmin,
                      myEmail: myEmail,
                      uploaderEmail: doc.uploaderEmail,
                    ),
                    onEdit: () =>
                        context.push(AppRoutes.documentEditFor(doc.id)),
                  ),
              ],
            ),
          );
        },
      ),
    );
  }
}

IconData documentIcon(DocumentKind kind) {
  switch (kind) {
    case DocumentKind.pdf:
      return LucideIcons.fileType;
    case DocumentKind.sheet:
      return LucideIcons.sheet;
    case DocumentKind.text:
      return LucideIcons.fileText;
    case DocumentKind.file:
      return LucideIcons.file;
  }
}

class _Summary extends StatelessWidget {
  const _Summary({required this.totals, required this.includeArchived});

  final DocumentTotals totals;
  final bool includeArchived;

  @override
  Widget build(BuildContext context) {
    return Container(
      color: AppColors.surface,
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
      margin: const EdgeInsets.only(bottom: 1),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Wrap(
            spacing: 20,
            runSpacing: 10,
            children: [
              _Stat(value: '${totals.active}', label: 'active'),
              if (includeArchived)
                _Stat(value: '${totals.archived}', label: 'archived'),
              _Stat(value: '${totals.unshared}', label: 'shared with nobody'),
            ],
          ),
          if (!includeArchived) ...[
            const SizedBox(height: 8),
            Text(
              // The archived ones are excluded from the request, not filtered
              // out here, so the counts above genuinely do not cover them.
              'Archived documents are not shown or counted. Use the eye in the '
              'header to include them.',
              style: AppTypography.caption.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _Stat extends StatelessWidget {
  const _Stat({required this.value, required this.label});

  final String value;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(
          value,
          style: AppTypography.h2.copyWith(fontWeight: FontWeight.w600),
        ),
        Text(
          label,
          style: AppTypography.caption.copyWith(color: AppColors.textSecondary),
        ),
      ],
    );
  }
}

class _DocumentRow extends StatefulWidget {
  const _DocumentRow({
    required this.doc,
    required this.canWrite,
    required this.onEdit,
  });

  final CrmDocument doc;
  final bool canWrite;
  final VoidCallback onEdit;

  @override
  State<_DocumentRow> createState() => _DocumentRowState();
}

class _DocumentRowState extends State<_DocumentRow> {
  bool _downloading = false;

  CrmDocument get doc => widget.doc;
  bool get canWrite => widget.canWrite;

  /// Fetch the bytes with the token attached, then let the OS choose where to
  /// put them. The progress state is not decoration: a large file is a long
  /// silence otherwise, and a second tap would start a second download.
  Future<void> _download() async {
    if (_downloading) return;
    setState(() => _downloading = true);
    final result = await downloadAttachment(
      url: ApiConfig.documentDownload(doc.id),
      fileName: doc.fileName,
    );
    if (!mounted) return;
    setState(() => _downloading = false);
    if (result.success) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(result.error ?? 'Could not download that file.'),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return InkWell(
      // Reading is the broad privilege, so the row is the download. A row with
      // no file behind it does not respond rather than failing on tap.
      onTap: doc.hasFile ? _download : null,
      child: Container(
        color: AppColors.surface,
        margin: const EdgeInsets.only(bottom: 1),
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.only(top: 2),
              child: Icon(
                documentIcon(doc.kind),
                size: 20,
                color: doc.isArchived
                    ? AppColors.textTertiary
                    : AppColors.textSecondary,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    doc.title,
                    style: AppTypography.body.copyWith(
                      fontWeight: FontWeight.w600,
                      color: doc.isArchived
                          ? AppColors.textSecondary
                          : AppColors.textPrimary,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    '${doc.fileName} · ${documentSizeLabel(doc.sizeBytes)}',
                    style: AppTypography.caption.copyWith(
                      color: AppColors.textSecondary,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 4),
                  Text(
                    documentShareSummary(doc),
                    style: AppTypography.caption.copyWith(
                      color: AppColors.textTertiary,
                    ),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 6),
                  Wrap(
                    spacing: 8,
                    runSpacing: 6,
                    crossAxisAlignment: WrapCrossAlignment.center,
                    children: [
                      if (doc.isArchived)
                        StatusBadge(
                          label: 'Archived',
                          color: AppColors.gray500,
                        ),
                      Text(
                        'Uploaded by ${doc.uploaderName}',
                        style: AppTypography.caption.copyWith(
                          color: AppColors.textTertiary,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            if (_downloading)
              const Padding(
                padding: EdgeInsets.all(12),
                child: SizedBox(
                  width: 18,
                  height: 18,
                  child: CircularProgressIndicator(strokeWidth: 2),
                ),
              )
            else if (doc.hasFile)
              const Padding(
                padding: EdgeInsets.all(12),
                child: Icon(
                  LucideIcons.download,
                  size: 18,
                  color: AppColors.textTertiary,
                ),
              ),
            // Editing is the uploader's and an admin's. A 44px target, its own
            // tap area, so a thumb aiming at Edit does not start a download.
            if (canWrite)
              IconButton(
                onPressed: widget.onEdit,
                icon: const Icon(LucideIcons.pencil, size: 18),
                color: AppColors.textTertiary,
                tooltip: 'Manage this document',
                constraints: const BoxConstraints(minWidth: 44, minHeight: 44),
              ),
          ],
        ),
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({required this.includeArchived});

  final bool includeArchived;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(LucideIcons.folder, size: 40, color: AppColors.textTertiary),
            const SizedBox(height: 16),
            Text('No documents', style: AppTypography.h3),
            const SizedBox(height: 8),
            Text(
              // The list is narrowed to what this person may open, so "there
              // are none" would be a claim about the org that this screen
              // cannot make.
              includeArchived
                  ? 'Nothing has been shared with you, and you have uploaded '
                        'nothing yourself.'
                  : 'Nothing active has been shared with you. There may be '
                        'archived documents: use the eye in the header.',
              style: AppTypography.body.copyWith(
                color: AppColors.textSecondary,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}

class _ErrorState extends StatelessWidget {
  const _ErrorState({required this.onRetry});

  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
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
            Text('Could not load the documents', style: AppTypography.body),
            const SizedBox(height: 16),
            OutlinedButton(onPressed: onRetry, child: const Text('Try again')),
          ],
        ),
      ),
    );
  }
}
