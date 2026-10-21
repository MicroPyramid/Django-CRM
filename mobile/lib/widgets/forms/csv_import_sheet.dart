import 'dart:convert';
import 'dart:typed_data';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';

import '../../core/theme/theme.dart';
import '../../providers/csv_import_provider.dart';
import '../../services/attachment_upload.dart' show clearAttachmentPickerCache;

/// Open the import sheet for [target].
///
/// After a successful contacts or leads import the sheet stays open on a done
/// step, as the web's `ImportFlow` does: what was created, the values left
/// blank, and the skipped rows, which can be saved. A ticket import closes at
/// once and a snackbar reports how many were created. Either way [onImported]
/// runs once the sheet has closed, however it was closed, so the list behind
/// it refreshes. The sheet cannot be closed while the import runs: the result
/// arrives through its own pop, so closing it early would leave the list and
/// the dashboard showing nothing of the new records.
///
/// [onUseLeads], when given, turns the contacts sheet's "import as leads"
/// suggestion into a button, as the web's `onUseLeads` does on its first-run
/// page: the sheet previews the same file as leads, and [onUseLeads] runs so
/// the caller knows where the records will land. Without it the suggestion is
/// text.
///
/// [pickFile] and [saveFile] replace the platform pickers in tests; nothing
/// else passes them.
Future<void> showCsvImportSheet(
  BuildContext context,
  CsvImportTarget target, {
  required VoidCallback onImported,
  VoidCallback? onUseLeads,
  Future<PlatformFile?> Function()? pickFile,
  Future<String?> Function(String fileName, List<int> bytes)? saveFile,
}) async {
  final result = await showModalBottomSheet<(CsvImportTarget, int)>(
    context: context,
    isScrollControlled: true,
    useSafeArea: true,
    // A swipe pops the sheet directly, past the PopScope that holds back and
    // a tap outside while the import runs. The close button, Cancel and a tap
    // outside still close it.
    enableDrag: false,
    builder: (_) => CsvImportSheet(
      target: target,
      onUseLeads: onUseLeads,
      pickFile: pickFile,
      saveFile: saveFile,
    ),
  );
  if (result == null || !context.mounted) return;
  final (imported, created) = result;
  // The done step has already said it for a column-matching import.
  if (!imported.usesMapping) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Imported $created ${imported.noun(created)}')),
    );
  }
  onImported();
}

class CsvImportSheet extends ConsumerStatefulWidget {
  const CsvImportSheet({
    super.key,
    required this.target,
    this.onUseLeads,
    this.pickFile,
    this.saveFile,
  });

  final CsvImportTarget target;
  final VoidCallback? onUseLeads;
  final Future<PlatformFile?> Function()? pickFile;
  final Future<String?> Function(String fileName, List<int> bytes)? saveFile;

  @override
  ConsumerState<CsvImportSheet> createState() => _CsvImportSheetState();
}

class _CsvImportSheetState extends ConsumerState<CsvImportSheet> {
  /// Starts as the sheet's target, and becomes leads when a contacts file is
  /// sent in as leads instead.
  late CsvImportTarget _target = widget.target;
  String? _templateNote;
  String? _saveNote;
  bool _showEmpty = false;

  CsvImportNotifier get _notifier =>
      ref.read(csvImportProvider(_target).notifier);

  Future<void> _choose() async {
    final injected = widget.pickFile;
    final picked = await (injected ?? _pickOne)();
    if (!mounted) return;
    setState(() {
      _saveNote = null;
      _showEmpty = false;
    });
    await _notifier.choose(picked);
    // The bytes are held in memory from here on, so the picker's cached copy
    // is not needed for the commit.
    if (injected == null && picked != null) await clearAttachmentPickerCache();
  }

  // Any type, then refused by name: a CSV is labelled text/plain by some
  // Android file managers, and filtering on MIME type would hide it.
  static Future<PlatformFile?> _pickOne() => FilePicker.pickFile();

  /// Ask where to keep [content] as [fileName]. `null` when the person
  /// closed the dialog, a sentence to show otherwise.
  Future<String?> _save(
    String fileName,
    String content, {
    required String saved,
    required String failed,
  }) async {
    try {
      final path = await (widget.saveFile ?? _saveWithPicker)(
        fileName,
        utf8.encode(content),
      );
      return path == null ? null : saved;
    } catch (_) {
      return failed;
    }
  }

