import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';

import '../../config/api_config.dart';
import '../../core/theme/theme.dart';
import '../../data/models/custom_object.dart';
import '../../providers/custom_objects_provider.dart';
import '../../services/attachment_upload.dart';

const _columns = 3;
const _gap = 8.0;
const _tileDecodeWidth = 300;

/// A record's photos as a three-column sliver, so only tiles near the
/// viewport are built and download their file (there are no thumbnails).
/// Place it inside a `CustomScrollView`.
class PhotoGallery extends StatelessWidget {
  const PhotoGallery({super.key, required this.photos, this.onDelete});

  final List<RecordAttachment> photos;

  /// Offered in the viewer for a photo whose `canDelete` is true.
  final void Function(RecordAttachment photo)? onDelete;

  @override
  Widget build(BuildContext context) {
    return SliverGrid.builder(
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: _columns,
        mainAxisSpacing: _gap,
        crossAxisSpacing: _gap,
      ),
      itemCount: photos.length,
      itemBuilder: (context, i) => _PhotoTile(
        key: ValueKey('photo-${photos[i].id}'),
        photo: photos[i],
        onTap: () => Navigator.of(context).push(
          MaterialPageRoute<void>(
            builder: (_) => _PhotoViewer(photo: photos[i], onDelete: onDelete),
          ),
        ),
      ),
    );
  }
}

Widget _broken() => Center(
  child: Icon(LucideIcons.imageOff, color: AppColors.textTertiary, size: 24),
);

class _PhotoTile extends ConsumerWidget {
  const _PhotoTile({super.key, required this.photo, required this.onTap});

  final RecordAttachment photo;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final bytes = ref.watch(attachmentBytesProvider(photo.id));
    return Semantics(
      button: true,
      label: photo.fileName,
      child: Material(
        key: const ValueKey('photo-tile'),
        color: AppColors.gray100,
        borderRadius: AppLayout.borderRadiusMd,
        clipBehavior: Clip.antiAlias,
        child: InkWell(
          onTap: onTap,
          child: bytes.when(
            loading: () => const Center(
              child: SizedBox(
                width: 18,
                height: 18,
                child: CircularProgressIndicator(strokeWidth: 2),
              ),
            ),
            error: (_, _) => _broken(),
            data: (data) => data == null
                ? _broken()
                : Image.memory(
                    data,
                    cacheWidth: _tileDecodeWidth,
                    fit: BoxFit.cover,
                    errorBuilder: (_, _, _) => _broken(),
                  ),
          ),
        ),
      ),
    );
  }
}

class _PhotoViewer extends ConsumerWidget {
  const _PhotoViewer({required this.photo, this.onDelete});

  final RecordAttachment photo;
  final void Function(RecordAttachment photo)? onDelete;

  Future<void> _save(BuildContext context) async {
    final messenger = ScaffoldMessenger.of(context);
    final result = await downloadAttachment(
      url: ApiConfig.attachmentDownload(photo.id),
      fileName: photo.fileName,
    );
    if (result.success) return;
    messenger.showSnackBar(
      SnackBar(
        content: Text(result.error ?? 'Could not download that file.'),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final bytes = ref.watch(attachmentBytesProvider(photo.id)).value;
    final canDelete = onDelete != null && photo.canDelete;
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        foregroundColor: Colors.white,
        title: Text(photo.fileName, overflow: TextOverflow.ellipsis),
        actions: [
          IconButton(
            tooltip: 'Save',
            icon: const Icon(LucideIcons.download),
            onPressed: () => _save(context),
          ),
          if (canDelete)
            IconButton(
              tooltip: 'Delete photo',
              icon: const Icon(LucideIcons.trash2),
              onPressed: () {
                Navigator.of(context).pop();
                onDelete!(photo);
              },
            ),
        ],
      ),
      body: bytes == null
          ? Center(child: Icon(LucideIcons.imageOff, color: Colors.white54))
          : InteractiveViewer(
              maxScale: 5,
              child: Center(
                child: Image.memory(
                  bytes,
                  fit: BoxFit.contain,
                  errorBuilder: (_, _, _) =>
                      Icon(LucideIcons.imageOff, color: Colors.white54),
                ),
              ),
            ),
    );
  }
}
