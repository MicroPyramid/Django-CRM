import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../../core/theme/theme.dart';
import '../../data/models/models.dart';
import '../../providers/leads_provider.dart';
import '../../providers/lookup_provider.dart';
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

  // Basic Info Controllers
  final _titleController = TextEditingController();
  final _firstNameController = TextEditingController();
  final _lastNameController = TextEditingController();
  final _companyController = TextEditingController();
  final _emailController = TextEditingController();
  final _phoneController = TextEditingController();
  final _jobTitleController = TextEditingController();
  final _websiteController = TextEditingController();
  final _industryController = TextEditingController();
  final _notesController = TextEditingController();

  // Classification Fields
  LeadStatus _status = LeadStatus.assigned;
  LeadSource _source = LeadSource.email;
  LeadRating _rating = LeadRating.cold;

  // Relationship Fields
  List<String> _assignedToIds = [];
  List<String> _tagIds = [];

  bool _isLoading = false;
  bool _isFetchingLead = false;
  String? _fetchError;
  Lead? _existingLead;

  @override
  void initState() {
    super.initState();
    // Fetch lookup data
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(lookupProvider.notifier).fetchAll();
    });

    if (widget.initialLead != null) {
      _populateFromLead(widget.initialLead!);
    } else if (widget.isEditMode) {
      _fetchLead();
    }
  }

  @override
  void dispose() {
    _titleController.dispose();
    _firstNameController.dispose();
    _lastNameController.dispose();
    _companyController.dispose();
    _emailController.dispose();
    _phoneController.dispose();
    _jobTitleController.dispose();
    _websiteController.dispose();
    _industryController.dispose();
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
    _titleController.text = lead.title ?? '';
    _firstNameController.text = lead.firstName;
    _lastNameController.text = lead.lastName;
    _companyController.text = lead.companyName;
    _emailController.text = lead.email;
    _phoneController.text = lead.phone ?? '';
    _jobTitleController.text = lead.jobTitle ?? '';
    _websiteController.text = lead.website ?? '';
    _industryController.text = lead.industry ?? '';
    _notesController.text = lead.description ?? '';
    _status = lead.status;
    _source = lead.source;
    _rating = lead.rating;
    _assignedToIds = List.from(lead.assignedToIds);
    _tagIds = List.from(lead.tagIds);
  }

  bool get _hasUnsavedChanges {
    if (_existingLead != null) {
      return _titleController.text != (_existingLead!.title ?? '') ||
          _firstNameController.text != _existingLead!.firstName ||
          _lastNameController.text != _existingLead!.lastName ||
          _companyController.text != _existingLead!.companyName ||
          _emailController.text != _existingLead!.email ||
          _phoneController.text != (_existingLead!.phone ?? '') ||
          _jobTitleController.text != (_existingLead!.jobTitle ?? '') ||
          _websiteController.text != (_existingLead!.website ?? '') ||
          _industryController.text != (_existingLead!.industry ?? '') ||
          _notesController.text != (_existingLead!.description ?? '') ||
          _status != _existingLead!.status ||
          _source != _existingLead!.source ||
          _rating != _existingLead!.rating ||
          !_listEquals(_assignedToIds, _existingLead!.assignedToIds) ||
          !_listEquals(_tagIds, _existingLead!.tagIds);
    }
    return _titleController.text.isNotEmpty ||
        _firstNameController.text.isNotEmpty ||
        _lastNameController.text.isNotEmpty ||
        _companyController.text.isNotEmpty ||
        _emailController.text.isNotEmpty ||
        _phoneController.text.isNotEmpty ||
        _notesController.text.isNotEmpty ||
        _assignedToIds.isNotEmpty ||
        _tagIds.isNotEmpty;
  }

  bool _listEquals(List<String> a, List<String> b) {
    if (a.length != b.length) return false;
    for (int i = 0; i < a.length; i++) {
      if (a[i] != b[i]) return false;
    }
    return true;
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
    final payload = <String, dynamic>{
      'first_name': _firstNameController.text.trim(),
      'last_name': _lastNameController.text.trim(),
      'email': _emailController.text.trim(),
      'company_name': _companyController.text.trim(),
      'status': _status.value,
      'source': _source.value,
      'rating': _rating.value,
    };

    // Optional fields - include empty string to clear if in edit mode
    final title = _titleController.text.trim();
    final phone = _phoneController.text.trim();
    final jobTitle = _jobTitleController.text.trim();
    final website = _websiteController.text.trim();
    final industry = _industryController.text.trim();
    final notes = _notesController.text.trim();

    if (title.isNotEmpty || widget.isEditMode) {
      payload['title'] = title.isEmpty ? null : title;
    }
    // Only include phone if it has a valid value (backend validator rejects empty strings)
    debugPrint('Phone field value: "$phone" (length: ${phone.length})');
    if (phone.isNotEmpty) {
      debugPrint('Including phone in payload');
      payload['phone'] = phone;
    } else {
      debugPrint('NOT including phone in payload (empty)');
    }
    if (jobTitle.isNotEmpty || widget.isEditMode) {
      payload['job_title'] = jobTitle.isEmpty ? null : jobTitle;
    }
    if (website.isNotEmpty || widget.isEditMode) {
      payload['website'] = website.isEmpty ? null : website;
    }
    if (industry.isNotEmpty || widget.isEditMode) {
      payload['industry'] = industry.isEmpty ? null : industry;
    }
    if (notes.isNotEmpty || widget.isEditMode) {
      payload['description'] = notes.isEmpty ? null : notes;
    }
    // Always include these - empty list clears them
    payload['assigned_to'] = _assignedToIds;
    payload['tags'] = _tagIds;

    return payload;
  }

  Future<void> _handleSubmit() async {
    if (!_formKey.currentState!.validate()) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text('Please fix the errors in the form'),
          behavior: SnackBarBehavior.floating,
          backgroundColor: AppColors.danger600,
        ),
      );
      return;
    }

    setState(() => _isLoading = true);

    final payload = _buildPayload();
    final notifier = ref.read(leadsProvider.notifier);

    final response = widget.isEditMode
        ? await notifier.updateLead(widget.leadId!, payload)
        : await notifier.createLead(payload);

    debugPrint('Response: success=${response.success}, message=${response.message}, statusCode=${response.statusCode}');

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

            // Contact Details Section
            _buildSectionTitle('Contact Details'),
            const SizedBox(height: 16),
            _buildContactFields(),

            const SizedBox(height: 32),

            // Classification Section
            _buildSectionTitle('Classification'),
            const SizedBox(height: 16),
            _buildClassificationFields(),

            const SizedBox(height: 32),

            // Relationships Section
            _buildSectionTitle('Relationships'),
            const SizedBox(height: 16),
            _buildRelationshipFields(),

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
        // Title (Lead Subject)
        FloatingLabelInput(
          label: 'Title (Optional)',
          hint: 'e.g. Website Inquiry',
          controller: _titleController,
          prefixIcon: LucideIcons.fileText,
          textInputAction: TextInputAction.next,
        ),

        const SizedBox(height: 16),

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

        // Job Title
        FloatingLabelInput(
          label: 'Job Title (Optional)',
          hint: 'e.g. Marketing Manager',
          controller: _jobTitleController,
          prefixIcon: LucideIcons.briefcase,
          textInputAction: TextInputAction.next,
        ),

        const SizedBox(height: 16),

        // Industry
        FloatingLabelInput(
          label: 'Industry (Optional)',
          hint: 'e.g. Technology',
          controller: _industryController,
          prefixIcon: LucideIcons.factory,
          textInputAction: TextInputAction.next,
        ),
      ],
    );
  }

  Widget _buildContactFields() {
    return Column(
      children: [
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

        const SizedBox(height: 16),

        // Website
        FloatingLabelInput(
          label: 'Website (Optional)',
          hint: 'https://acme.com',
          controller: _websiteController,
          prefixIcon: LucideIcons.globe,
          keyboardType: TextInputType.url,
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

  Widget _buildRelationshipFields() {
    final lookupState = ref.watch(lookupProvider);

    return Column(
      children: [
        // Assigned To (Multi-select)
        _buildMultiSelectField(
          label: 'Assigned To',
          icon: LucideIcons.users,
          selectedCount: _assignedToIds.length,
          selectedLabel: _getSelectedUsersLabel(lookupState.users),
          onTap: () => _showAssignedToPicker(),
        ),

        const SizedBox(height: 16),

        // Tags (Multi-select)
        _buildMultiSelectField(
          label: 'Tags',
          icon: LucideIcons.tag,
          selectedCount: _tagIds.length,
          selectedLabel: _getSelectedTagsLabel(lookupState.tags),
          onTap: () => _showTagsPicker(),
        ),
      ],
    );
  }

  String _getSelectedUsersLabel(List<UserLookup> users) {
    if (_assignedToIds.isEmpty) return 'Select users';
    final selectedUsers = users.where((u) => _assignedToIds.contains(u.id)).toList();
    if (selectedUsers.isEmpty) return '${_assignedToIds.length} selected';
    if (selectedUsers.length == 1) return selectedUsers.first.displayName;
    return '${selectedUsers.length} users selected';
  }

  String _getSelectedTagsLabel(List<TagLookup> tags) {
    if (_tagIds.isEmpty) return 'Select tags';
    final selectedTags = tags.where((t) => _tagIds.contains(t.id)).toList();
    if (selectedTags.isEmpty) return '${_tagIds.length} selected';
    if (selectedTags.length == 1) return selectedTags.first.name;
    return '${selectedTags.length} tags selected';
  }

  Widget _buildMultiSelectField({
    required String label,
    required IconData icon,
    required int selectedCount,
    required String selectedLabel,
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
              children: [
                Icon(
                  icon,
                  size: 20,
                  color: AppColors.textSecondary,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    selectedLabel,
                    style: AppTypography.body.copyWith(
                      color: selectedCount > 0
                          ? AppColors.textPrimary
                          : AppColors.textSecondary,
                    ),
                  ),
                ),
                if (selectedCount > 0) ...[
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: AppColors.primary100,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      selectedCount.toString(),
                      style: AppTypography.caption.copyWith(
                        color: AppColors.primary600,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                ],
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

  void _showAssignedToPicker() {
    final users = ref.read(lookupProvider).users;

    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.surface,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => _MultiSelectPickerSheet<UserLookup>(
        title: 'Assign To',
        items: users,
        selectedIds: _assignedToIds,
        getItemId: (user) => user.id,
        getItemLabel: (user) => user.displayName,
        getItemSubtitle: (user) => user.email,
        onSelectionChanged: (ids) {
          setState(() => _assignedToIds = ids);
        },
      ),
    );
  }

  void _showTagsPicker() {
    final tags = ref.read(lookupProvider).tags;

    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.surface,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => _MultiSelectPickerSheet<TagLookup>(
        title: 'Select Tags',
        items: tags,
        selectedIds: _tagIds,
        getItemId: (tag) => tag.id,
        getItemLabel: (tag) => tag.name,
        getItemColor: (tag) => _getTagColor(tag.color),
        onSelectionChanged: (ids) {
          setState(() => _tagIds = ids);
        },
      ),
    );
  }

  Color _getTagColor(String colorName) {
    switch (colorName.toLowerCase()) {
      case 'red':
        return AppColors.danger500;
      case 'orange':
        return AppColors.warning500;
      case 'yellow':
        return Colors.amber;
      case 'green':
        return AppColors.success500;
      case 'blue':
        return AppColors.primary500;
      case 'purple':
        return AppColors.purple500;
      case 'pink':
        return Colors.pink;
      default:
        return AppColors.gray500;
    }
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

/// Multi-select picker sheet
class _MultiSelectPickerSheet<T> extends StatefulWidget {
  final String title;
  final List<T> items;
  final List<String> selectedIds;
  final String Function(T) getItemId;
  final String Function(T) getItemLabel;
  final String? Function(T)? getItemSubtitle;
  final Color? Function(T)? getItemColor;
  final void Function(List<String>) onSelectionChanged;

  const _MultiSelectPickerSheet({
    required this.title,
    required this.items,
    required this.selectedIds,
    required this.getItemId,
    required this.getItemLabel,
    this.getItemSubtitle,
    this.getItemColor,
    required this.onSelectionChanged,
  });

  @override
  State<_MultiSelectPickerSheet<T>> createState() =>
      _MultiSelectPickerSheetState<T>();
}

class _MultiSelectPickerSheetState<T>
    extends State<_MultiSelectPickerSheet<T>> {
  late List<String> _selectedIds;
  String _searchQuery = '';

  @override
  void initState() {
    super.initState();
    _selectedIds = List.from(widget.selectedIds);
  }

  List<T> get _filteredItems {
    if (_searchQuery.isEmpty) return widget.items;
    return widget.items.where((item) {
      final label = widget.getItemLabel(item).toLowerCase();
      final subtitle = widget.getItemSubtitle?.call(item)?.toLowerCase() ?? '';
      return label.contains(_searchQuery.toLowerCase()) ||
          subtitle.contains(_searchQuery.toLowerCase());
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    return DraggableScrollableSheet(
      initialChildSize: 0.7,
      minChildSize: 0.5,
      maxChildSize: 0.9,
      expand: false,
      builder: (context, scrollController) => Column(
        children: [
          // Handle
          Container(
            margin: const EdgeInsets.only(top: 12),
            width: 40,
            height: 4,
            decoration: BoxDecoration(
              color: AppColors.gray300,
              borderRadius: BorderRadius.circular(2),
            ),
          ),

          // Header
          Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(widget.title, style: AppTypography.h3),
                TextButton(
                  onPressed: () {
                    widget.onSelectionChanged(_selectedIds);
                    Navigator.pop(context);
                  },
                  child: const Text('Done'),
                ),
              ],
            ),
          ),

          // Search
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: TextField(
              decoration: InputDecoration(
                hintText: 'Search...',
                prefixIcon: const Icon(LucideIcons.search, size: 20),
                filled: true,
                fillColor: AppColors.gray50,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: BorderSide.none,
                ),
                contentPadding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 12,
                ),
              ),
              onChanged: (value) => setState(() => _searchQuery = value),
            ),
          ),

          const SizedBox(height: 8),

          // List
          Expanded(
            child: ListView.builder(
              controller: scrollController,
              itemCount: _filteredItems.length,
              itemBuilder: (context, index) {
                final item = _filteredItems[index];
                final id = widget.getItemId(item);
                final isSelected = _selectedIds.contains(id);
                final color = widget.getItemColor?.call(item);
                final subtitle = widget.getItemSubtitle?.call(item);

                return InkWell(
                  onTap: () {
                    setState(() {
                      if (isSelected) {
                        _selectedIds.remove(id);
                      } else {
                        _selectedIds.add(id);
                      }
                    });
                  },
                  child: Padding(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 16,
                      vertical: 12,
                    ),
                    child: Row(
                      children: [
                        // Checkbox
                        Container(
                          width: 24,
                          height: 24,
                          decoration: BoxDecoration(
                            color: isSelected
                                ? AppColors.primary600
                                : AppColors.surface,
                            borderRadius: BorderRadius.circular(6),
                            border: Border.all(
                              color: isSelected
                                  ? AppColors.primary600
                                  : AppColors.gray300,
                              width: 2,
                            ),
                          ),
                          child: isSelected
                              ? const Icon(
                                  LucideIcons.check,
                                  size: 16,
                                  color: Colors.white,
                                )
                              : null,
                        ),

                        const SizedBox(width: 12),

                        // Color indicator (for tags)
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

                        // Label
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                widget.getItemLabel(item),
                                style: AppTypography.body.copyWith(
                                  fontWeight: isSelected
                                      ? FontWeight.w600
                                      : FontWeight.normal,
                                ),
                              ),
                              if (subtitle != null && subtitle.isNotEmpty)
                                Text(
                                  subtitle,
                                  style: AppTypography.caption.copyWith(
                                    color: AppColors.textSecondary,
                                  ),
                                ),
                            ],
                          ),
                        ),
                      ],
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