  Future<void> _saveTemplate() async {
    final note = await _save(
      _target.templateFileName,
      _target.templateCsv,
      saved: 'Template saved.',
      failed: 'Could not save the template.',
    );
    if (mounted) setState(() => _templateNote = note);
  }

  /// The web drawer's "Download errors": the row errors as a CSV file.
  Future<void> _saveErrors(List<CsvRowError> errors) async {
    final note = await _save(
      _target.errorsFileName,
      csvImportErrorsCsv(errors),
      saved: 'Saved ${_target.errorsFileName}.',
      failed: 'Could not save the errors.',
    );
    if (mounted) setState(() => _saveNote = note);
  }

  /// The web's "Download skipped rows": the file's own columns plus a reason,
  /// to fix and upload again. [rows] are the preview's on the matching step
  /// and the commit's on the done step. A byte-order mark leads, as on the
  /// web, so Excel reads accented names as UTF-8; the importer reads the file
  /// with or without it.
  Future<void> _saveSkipped(List<CsvSkippedRow> rows) async {
    final csv = csvSkippedRowsCsv([
      for (final c in ref.read(csvImportProvider(_target)).columns) c.header,
    ], rows);
    final note = await _save(
      _target.skippedFileName,
      '\uFEFF$csv',
      saved: 'Saved ${_target.skippedFileName}.',
      failed: 'Could not save the skipped rows.',
    );
    if (mounted) setState(() => _saveNote = note);
  }

  static Future<String?> _saveWithPicker(
    String fileName,
    List<int> bytes,
  ) async => (await FilePicker.saveFile(
    dialogTitle: 'Save CSV file',
    fileName: fileName,
    bytes: Uint8List.fromList(bytes),
  ))?.toString();

