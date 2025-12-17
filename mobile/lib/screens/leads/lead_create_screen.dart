import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../../core/theme/theme.dart';
import '../../data/models/models.dart';
import '../../data/mock/mock_data.dart';
import '../../widgets/common/common.dart';

/// Lead Create Screen
/// Form for creating a new lead
class LeadCreateScreen extends StatefulWidget {
  const LeadCreateScreen({super.key});

  @override
  State<LeadCreateScreen> createState() => _LeadCreateScreenState();
}

class _LeadCreateScreenState extends State<LeadCreateScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _companyController = TextEditingController();
  final _emailController = TextEditingController();
  final _phoneController = TextEditingController();
  final _notesController = TextEditingController();

  LeadStatus _status = LeadStatus.newLead;
  LeadSource _source = LeadSource.website;
  Priority _priority = Priority.medium;
  String _assignedTo = MockData.currentUser.id;
  final List<String> _tags = [];
  bool _showAdvanced = false;
  bool _isLoading = false;

  final _tagController = TextEditingController();

  @override
  void dispose() {
    _nameController.dispose();
    _companyController.dispose();
    _emailController.dispose();
    _phoneController.dispose();
    _notesController.dispose();
    _tagController.dispose();
    super.dispose();
  }

  bool get _hasUnsavedChanges {
    return _nameController.text.isNotEmpty ||
        _companyController.text.isNotEmpty ||
        _emailController.text.isNotEmpty ||
        _phoneController.text.isNotEmpty ||
        _notesController.text.isNotEmpty ||
        _tags.isNotEmpty;
  }

  Future<bool> _onWillPop() async {
    if (!_hasUnsavedChanges) return true;

    final result = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Discard changes?'),
        content: const Text(
          'You have unsaved changes. Are you sure you want to leave?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: Text(
              'Discard',
              style: TextStyle(color: AppColors.danger600),
            ),
          ),
        ],
      ),
    );

    return result ?? false;
  }

  Future<void> _handleSubmit() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);

    // Simulate API call
    await Future.delayed(const Duration(milliseconds: 1500));

    if (mounted) {
      setState(() => _isLoading = false);

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Lead created successfully'),
          behavior: SnackBarBehavior.floating,
        ),
      );

      context.pop();
    }
  }

  void _addTag(String tag) {
    final trimmedTag = tag.trim();
    if (trimmedTag.isNotEmpty && !_tags.contains(trimmedTag)) {
      setState(() {
        _tags.add(trimmedTag);
        _tagController.clear();
      });
    }
  }

  void _removeTag(String tag) {
    setState(() {
      _tags.remove(tag);
    });
  }

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: !_hasUnsavedChanges,
      onPopInvokedWithResult: (didPop, result) async {
        if (didPop) return;
        final shouldPop = await _onWillPop();
        if (shouldPop && context.mounted) {
          context.pop();
        }
      },
      child: Scaffold(
        backgroundColor: AppColors.surface,
        appBar: AppBar(
          title: const Text('New Lead'),
          backgroundColor: AppColors.surface,
          elevation: 0,
          scrolledUnderElevation: 1,
          leading: IconButton(
            icon: const Icon(LucideIcons.chevronLeft),
            onPressed: () async {
              if (_hasUnsavedChanges) {
                final shouldPop = await _onWillPop();
                if (shouldPop && context.mounted) {
                  context.pop();
                }
              } else {
                context.pop();
              }
            },
          ),
        ),
        body: Form(
          key: _formKey,
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Basic Information Section
                _buildSectionTitle('Basic Information'),
                const SizedBox(height: 16),
                _buildBasicFields(),

                const SizedBox(height: 32),

                // Classification Section
                _buildSectionTitle('Classification'),
                const SizedBox(height: 16),
                _buildClassificationFields(),

                const SizedBox(height: 32),

                // Assignment Section
                _buildSectionTitle('Assignment'),
                const SizedBox(height: 16),
                _buildAssignmentField(),

                const SizedBox(height: 24),

                // Advanced Section (Collapsible)
                _buildAdvancedSection(),

                const SizedBox(height: 32),

                // Submit Button
                PrimaryButton(
                  label: 'Create Lead',
                  onPressed: _isLoading ? null : _handleSubmit,
                  isLoading: _isLoading,
                ),

                const SizedBox(height: 16),

                // Cancel Button
                Center(
                  child: GestureDetector(
                    onTap: () async {
                      if (_hasUnsavedChanges) {
                        final shouldPop = await _onWillPop();
                        if (shouldPop && context.mounted) {
                          context.pop();
                        }
                      } else {
                        context.pop();
                      }
                    },
                    child: Text(
                      'Cancel',
                      style: AppTypography.label.copyWith(
                        color: AppColors.textSecondary,
                      ),
                    ),
                  ),
                ),

                const SizedBox(height: 48),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Text(
      title.toUpperCase(),
      style: AppTypography.overline.copyWith(
        color: AppColors.textSecondary,
        letterSpacing: 1.2,
      ),
    );
  }

  Widget _buildBasicFields() {
    return Column(
      children: [
        // Full Name
        FloatingLabelInput(
          label: 'Full Name',
          hint: 'John Doe',
          controller: _nameController,
          prefixIcon: LucideIcons.user,
          textInputAction: TextInputAction.next,
          validator: (value) {
            if (value == null || value.isEmpty) {
              return 'Name is required';
            }
            if (value.length < 2) {
              return 'Name must be at least 2 characters';
            }
            return null;
          },
        ),

        const SizedBox(height: 16),

        // Company
        FloatingLabelInput(
          label: 'Company',
          hint: 'Acme Inc.',
          controller: _companyController,
          prefixIcon: LucideIcons.building2,
          textInputAction: TextInputAction.next,
          validator: (value) {
            if (value == null || value.isEmpty) {
              return 'Company is required';
            }
            return null;
          },
        ),

        const SizedBox(height: 16),

        // Email
        FloatingLabelInput(
          label: 'Email',
          hint: 'john@acme.com',
          controller: _emailController,
          prefixIcon: LucideIcons.mail,
          keyboardType: TextInputType.emailAddress,
          textInputAction: TextInputAction.next,
          validator: (value) {
            if (value == null || value.isEmpty) {
              return 'Email is required';
            }
            if (!value.contains('@') || !value.contains('.')) {
              return 'Please enter a valid email';
            }
            return null;
          },
        ),

        const SizedBox(height: 16),

        // Phone
        FloatingLabelInput(
          label: 'Phone (Optional)',
          hint: '+1 (555) 123-4567',
          controller: _phoneController,
          prefixIcon: LucideIcons.phone,
          keyboardType: TextInputType.phone,
          textInputAction: TextInputAction.next,
        ),
      ],
    );
  }

  Widget _buildClassificationFields() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Status Dropdown
        _buildDropdownField(
          label: 'Status',
          value: _status.displayName,
          onTap: () => _showStatusPicker(),
        ),

        const SizedBox(height: 16),

        // Source Dropdown
        _buildDropdownField(
          label: 'Source',
          value: _source.displayName,
          onTap: () => _showSourcePicker(),
        ),

        const SizedBox(height: 16),

        // Priority Selector
        Text(
          'Priority',
          style: AppTypography.caption.copyWith(
            color: AppColors.textSecondary,
          ),
        ),
        const SizedBox(height: 8),
        _buildPrioritySelector(),
      ],
    );
  }

  Widget _buildDropdownField({
    required String label,
    required String value,
    required VoidCallback onTap,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: AppTypography.caption.copyWith(
            color: AppColors.textSecondary,
          ),
        ),
        const SizedBox(height: 8),
        GestureDetector(
          onTap: onTap,
          child: Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
            decoration: BoxDecoration(
              color: AppColors.gray50,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppColors.border),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  value,
                  style: AppTypography.body,
                ),
                Icon(
                  LucideIcons.chevronDown,
                  size: 20,
                  color: AppColors.textSecondary,
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildPrioritySelector() {
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border),
      ),
      child: Row(
        children: Priority.values.map((priority) {
          final isSelected = _priority == priority;
          final isFirst = priority == Priority.values.first;
          final isLast = priority == Priority.values.last;

          return Expanded(
            child: GestureDetector(
              onTap: () => setState(() => _priority = priority),
              child: AnimatedContainer(
                duration: AppDurations.fast,
                padding: const EdgeInsets.symmetric(vertical: 14),
                decoration: BoxDecoration(
                  color: isSelected
                      ? _getPriorityColor(priority)
                      : AppColors.surface,
                  borderRadius: BorderRadius.horizontal(
                    left: isFirst ? const Radius.circular(11) : Radius.zero,
                    right: isLast ? const Radius.circular(11) : Radius.zero,
                  ),
                ),
                child: Text(
                  priority.displayName,
                  textAlign: TextAlign.center,
                  style: AppTypography.label.copyWith(
                    color: isSelected ? Colors.white : AppColors.textSecondary,
                    fontWeight: isSelected ? FontWeight.w600 : FontWeight.w500,
                  ),
                ),
              ),
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget _buildAssignmentField() {
    final selectedUser = MockData.getUserById(_assignedTo);

    return GestureDetector(
      onTap: () => _showUserPicker(),
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppColors.gray50,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppColors.border),
        ),
        child: Row(
          children: [
            UserAvatar(
              name: selectedUser?.name ?? 'Unknown',
              imageUrl: selectedUser?.avatar,
              size: AvatarSize.md,
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    selectedUser?.name ?? 'Select team member',
                    style: AppTypography.label,
                  ),
                  if (selectedUser != null)
                    Text(
                      selectedUser.role,
                      style: AppTypography.caption.copyWith(
                        color: AppColors.textSecondary,
                      ),
                    ),
                ],
              ),
            ),
            Icon(
              LucideIcons.chevronDown,
              size: 20,
              color: AppColors.textSecondary,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAdvancedSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Toggle Header
        GestureDetector(
          onTap: () => setState(() => _showAdvanced = !_showAdvanced),
          child: Row(
            children: [
              AnimatedRotation(
                turns: _showAdvanced ? 0.25 : 0,
                duration: AppDurations.fast,
                child: Icon(
                  LucideIcons.chevronRight,
                  size: 20,
                  color: AppColors.textSecondary,
                ),
              ),
              const SizedBox(width: 8),
              Text(
                'Advanced Options',
                style: AppTypography.label.copyWith(
                  color: AppColors.textSecondary,
                ),
              ),
            ],
          ),
        ),

        // Expanded Content
        AnimatedCrossFade(
          firstChild: const SizedBox.shrink(),
          secondChild: Padding(
            padding: const EdgeInsets.only(top: 16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Tags
                Text(
                  'Tags',
                  style: AppTypography.caption.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
                const SizedBox(height: 8),
                _buildTagInput(),

                const SizedBox(height: 16),

                // Notes
                TextAreaField(
                  label: 'Notes',
                  hint: 'Add any additional notes about this lead...',
                  controller: _notesController,
                  maxLines: 4,
                ),
              ],
            ),
          ),
          crossFadeState: _showAdvanced
              ? CrossFadeState.showSecond
              : CrossFadeState.showFirst,
          duration: AppDurations.normal,
        ),
      ],
    );
  }

  Widget _buildTagInput() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Tag chips
        if (_tags.isNotEmpty) ...[
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: _tags
                .map((tag) => Chip(
                      label: Text(tag),
                      deleteIcon: const Icon(LucideIcons.x, size: 14),
                      onDeleted: () => _removeTag(tag),
                      backgroundColor: AppColors.primary100,
                      labelStyle: AppTypography.caption.copyWith(
                        color: AppColors.primary700,
                      ),
                      deleteIconColor: AppColors.primary600,
                      side: BorderSide.none,
                      padding: const EdgeInsets.symmetric(horizontal: 4),
                    ))
                .toList(),
          ),
          const SizedBox(height: 12),
        ],

        // Tag input
        TextField(
          controller: _tagController,
          decoration: InputDecoration(
            hintText: 'Add tag and press enter...',
            hintStyle: AppTypography.body.copyWith(
              color: AppColors.textTertiary,
            ),
            filled: true,
            fillColor: AppColors.gray50,
            contentPadding: const EdgeInsets.symmetric(
              horizontal: 16,
              vertical: 14,
            ),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: AppColors.border),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: AppColors.border),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: AppColors.primary500, width: 1.5),
            ),
            suffixIcon: IconButton(
              icon: Icon(
                LucideIcons.plus,
                size: 20,
                color: AppColors.textSecondary,
              ),
              onPressed: () => _addTag(_tagController.text),
            ),
          ),
          onSubmitted: _addTag,
        ),

        // Suggested tags
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          children: ['Enterprise', 'SMB', 'Startup', 'Priority']
              .where((tag) => !_tags.contains(tag))
              .take(3)
              .map((tag) => GestureDetector(
                    onTap: () => _addTag(tag),
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 10,
                        vertical: 6,
                      ),
                      decoration: BoxDecoration(
                        color: AppColors.gray100,
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            LucideIcons.plus,
                            size: 12,
                            color: AppColors.textSecondary,
                          ),
                          const SizedBox(width: 4),
                          Text(
                            tag,
                            style: AppTypography.caption.copyWith(
                              color: AppColors.textSecondary,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ))
              .toList(),
        ),
      ],
    );
  }

  void _showStatusPicker() {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => _PickerBottomSheet(
        title: 'Select Status',
        options: LeadStatus.values
            .map((status) => _PickerOption(
                  label: status.displayName,
                  isSelected: _status == status,
                  color: _getStatusColorForPicker(status),
                  onTap: () {
                    setState(() => _status = status);
                    Navigator.pop(context);
                  },
                ))
            .toList(),
      ),
    );
  }

  void _showSourcePicker() {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => _PickerBottomSheet(
        title: 'Select Source',
        options: LeadSource.values
            .map((source) => _PickerOption(
                  label: source.displayName,
                  isSelected: _source == source,
                  icon: _getSourceIcon(source),
                  onTap: () {
                    setState(() => _source = source);
                    Navigator.pop(context);
                  },
                ))
            .toList(),
      ),
    );
  }

  void _showUserPicker() {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      isScrollControlled: true,
      constraints: BoxConstraints(
        maxHeight: MediaQuery.of(context).size.height * 0.6,
      ),
      builder: (context) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              margin: const EdgeInsets.only(top: 12),
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: AppColors.gray300,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(16),
              child: Text('Assign to', style: AppTypography.h3),
            ),
            Flexible(
              child: ListView(
                shrinkWrap: true,
                children: MockData.users.map((user) => ListTile(
                      leading: UserAvatar(
                        name: user.name,
                        imageUrl: user.avatar,
                        size: AvatarSize.sm,
                      ),
                      title: Text(user.name),
                      subtitle: Text(user.role),
                      trailing: _assignedTo == user.id
                          ? Icon(LucideIcons.check, color: AppColors.primary600)
                          : null,
                      onTap: () {
                        setState(() => _assignedTo = user.id);
                        Navigator.pop(context);
                      },
                    )).toList(),
              ),
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }

  Color _getPriorityColor(Priority priority) {
    // Use the color defined in the enum
    return priority.color;
  }

  Color _getStatusColorForPicker(LeadStatus status) {
    // Use the color defined in the enum
    return status.color;
  }

  IconData _getSourceIcon(LeadSource source) {
    // Use the icon defined in the enum
    return source.icon;
  }
}

