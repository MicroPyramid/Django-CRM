import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../../core/theme/theme.dart';
import '../../data/models/models.dart';
import '../../providers/leads_provider.dart';
import '../../widgets/common/common.dart';

/// Lead Form Screen - Reusable for both Create and Edit
class LeadFormScreen extends ConsumerStatefulWidget {
  final String? leadId;
  final Lead? initialLead;

  const LeadFormScreen({
    super.key,
    this.leadId,
    this.initialLead,
  });

  bool get isEditMode => leadId != null;

  @override
  ConsumerState<LeadFormScreen> createState() => _LeadFormScreenState();
}

class _LeadFormScreenState extends ConsumerState<LeadFormScreen> {
  final _formKey = GlobalKey<FormState>();
  final _firstNameController = TextEditingController();
  final _lastNameController = TextEditingController();
  final _companyController = TextEditingController();
  final _emailController = TextEditingController();
  final _phoneController = TextEditingController();
  final _notesController = TextEditingController();

  LeadStatus _status = LeadStatus.assigned;
  LeadSource _source = LeadSource.email;
  LeadRating _rating = LeadRating.cold;
  bool _isLoading = false;
  bool _isFetchingLead = false;
  String? _fetchError;
  Lead? _existingLead;

  @override
  void initState() {
    super.initState();
    if (widget.initialLead != null) {
      _populateFromLead(widget.initialLead!);
    } else if (widget.isEditMode) {
      _fetchLead();
    }
  }