  /// Send the same file in as leads: the leads import previews the bytes the
  /// contacts one already read, with a fresh guess at its columns.
  void _useLeads() {
    final file = ref.read(csvImportProvider(_target)).file;
    widget.onUseLeads?.call();
    setState(() {
      _target = CsvImportTarget.leads;
      _saveNote = null;
      _showEmpty = false;
    });
    if (file == null) return;
    // After the rebuild, which is what starts watching the leads import; read
    // before it, the import would be discarded as nobody's.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) _notifier.useFile(file);
    });
  }

  /// A column-matching import stays open on its done step. A ticket import
  /// closes at once, and the caller's snackbar says how many.
  Future<void> _commit() async {
    final ok = await _notifier.commit();
    if (!ok || !mounted) return;
    if (_target.usesMapping) {
      // A note about saving the preview's rows is not about the commit's.
      setState(() => _saveNote = null);
      return;
    }
    _close();
  }

  /// Every way out of the sheet comes here. Once an import has succeeded the
  /// pop carries its result, however the sheet is closed, so the caller
  /// still refreshes the list.
  void _close() {
    final result = ref.read(csvImportProvider(_target)).result;
    Navigator.of(
      context,
    ).pop(result == null ? null : (_target, result.created));
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(csvImportProvider(_target));
    final preview = state.preview;
    final mapping = _target.usesMapping;
    // A ticket import has a result only while its sheet animates away.
    final result = mapping ? state.result : null;

    // Back and a tap outside ask before popping. The answer is read when they
    // happen rather than at build, so no frame can slip a pop past an import
    // that has just started.
    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, _) {
        if (didPop) return;
        if (ref.read(csvImportProvider(_target)).committing) return;
        _close();
      },
      child: ConstrainedBox(
        constraints: BoxConstraints(
          maxHeight: MediaQuery.of(context).size.height * 0.9,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 4, 0),
              child: Row(
                children: [
                  const Icon(
                    LucideIcons.upload,
                    size: 18,
                    color: AppColors.textSecondary,
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      mapping
                          ? 'Import ${_target.plural}'
                          : 'Import ${_target.plural} from CSV',
                      style: AppTypography.h3.copyWith(
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                  IconButton(
                    tooltip: 'Close',
                    icon: const Icon(LucideIcons.x, size: 20),
                    onPressed: state.committing ? null : _close,
                  ),
                ],
              ),
            ),
            Flexible(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(16, 4, 16, 12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Text(
                      _target.description,
                      style: AppTypography.bodySmall.copyWith(
                        color: AppColors.textSecondary,
                      ),
                    ),
                    const SizedBox(height: 12),
                    if (result != null)
                      _DoneStep(
                        target: _target,
                        result: result,
                        fields: state.fields,
                        onSaveSkipped: () => _saveSkipped(result.skipped),
                        saveNote: _saveNote,
                      )
                    else ...[
                      if (state.file != null) ...[
                        _FileLine(file: state.file!),
                        const SizedBox(height: 12),
                      ],
                      if (state.busy) ...[
                        const LinearProgressIndicator(minHeight: 2),
                        const SizedBox(height: 12),
                      ],
                      if (preview == null)
                        mapping
                            ? _SpreadsheetHelp(
                                onSaveTemplate: _saveTemplate,
                                note: _templateNote,
                              )
                            : _FormatHelp(
                                target: _target,
                                onSaveTemplate: _saveTemplate,
                                note: _templateNote,
                              )
                      else if (preview.mapped)
                        _MatchStep(
                          target: _target,
                          state: state,
                          showEmpty: _showEmpty,
                          onToggleEmpty: () =>
                              setState(() => _showEmpty = !_showEmpty),
                          onChange: _notifier.setColumnField,
                          onSaveSkipped: () => _saveSkipped(state.skipped),
                          saveNote: _saveNote,
                          onUseLeads: widget.onUseLeads == null
                              ? null
                              : _useLeads,
                        )
                      else
                        _PreviewSummary(
                          target: _target,
                          preview: preview,
                          onSaveErrors: _saveErrors,
                          errorsNote: _saveNote,
                        ),
                      if (state.commitErrors.isNotEmpty) ...[
                        const SizedBox(height: 12),
                        _RowErrors(
                          heading:
                              'Server rejected ${state.commitErrors.length} '
                              'row${state.commitErrors.length == 1 ? '' : 's'} '
                              'during import. The file may have changed since '
                              'preview',
                          errors: state.commitErrors,
                          onSave: _saveErrors,
                          note: _saveNote,
                        ),
                      ],
                      if (state.error != null) ...[
                        const SizedBox(height: 12),
                        _Alert(message: state.error!),
                        // A failed re-preview leaves the counts of an older
                        // choice on screen, so the import waits for this.
                        if (state.stale && !state.busy)
                          Align(
                            alignment: AlignmentDirectional.centerStart,
                            child: TextButton(
                              style: _textButton,
                              onPressed: _notifier.retryPreview,
                              child: const Text('Try again'),
                            ),
                          ),
                      ],
                    ],
                  ],
                ),
              ),
            ),
            Container(
              decoration: const BoxDecoration(
                border: Border(top: BorderSide(color: AppColors.border)),
              ),
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
              child: result != null
                  ? FilledButton(
                      style: _filled,
                      onPressed: _close,
                      child: const Text('Done'),
                    )
                  : Row(
                      children: [
                        Expanded(
                          child: OutlinedButton(
                            style: _outlined,
                            // A preview being redone can be walked away
                            // from; the import itself cannot.
                            onPressed:
                                state.committing ||
                                    (state.busy && preview == null)
                                ? null
                                : preview == null
                                ? _close
                                : _notifier.reset,
                            child: Text(preview == null ? 'Cancel' : 'Back'),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: preview == null
                              ? FilledButton.icon(
                                  style: _filled,
                                  onPressed: state.busy ? null : _choose,
                                  icon: Icon(
                                    mapping
                                        ? LucideIcons.fileSpreadsheet
                                        : LucideIcons.fileText,
                                    size: 18,
                                  ),
                                  label: Text(
                                    mapping
                                        ? 'Choose a spreadsheet'
                                        : 'Choose CSV file',
                                    textAlign: TextAlign.center,
                                  ),
                                )
                              : FilledButton(
                                  style: _filled,
                                  onPressed: state.canCommit ? _commit : null,
                                  child: Text(
                                    'Import ${preview.valid} '
                                    '${_target.noun(preview.valid)}',
                                    textAlign: TextAlign.center,
                                  ),
                                ),
                        ),
                      ],
                    ),
            ),
          ],
        ),
      ),
    );
  }

  static final ButtonStyle _filled = FilledButton.styleFrom(
    minimumSize: const Size.fromHeight(AppLayout.buttonHeightLarge),
    shape: RoundedRectangleBorder(borderRadius: AppLayout.borderRadiusMd),
  );

  static final ButtonStyle _outlined = OutlinedButton.styleFrom(
    minimumSize: const Size.fromHeight(AppLayout.buttonHeightLarge),
  );
}

