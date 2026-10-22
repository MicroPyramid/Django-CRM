import 'package:flutter/material.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';

import '../../core/theme/theme.dart';

/// One dropdown option being edited.
///
/// [value] is what records store. It is empty for a row added in this sheet
/// and is left exactly as it was for a row that came back from the server,
/// because relabelling an option must not move the records that hold it.
class OptionDraft {
  OptionDraft({required this.value, required String label})
    : controller = TextEditingController(text: label);

  final String value;
  final TextEditingController controller;
}

class OptionsEditor extends StatelessWidget {
  const OptionsEditor({
    super.key,
    required this.options,
    required this.onAdd,
    required this.onRemove,
  });

  final List<OptionDraft> options;
  final VoidCallback onAdd;
  final void Function(int index) onRemove;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Options',
          style: AppTypography.body.copyWith(fontWeight: FontWeight.w600),
        ),
        const SizedBox(height: 4),
        Text(
          'Renaming an option keeps the records that already use it.',
          style: AppTypography.caption.copyWith(color: AppColors.textSecondary),
        ),
        const SizedBox(height: 8),
        for (var i = 0; i < options.length; i++)
          Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: options[i].controller,
                    textCapitalization: TextCapitalization.sentences,
                    decoration: InputDecoration(
                      isDense: true,
                      hintText: 'Option ${i + 1}',
                      border: const OutlineInputBorder(),
                    ),
                  ),
                ),
                IconButton(
                  onPressed: () => onRemove(i),
                  tooltip: 'Remove option',
                  icon: Icon(
                    LucideIcons.x,
                    size: 18,
                    color: AppColors.textSecondary,
                  ),
                ),
              ],
            ),
          ),
        SizedBox(
          height: 44,
          child: OutlinedButton.icon(
            onPressed: onAdd,
            icon: const Icon(LucideIcons.plus, size: 16),
            label: const Text('Add option'),
          ),
        ),
      ],
    );
  }
}