/// Picker bottom sheet
class _PickerBottomSheet extends StatelessWidget {
  final String title;
  final List<_PickerOption> options;

  const _PickerBottomSheet({
    required this.title,
    required this.options,
  });

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            margin: const EdgeInsets.only(top: 12),
            width: 40,
            height: 4,
            decoration: BoxDecoration(
              color: AppColors.gray300,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: Text(title, style: AppTypography.h3),
          ),
          ...options,
          const SizedBox(height: 16),
        ],
      ),
    );
  }
}

/// Picker option item
class _PickerOption extends StatelessWidget {
  final String label;
  final bool isSelected;
  final Color? color;
  final IconData? icon;
  final VoidCallback onTap;

  const _PickerOption({
    required this.label,
    required this.isSelected,
    this.color,
    this.icon,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        child: Row(
          children: [
            if (color != null) ...[
              Container(
                width: 12,
                height: 12,
                decoration: BoxDecoration(
                  color: color,
                  shape: BoxShape.circle,
                ),
              ),
              const SizedBox(width: 12),
            ],
            if (icon != null) ...[
              Icon(
                icon,
                size: 20,
                color: AppColors.textSecondary,
              ),
              const SizedBox(width: 12),
            ],
            Expanded(
              child: Text(
                label,
                style: AppTypography.body.copyWith(
                  fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
                  color: isSelected
                      ? AppColors.primary600
                      : AppColors.textPrimary,
                ),
              ),
            ),
            if (isSelected)
              Icon(
                LucideIcons.check,
                size: 20,
                color: AppColors.primary600,
              ),
          ],
        ),
      ),
    );
  }
}