final ButtonStyle _textButton = TextButton.styleFrom(
  minimumSize: const Size(0, AppLayout.buttonHeightLarge),
  padding: EdgeInsets.zero,
);

String _rows(int n) => '$n ${n == 1 ? 'row' : 'rows'}';

class _FileLine extends StatelessWidget {
  const _FileLine({required this.file});

  final CsvImportFile file;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        const Icon(
          LucideIcons.fileText,
          size: 18,
          color: AppColors.textSecondary,
        ),
        const SizedBox(width: 8),
        Expanded(
          child: Text(
            file.name,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: AppTypography.body.copyWith(fontWeight: FontWeight.w500),
          ),
        ),
        const SizedBox(width: 8),
        Text(
          '${(file.bytes.length / 1024).toStringAsFixed(1)} KB',
          style: AppTypography.caption.copyWith(color: AppColors.textSecondary),
        ),
      ],
    );
  }
}

/// What the web's import shows before a file is chosen: any columns work,
/// what files are taken, and the template for someone starting from scratch.
class _SpreadsheetHelp extends StatelessWidget {
  const _SpreadsheetHelp({required this.onSaveTemplate, required this.note});

  final VoidCallback onSaveTemplate;
  final String? note;

  @override
  Widget build(BuildContext context) {
    final secondary = AppTypography.bodySmall.copyWith(
      color: AppColors.textSecondary,
    );
    return _HelpBox(
      children: [
        Text(
          "Any column names work. You'll check how they match before "
          'anything is imported.',
          style: AppTypography.bodySmall,
        ),
        const SizedBox(height: 4),
        Text('.xlsx or .csv, up to 5 MB.', style: secondary),
        const SizedBox(height: 8),
        Text('Starting from scratch?', style: secondary),
        TextButton.icon(
          style: _textButton,
          onPressed: onSaveTemplate,
          icon: const Icon(LucideIcons.download, size: 16),
          label: const Text('Save CSV template'),
        ),
        if (note != null) Text(note!, style: secondary),
      ],
    );
  }
}

/// The ticket drawer's "CSV format" box: what the columns are, and the
/// template.
class _FormatHelp extends StatelessWidget {
  const _FormatHelp({
    required this.target,
    required this.onSaveTemplate,
    required this.note,
  });

  final CsvImportTarget target;
  final VoidCallback onSaveTemplate;
  final String? note;

  @override
  Widget build(BuildContext context) {
    final secondary = AppTypography.bodySmall.copyWith(
      color: AppColors.textSecondary,
    );
    return _HelpBox(
      children: [
        Text(
          'CSV format',
          style: AppTypography.label.copyWith(fontWeight: FontWeight.w600),
        ),
        const SizedBox(height: 4),
        Text(
          'Required headers: ${target.requiredHeaders.join(', ')}. '
          'Optional: ${target.optionalHelp ?? ''}',
          style: secondary,
        ),
        Text('.csv only, up to 5 MB.', style: secondary),
        const SizedBox(height: 4),
        TextButton.icon(
          style: _textButton,
          onPressed: onSaveTemplate,
          icon: const Icon(LucideIcons.download, size: 16),
          label: const Text('Save CSV template'),
        ),
        if (note != null) Text(note!, style: secondary),
      ],
    );
  }
}

class _HelpBox extends StatelessWidget {
  const _HelpBox({required this.children});

  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.surfaceDim,
        border: Border.all(color: AppColors.border),
        borderRadius: AppLayout.borderRadiusMd,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: children,
      ),
    );
  }
}