  @override
  void dispose() {
    _firstNameController.dispose();
    _lastNameController.dispose();
    _companyController.dispose();
    _emailController.dispose();
    _phoneController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  Future<void> _fetchLead() async {
    setState(() {
      _isFetchingLead = true;
      _fetchError = null;
    });

    final lead = await ref.read(leadsProvider.notifier).getLeadById(widget.leadId!);

    if (mounted) {
      setState(() {
        _isFetchingLead = false;
        if (lead != null) {
          _existingLead = lead;
          _populateFromLead(lead);
        } else {
          _fetchError = 'Failed to load lead';
        }
      });
    }
  }

  void _populateFromLead(Lead lead) {
    _existingLead = lead;
    _firstNameController.text = lead.firstName;
    _lastNameController.text = lead.lastName;
    _companyController.text = lead.companyName;
    _emailController.text = lead.email;
    _phoneController.text = lead.phone ?? '';
    _notesController.text = lead.description ?? '';
    _status = lead.status;
    _source = lead.source;
    _rating = lead.rating;
  }

  bool get _hasUnsavedChanges {
    if (_existingLead != null) {
      return _firstNameController.text != _existingLead!.firstName ||
          _lastNameController.text != _existingLead!.lastName ||
          _companyController.text != _existingLead!.companyName ||
          _emailController.text != _existingLead!.email ||
          _phoneController.text != (_existingLead!.phone ?? '') ||
          _notesController.text != (_existingLead!.description ?? '') ||
          _status != _existingLead!.status ||
          _source != _existingLead!.source ||
          _rating != _existingLead!.rating;
    }
    return _firstNameController.text.isNotEmpty ||
        _lastNameController.text.isNotEmpty ||
        _companyController.text.isNotEmpty ||
        _emailController.text.isNotEmpty ||
        _phoneController.text.isNotEmpty ||
        _notesController.text.isNotEmpty;
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

  Map<String, dynamic> _buildPayload() {
    return {
      'first_name': _firstNameController.text.trim(),
      'last_name': _lastNameController.text.trim(),
      'email': _emailController.text.trim(),
      'phone': _phoneController.text.trim().isEmpty ? null : _phoneController.text.trim(),
      'company_name': _companyController.text.trim(),
      'status': _status.value,
      'source': _source.value,
      'rating': _rating.value,
      'description': _notesController.text.trim().isEmpty ? null : _notesController.text.trim(),
    };
  }

  Future<void> _handleSubmit() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);

    final payload = _buildPayload();
    final notifier = ref.read(leadsProvider.notifier);

    final response = widget.isEditMode
        ? await notifier.updateLead(widget.leadId!, payload)
        : await notifier.createLead(payload);

    if (mounted) {
      setState(() => _isLoading = false);

      if (response.success) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(widget.isEditMode ? 'Lead updated successfully' : 'Lead created successfully'),
            behavior: SnackBarBehavior.floating,
          ),
        );
        context.pop(true);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(response.message ?? 'Failed to save lead'),
            behavior: SnackBarBehavior.floating,
            backgroundColor: AppColors.danger600,
          ),
        );
      }
    }
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
          title: Text(widget.isEditMode ? 'Edit Lead' : 'New Lead'),
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
        body: _buildBody(),
      ),
    );
  }

  Widget _buildBody() {
    if (_isFetchingLead) {
      return const Center(
        child: CircularProgressIndicator(),
      );
    }

    if (_fetchError != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              LucideIcons.alertCircle,
              size: 48,
              color: AppColors.danger500,
            ),
            const SizedBox(height: 16),
            Text(
              _fetchError!,
              style: AppTypography.body.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
            const SizedBox(height: 16),
            TextButton(
              onPressed: _fetchLead,
              child: const Text('Retry'),
            ),
          ],
        ),
      );
    }

    return Form(
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

            // Notes Section
            _buildSectionTitle('Notes'),
            const SizedBox(height: 16),
            TextAreaField(
              label: 'Description',
              hint: 'Add any additional notes about this lead...',
              controller: _notesController,
              maxLines: 4,
            ),

            const SizedBox(height: 32),

            // Submit Button
            PrimaryButton(
              label: widget.isEditMode ? 'Update Lead' : 'Create Lead',
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
                    if (shouldPop && mounted) {
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
        // First Name
        FloatingLabelInput(
          label: 'First Name',
          hint: 'John',
          controller: _firstNameController,
          prefixIcon: LucideIcons.user,
          textInputAction: TextInputAction.next,
          validator: (value) {
            if (value == null || value.isEmpty) {
              return 'First name is required';
            }
            return null;
          },
        ),

        const SizedBox(height: 16),

        // Last Name
        FloatingLabelInput(
          label: 'Last Name',
          hint: 'Doe',
          controller: _lastNameController,
          prefixIcon: LucideIcons.user,
          textInputAction: TextInputAction.next,
          validator: (value) {
            if (value == null || value.isEmpty) {
              return 'Last name is required';
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
          textInputAction: TextInputAction.done,
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

        // Rating Selector
        Text(
          'Rating',
          style: AppTypography.caption.copyWith(
            color: AppColors.textSecondary,
          ),
        ),
        const SizedBox(height: 8),
        _buildRatingSelector(),
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

  Widget _buildRatingSelector() {
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border),
      ),
      child: Row(
        children: LeadRating.values.map((rating) {
          final isSelected = _rating == rating;
          final isFirst = rating == LeadRating.values.first;
          final isLast = rating == LeadRating.values.last;

          return Expanded(
            child: GestureDetector(
              onTap: () => setState(() => _rating = rating),
              child: AnimatedContainer(
                duration: AppDurations.fast,
                padding: const EdgeInsets.symmetric(vertical: 14),
                decoration: BoxDecoration(
                  color: isSelected ? rating.color : AppColors.surface,
                  borderRadius: BorderRadius.horizontal(
                    left: isFirst ? const Radius.circular(11) : Radius.zero,
                    right: isLast ? const Radius.circular(11) : Radius.zero,
                  ),
                ),
                child: Text(
                  rating.displayName,
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
                  color: status.color,
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
                  icon: source.icon,
                  onTap: () {
                    setState(() => _source = source);
                    Navigator.pop(context);
                  },
                ))
            .toList(),
      ),
    );
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