/// The web `ImportFlow`'s matching step on a phone: one card per column with
/// its header, a few of its values and the field it goes to, then what
/// importing will do. The web lays the same columns out as cards below 768px.
class _MatchStep extends StatelessWidget {
  const _MatchStep({
    required this.target,
    required this.state,
    required this.showEmpty,
    required this.onToggleEmpty,
    required this.onChange,
    required this.onSaveSkipped,
    required this.saveNote,
    required this.onUseLeads,
  });

  /// As many skipped rows as the web lists; the rest are in the saved file.
  static const int skippedShown = 50;

  final CsvImportTarget target;
  final CsvImportState state;
  final bool showEmpty;
  final VoidCallback onToggleEmpty;
  final void Function(int index, String? field) onChange;
  final VoidCallback onSaveSkipped;
  final String? saveNote;
  final VoidCallback? onUseLeads;

  @override
  Widget build(BuildContext context) {
    final preview = state.preview!;
    final columns = state.columns;
    // A column with no value in any row cannot import anything. Exports such
    // as Outlook's carry dozens of them, so they wait behind a toggle.
    final shown = showEmpty
        ? columns
        : columns
              .where((c) => c.field != null || c.samples.isNotEmpty)
              .toList();
    final hidden = columns.length - shown.length;
    final skipped = state.skipped;
    final secondary = AppTypography.bodySmall.copyWith(
      color: AppColors.textSecondary,
    );

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (!csvHasAnyMatch(columns)) ...[
          const _Note(child: Text(csvImportNoMatchHint)),
          const SizedBox(height: 12),
        ],
        for (final column in shown) ...[
          _ColumnCard(
            key: ValueKey(column.index),
            column: column,
            fields: state.fields,
            onChanged: state.committing
                ? null
                : (field) => onChange(column.index, field),
          ),
          const SizedBox(height: 8),
        ],
        if (hidden > 0 || showEmpty)
          Align(
            alignment: AlignmentDirectional.centerStart,
            child: TextButton(
              style: _textButton,
              onPressed: onToggleEmpty,
              child: Text(
                showEmpty
                    ? 'Hide the empty columns'
                    : 'Show $hidden empty column${hidden == 1 ? '' : 's'}',
              ),
            ),
          ),
        const SizedBox(height: 4),
        // Not after a failed re-preview: nothing is updating then, and the
        // error below offers Try again instead.
        if ((state.busy && !state.committing) ||
            (state.stale && state.error == null)) ...[
          Row(
            children: [
              const SizedBox.square(
                dimension: 12,
                child: CircularProgressIndicator(strokeWidth: 2),
              ),
              const SizedBox(width: 8),
              Expanded(child: Text('Updating the preview', style: secondary)),
            ],
          ),
          const SizedBox(height: 8),
        ],
        for (final line in csvDroppedLines(state.dropped, state.fields)) ...[
          Text(line, style: secondary),
          const SizedBox(height: 4),
        ],
        if (skipped.isNotEmpty) ...[
          const SizedBox(height: 4),
          _SkippedList(rows: skipped.take(skippedShown).toList()),
          if (skipped.length > skippedShown) ...[
            const SizedBox(height: 4),
            Text(
              '${_rows(skipped.length - skippedShown)} more are in the '
              'download.',
              style: secondary,
            ),
          ],
          Align(
            alignment: AlignmentDirectional.centerStart,
            child: TextButton.icon(
              style: _textButton,
              onPressed: onSaveSkipped,
              icon: const Icon(LucideIcons.download, size: 16),
              label: const Text('Save skipped rows'),
            ),
          ),
          if (saveNote != null) Text(saveNote!, style: secondary),
        ],
        if (csvSuggestLeads(target, skipped)) ...[
          const SizedBox(height: 8),
          _Note(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Some rows were skipped for a missing first or last name. '
                  'A lead needs only one of the two, so this file could go in '
                  'as leads instead.',
                ),
                if (onUseLeads != null) ...[
                  const SizedBox(height: 8),
                  OutlinedButton(
                    style: OutlinedButton.styleFrom(
                      minimumSize: const Size(0, AppLayout.buttonHeightLarge),
                    ),
                    onPressed: state.committing ? null : onUseLeads,
                    child: const Text('Import as leads instead'),
                  ),
                ],
              ],
            ),
          ),
        ],
        const SizedBox(height: 12),
        Semantics(
          liveRegion: true,
          child: Text(
            csvImportSummaryLine(target, preview),
            style: AppTypography.body.copyWith(fontWeight: FontWeight.w600),
          ),
        ),
      ],
    );
  }
}

/// The web `ImportFlow`'s done step, as one flat card: how many records were
/// created, a line per field whose values were left blank, and how many rows
/// were skipped, with the button that saves them to fix and upload again. All
/// three are the commit's own account, not the preview's. As on the web only
/// the count of skipped rows is shown; their cells, the file's own text, go
/// into the saved file and nowhere else.
class _DoneStep extends StatelessWidget {
  const _DoneStep({
    required this.target,
    required this.result,
    required this.fields,
    required this.onSaveSkipped,
    required this.saveNote,
  });

  final CsvImportTarget target;
  final CsvImportResult result;

  /// The preview's fields, for the labels of the dropped lines.
  final List<CsvImportField> fields;
  final VoidCallback onSaveSkipped;
  final String? saveNote;

  @override
  Widget build(BuildContext context) {
    final created = result.created;
    final skipped = result.skipped.length;
    final secondary = AppTypography.bodySmall.copyWith(
      color: AppColors.textSecondary,
    );
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.surface,
        border: Border.all(color: AppColors.border),
        borderRadius: AppLayout.borderRadiusMd,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Semantics(
            liveRegion: true,
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Icon(
                  LucideIcons.circleCheck,
                  size: 20,
                  color: AppColors.success700,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Imported $created ${target.noun(created)}.',
                    style: AppTypography.body.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ],
            ),
          ),
          for (final line in csvDroppedLines(result.dropped, fields)) ...[
            const SizedBox(height: 8),
            Text(line, style: secondary),
          ],
          if (skipped > 0) ...[
            const SizedBox(height: 8),
            Text('${_rows(skipped)} skipped.', style: secondary),
            TextButton.icon(
              style: _textButton,
              onPressed: onSaveSkipped,
              icon: const Icon(LucideIcons.download, size: 16),
              label: const Text('Save skipped rows'),
            ),
            if (saveNote != null) Text(saveNote!, style: secondary),
          ],
        ],
      ),
    );
  }
}

class _ColumnCard extends StatelessWidget {
  const _ColumnCard({
    super.key,
    required this.column,
    required this.fields,
    required this.onChanged,
  });

  final CsvImportColumn column;
  final List<CsvImportField> fields;

  /// Null while the import runs, which locks the picker.
  final ValueChanged<String?>? onChanged;

  @override
  Widget build(BuildContext context) {
    final name = column.header.isEmpty
        ? 'Column ${column.index + 1}'
        : column.header;
    // The server matches only to fields it lists; anything else would leave
    // the menu with no item for its value.
    final value = fields.any((f) => f.name == column.field)
        ? column.field
        : null;
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.surface,
        border: Border.all(color: AppColors.border),
        borderRadius: AppLayout.borderRadiusMd,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            name,
            style: AppTypography.body.copyWith(fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 2),
          Text(
            column.samples.isEmpty
                ? 'No values'
                : column.samples.join(' \u00b7 '),
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: AppTypography.bodySmall.copyWith(
              color: column.samples.isEmpty
                  ? AppColors.textTertiary
                  : AppColors.textSecondary,
            ),
          ),
          const SizedBox(height: 8),
          Semantics(
            label: 'Import $name as',
            child: DropdownButtonFormField<String>(
              initialValue: value,
              isExpanded: true,
              decoration: const InputDecoration(
                labelText: 'Import as',
                border: OutlineInputBorder(),
                contentPadding: EdgeInsets.symmetric(
                  horizontal: 12,
                  vertical: 12,
                ),
              ),
              items: [
                const DropdownMenuItem<String>(
                  value: null,
                  child: Text("Don't import"),
                ),
                for (final f in fields)
                  DropdownMenuItem<String>(
                    value: f.name,
                    child: Text(f.label, overflow: TextOverflow.ellipsis),
                  ),
              ],
              onChanged: onChanged,
            ),
          ),
        ],
      ),
    );
  }
}

/// Row number and reason, in a box that scrolls on its own so a long list
/// does not push the buttons off the sheet. The rows' cells are not shown:
/// they go only into the saved file.
class _SkippedList extends StatelessWidget {
  const _SkippedList({required this.rows});

  final List<CsvSkippedRow> rows;

  @override
  Widget build(BuildContext context) {
    return Container(
      constraints: const BoxConstraints(maxHeight: 192),
      decoration: BoxDecoration(
        border: Border.all(color: AppColors.border),
        borderRadius: AppLayout.borderRadiusMd,
      ),
      child: ListView.separated(
        shrinkWrap: true,
        padding: EdgeInsets.zero,
        itemCount: rows.length,
        separatorBuilder: (_, _) =>
            const Divider(height: 1, color: AppColors.border),
        itemBuilder: (_, i) => Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          child: Text.rich(
            TextSpan(
              children: [
                TextSpan(
                  text: 'Row ${rows[i].row}  ',
                  style: const TextStyle(color: AppColors.textSecondary),
                ),
                TextSpan(text: rows[i].message),
              ],
            ),
            style: AppTypography.bodySmall,
          ),
        ),
      ),
    );
  }
}

class _Note extends StatelessWidget {
  const _Note({required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.accent50,
        border: Border.all(color: AppColors.border),
        borderRadius: AppLayout.borderRadiusMd,
      ),
      child: DefaultTextStyle.merge(
        style: AppTypography.bodySmall.copyWith(color: AppColors.textPrimary),
        child: child,
      ),
    );
  }
}

class _PreviewSummary extends StatelessWidget {
  const _PreviewSummary({
    required this.target,
    required this.preview,
    required this.onSaveErrors,
    required this.errorsNote,
  });

  final CsvImportTarget target;
  final CsvImportPreview preview;
  final void Function(List<CsvRowError> errors) onSaveErrors;
  final String? errorsNote;

  @override
  Widget build(BuildContext context) {
    final headerError = preview.headerError;
    final errors = preview.errors;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (headerError != null)
          _Alert(message: headerError)
        else ...[
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              _Count(label: 'Total: ${preview.total}'),
              _Count(
                label: 'Valid: ${preview.valid}',
                color: AppColors.success700,
                background: AppColors.success50,
                icon: LucideIcons.circleCheck,
              ),
              if (preview.invalid > 0)
                _Count(
                  label: 'Invalid: ${preview.invalid}',
                  color: AppColors.danger700,
                  background: AppColors.danger50,
                  icon: LucideIcons.circleAlert,
                ),
            ],
          ),
          if (preview.validRows.isNotEmpty) ...[
            const SizedBox(height: 12),
            _ValidSample(target: target, rows: preview.validRows),
          ],
          if (errors.isNotEmpty) ...[
            const SizedBox(height: 12),
            _RowErrors(
              heading:
                  '${errors.length} error${errors.length == 1 ? '' : 's'}, '
                  'fix the CSV before importing',
              errors: errors,
              onSave: onSaveErrors,
              note: errorsNote,
            ),
          ] else if (preview.valid == 0) ...[
            const SizedBox(height: 12),
            Text(
              'No ${target.plural} to import in this file.',
              style: AppTypography.bodySmall.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
          ],
        ],
      ],
    );
  }
}

class _Count extends StatelessWidget {
  const _Count({
    required this.label,
    this.color = AppColors.textPrimary,
    this.background = AppColors.gray100,
    this.icon,
  });

  final String label;
  final Color color;
  final Color background;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: background,
        borderRadius: AppLayout.borderRadiusFull,
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (icon != null) ...[
            Icon(icon, size: 14, color: color),
            const SizedBox(width: 4),
          ],
          Text(label, style: AppTypography.labelSmall.copyWith(color: color)),
        ],
      ),
    );
  }
}

/// Row number, column and problem, in a box that scrolls on its own so a file
/// with hundreds of bad rows does not push the buttons off the screen.
class _RowErrors extends StatelessWidget {
  const _RowErrors({
    required this.heading,
    required this.errors,
    required this.onSave,
    required this.note,
  });

  final String heading;
  final List<CsvRowError> errors;
  final void Function(List<CsvRowError> errors) onSave;

  /// What the last save said, if anything.
  final String? note;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          heading,
          style: AppTypography.bodySmall.copyWith(
            color: AppColors.danger800,
            fontWeight: FontWeight.w600,
          ),
        ),
        Align(
          alignment: AlignmentDirectional.centerStart,
          child: TextButton.icon(
            style: _textButton,
            onPressed: () => onSave(errors),
            icon: const Icon(LucideIcons.download, size: 16),
            label: const Text('Save errors as CSV'),
          ),
        ),
        if (note != null) ...[
          Text(
            note!,
            style: AppTypography.bodySmall.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
          const SizedBox(height: 4),
        ],
        const SizedBox(height: 4),
        Container(
          constraints: const BoxConstraints(maxHeight: 240),
          decoration: BoxDecoration(
            color: AppColors.danger50,
            border: Border.all(color: AppColors.danger200),
            borderRadius: AppLayout.borderRadiusMd,
          ),
          child: ListView.separated(
            shrinkWrap: true,
            padding: EdgeInsets.zero,
            itemCount: errors.length,
            separatorBuilder: (_, _) =>
                const Divider(height: 1, color: AppColors.danger200),
            itemBuilder: (_, i) {
              final e = errors[i];
              return Padding(
                padding: const EdgeInsets.symmetric(
                  horizontal: 12,
                  vertical: 8,
                ),
                child: Text.rich(
                  TextSpan(
                    children: [
                      TextSpan(
                        text: 'Row ${e.row}',
                        style: const TextStyle(fontWeight: FontWeight.w600),
                      ),
                      if (e.field.isNotEmpty) TextSpan(text: ' · ${e.field}'),
                      TextSpan(text: '\n${e.message}'),
                    ],
                  ),
                  style: AppTypography.bodySmall.copyWith(
                    color: AppColors.danger900,
                  ),
                ),
              );
            },
          ),
        ),
      ],
    );
  }
}

/// The web drawer's sample of the rows that would import: the first 20, in a
/// box that scrolls on its own, one line of name and one of the other columns
/// the web table prints, since five columns do not fit a phone.
class _ValidSample extends StatelessWidget {
  const _ValidSample({required this.target, required this.rows});

  static const int shown = 20;

  final CsvImportTarget target;
  final List<Map<String, dynamic>> rows;

  @override
  Widget build(BuildContext context) {
    final sample = rows.take(shown).toList(growable: false);
    final secondary = AppTypography.bodySmall.copyWith(
      color: AppColors.textSecondary,
    );
    return Container(
      constraints: const BoxConstraints(maxHeight: 192),
      decoration: BoxDecoration(
        border: Border.all(color: AppColors.border),
        borderRadius: AppLayout.borderRadiusMd,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Flexible(
            child: ListView.separated(
              shrinkWrap: true,
              padding: EdgeInsets.zero,
              itemCount: sample.length,
              separatorBuilder: (_, _) =>
                  const Divider(height: 1, color: AppColors.border),
              itemBuilder: (_, i) {
                final row = sample[i];
                final line = target.sampleLine(row);
                return Padding(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 12,
                    vertical: 8,
                  ),
                  child: Text.rich(
                    TextSpan(
                      children: [
                        TextSpan(
                          text: 'Row ${row['row'] ?? i + 1}',
                          style: const TextStyle(
                            color: AppColors.textSecondary,
                          ),
                        ),
                        TextSpan(
                          text: '  ${line.title}',
                          style: const TextStyle(fontWeight: FontWeight.w600),
                        ),
                        if (line.details.isNotEmpty)
                          TextSpan(text: '\n${line.details}', style: secondary),
                      ],
                    ),
                    style: AppTypography.bodySmall,
                  ),
                );
              },
            ),
          ),
          if (rows.length > shown)
            Container(
              color: AppColors.surfaceDim,
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              child: Text(
                'Showing first $shown of ${rows.length} valid rows',
                textAlign: TextAlign.center,
                style: AppTypography.caption.copyWith(
                  color: AppColors.textSecondary,
                ),
              ),
            ),
        ],
      ),
    );
  }
}

class _Alert extends StatelessWidget {
  const _Alert({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.danger50,
        border: Border.all(color: AppColors.danger200),
        borderRadius: AppLayout.borderRadiusMd,
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(
            LucideIcons.circleAlert,
            size: 16,
            color: AppColors.danger700,
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              message,
              style: AppTypography.bodySmall.copyWith(
                color: AppColors.danger800,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
