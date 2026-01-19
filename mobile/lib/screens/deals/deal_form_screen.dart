import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../../core/theme/theme.dart';
import '../../data/models/models.dart';
import '../../providers/deals_provider.dart';
import '../../providers/lookup_provider.dart';
import '../../widgets/common/common.dart';

/// Deal Form Screen - Reusable for both Create and Edit
class DealFormScreen extends ConsumerStatefulWidget {
  final String? dealId;
  final Deal? initialDeal;

  const DealFormScreen({
    super.key,
    this.dealId,
    this.initialDeal,
  });

  bool get isEditMode => dealId != null;

  @override
  ConsumerState<DealFormScreen> createState() => _DealFormScreenState();
}

class _DealFormScreenState extends ConsumerState<DealFormScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _amountController = TextEditingController();
  final _probabilityController = TextEditingController();
  final _notesController = TextEditingController();

  DealStage _stage = DealStage.prospecting;
  OpportunityType _opportunityType = OpportunityType.newBusiness;
  OpportunitySource _leadSource = OpportunitySource.none;
  Currency _currency = Currency.usd;
  DateTime? _closeDate;
  bool _isLoading = false;
  bool _isFetchingDeal = false;
  String? _fetchError;
  Deal? _existingDeal;

  // Selector state
  String? _selectedAccountId;
  List<String> _selectedContactIds = [];
  List<String> _selectedAssignedToIds = [];
  List<String> _selectedTagIds = [];

  @override
  void initState() {
    super.initState();
    _probabilityController.text = _stage.defaultProbability.toString();

    // Fetch lookup data
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(lookupProvider.notifier).fetchAll();
    });

    if (widget.initialDeal != null) {
      _populateFromDeal(widget.initialDeal!);
    } else if (widget.isEditMode) {
      _fetchDeal();
    }
  }

  @override
  void dispose() {
    _nameController.dispose();
    _amountController.dispose();
    _probabilityController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  Future<void> _fetchDeal() async {
    setState(() {
      _isFetchingDeal = true;
      _fetchError = null;
    });

    final deal = await ref.read(dealsProvider.notifier).getDeal(widget.dealId!);

    if (mounted) {
      setState(() {
        _isFetchingDeal = false;
        if (deal != null) {
          _existingDeal = deal;
          _populateFromDeal(deal);
        } else {
          _fetchError = 'Failed to load deal';
        }
      });
    }
  }

  void _populateFromDeal(Deal deal) {
    _existingDeal = deal;
    _nameController.text = deal.title;
    _amountController.text = deal.value > 0 ? deal.value.toStringAsFixed(2) : '';
    _probabilityController.text = deal.probability.toString();
    _notesController.text = deal.notes ?? '';
    _stage = deal.stage;
    _opportunityType = deal.opportunityType;
    _leadSource = deal.leadSource;
    _currency = deal.currency;
    _closeDate = deal.closeDate;
    _selectedAccountId = deal.accountId;
    _selectedContactIds = List.from(deal.contactIds);
    _selectedAssignedToIds = List.from(deal.assignedToIds);
    _selectedTagIds = List.from(deal.tagIds);
  }

  bool get _hasUnsavedChanges {
    if (_existingDeal != null) {
      return _nameController.text != _existingDeal!.title ||
          _amountController.text != (_existingDeal!.value > 0 ? _existingDeal!.value.toStringAsFixed(2) : '') ||
          _probabilityController.text != _existingDeal!.probability.toString() ||
          _notesController.text != (_existingDeal!.notes ?? '') ||
          _stage != _existingDeal!.stage ||
          _opportunityType != _existingDeal!.opportunityType ||
          _leadSource != _existingDeal!.leadSource ||
          _currency != _existingDeal!.currency ||
          _closeDate != _existingDeal!.closeDate ||
          _selectedAccountId != _existingDeal!.accountId ||
          !_listEquals(_selectedContactIds, _existingDeal!.contactIds) ||
          !_listEquals(_selectedAssignedToIds, _existingDeal!.assignedToIds) ||
          !_listEquals(_selectedTagIds, _existingDeal!.tagIds);
    }
    return _nameController.text.isNotEmpty ||
        _amountController.text.isNotEmpty ||
        _notesController.text.isNotEmpty ||
        _selectedAccountId != null ||
        _selectedContactIds.isNotEmpty ||
        _selectedAssignedToIds.isNotEmpty ||
        _selectedTagIds.isNotEmpty;
  }

  bool _listEquals(List<String> a, List<String> b) {
    if (a.length != b.length) return false;
    final sortedA = List.from(a)..sort();
    final sortedB = List.from(b)..sort();
    for (int i = 0; i < sortedA.length; i++) {
      if (sortedA[i] != sortedB[i]) return false;
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

  Deal _buildDeal() {
    final amount = double.tryParse(_amountController.text.trim()) ?? 0.0;
    final probability = int.tryParse(_probabilityController.text.trim()) ?? _stage.defaultProbability;

    // Get account name from lookup
    final lookupState = ref.read(lookupProvider);
    final account = lookupState.accounts.where((a) => a.id == _selectedAccountId).firstOrNull;

    return Deal(
      id: widget.dealId ?? '',
      title: _nameController.text.trim(),
      value: amount,
      stage: _stage,
      probability: probability,
      closeDate: _closeDate,
      companyName: account?.name ?? _existingDeal?.companyName ?? '',
      accountId: _selectedAccountId,
      assignedTo: _existingDeal?.assignedTo ?? '',
      assignedToIds: _selectedAssignedToIds,
      priority: Priority.medium,
      labels: _existingDeal?.labels ?? [],
      tagIds: _selectedTagIds,
      contactIds: _selectedContactIds,
      notes: _notesController.text.trim().isEmpty ? null : _notesController.text.trim(),
      opportunityType: _opportunityType,
      leadSource: _leadSource,
      currency: _currency,
      createdAt: _existingDeal?.createdAt ?? DateTime.now(),
      updatedAt: DateTime.now(),
    );
  }

  Future<void> _handleSubmit() async {
    if (!_formKey.currentState!.validate()) return;

    // Validate closed_on for closed stages
    if ((_stage == DealStage.closedWon || _stage == DealStage.closedLost) && _closeDate == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Close date is required for ${_stage.label} stage'),
          behavior: SnackBarBehavior.floating,
          backgroundColor: AppColors.danger600,
        ),
      );
      return;
    }

    setState(() => _isLoading = true);

    final deal = _buildDeal();
    final notifier = ref.read(dealsProvider.notifier);

    final response = widget.isEditMode
        ? await notifier.updateDeal(widget.dealId!, deal)
        : await notifier.createDeal(deal);

    if (mounted) {
      setState(() => _isLoading = false);

      if (response.success) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(widget.isEditMode ? 'Deal updated successfully' : 'Deal created successfully'),
            behavior: SnackBarBehavior.floating,
          ),
        );
        context.pop(true);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(response.error ?? 'Failed to save deal'),
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
          title: Text(widget.isEditMode ? 'Edit Deal' : 'New Deal'),
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
    if (_isFetchingDeal) {
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
              onPressed: _fetchDeal,
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

            // Deal Details Section
            _buildSectionTitle('Deal Details'),
            const SizedBox(height: 16),
            _buildDealDetailsFields(),

            const SizedBox(height: 32),

            // Relationships Section
            _buildSectionTitle('Relationships'),
            const SizedBox(height: 16),
            _buildRelationshipFields(),

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
              hint: 'Add any additional notes about this deal...',
              controller: _notesController,
              maxLines: 4,
            ),

            const SizedBox(height: 32),

            // Submit Button
            PrimaryButton(
              label: widget.isEditMode ? 'Update Deal' : 'Create Deal',
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
        // Deal Name
        FloatingLabelInput(
          label: 'Deal Name',
          hint: 'Enterprise Contract',
          controller: _nameController,
          prefixIcon: LucideIcons.briefcase,
          textInputAction: TextInputAction.next,
          validator: (value) {
            if (value == null || value.isEmpty) {
              return 'Deal name is required';
            }
            return null;
          },
        ),

        const SizedBox(height: 16),

        // Amount with Currency
        Row(
          children: [
            // Currency Selector
            GestureDetector(
              onTap: _showCurrencyPicker,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
                decoration: BoxDecoration(
                  color: AppColors.gray50,
                  borderRadius: const BorderRadius.only(
                    topLeft: Radius.circular(12),
                    bottomLeft: Radius.circular(12),
                  ),
                  border: Border.all(color: AppColors.border),
                ),
                child: Row(
                  children: [
                    Text(
                      _currency.symbol,
                      style: AppTypography.body.copyWith(
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(width: 4),
                    Icon(
                      LucideIcons.chevronDown,
                      size: 16,
                      color: AppColors.textSecondary,
                    ),
                  ],
                ),
              ),
            ),
            // Amount Input
            Expanded(
              child: TextFormField(
                controller: _amountController,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                textInputAction: TextInputAction.next,
                decoration: InputDecoration(
                  hintText: '0.00',
                  hintStyle: AppTypography.body.copyWith(
                    color: AppColors.gray400,
                  ),
                  filled: true,
                  fillColor: AppColors.gray50,
                  border: const OutlineInputBorder(
                    borderRadius: BorderRadius.only(
                      topRight: Radius.circular(12),
                      bottomRight: Radius.circular(12),
                    ),
                    borderSide: BorderSide.none,
                  ),
                  enabledBorder: OutlineInputBorder(
                    borderRadius: const BorderRadius.only(
                      topRight: Radius.circular(12),
                      bottomRight: Radius.circular(12),
                    ),
                    borderSide: BorderSide(color: AppColors.border),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderRadius: const BorderRadius.only(
                      topRight: Radius.circular(12),
                      bottomRight: Radius.circular(12),
                    ),
                    borderSide: BorderSide(color: AppColors.primary500, width: 2),
                  ),
                  contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
                ),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildDealDetailsFields() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Stage Dropdown
        _buildDropdownField(
          label: 'Stage',
          value: _stage.label,
          color: _stage.color,
          onTap: _showStagePicker,
        ),

        const SizedBox(height: 16),

        // Probability
        FloatingLabelInput(
          label: 'Probability (%)',
          hint: '50',
          controller: _probabilityController,
          prefixIcon: LucideIcons.percent,
          keyboardType: TextInputType.number,
          textInputAction: TextInputAction.next,
          validator: (value) {
            if (value != null && value.isNotEmpty) {
              final prob = int.tryParse(value);
              if (prob == null || prob < 0 || prob > 100) {
                return 'Probability must be 0-100';
              }
            }
            return null;
          },
        ),

        const SizedBox(height: 16),

        // Close Date
        _buildDateField(
          label: 'Expected Close Date',
          value: _closeDate,
          onTap: _selectCloseDate,
        ),
      ],
    );
  }

  Widget _buildRelationshipFields() {
    final lookupState = ref.watch(lookupProvider);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Account Selector
        _buildSingleSelectField(
          label: 'Account',
          value: _selectedAccountId != null
              ? lookupState.accounts.where((a) => a.id == _selectedAccountId).firstOrNull?.name
              : null,
          placeholder: 'Select account',
          icon: LucideIcons.building2,
          isLoading: lookupState.isLoadingAccounts,
          onTap: _showAccountPicker,
          onClear: _selectedAccountId != null ? () => setState(() => _selectedAccountId = null) : null,
        ),

        const SizedBox(height: 16),

        // Contacts Multi-Select
        _buildMultiSelectField(
          label: 'Contacts',
          selectedCount: _selectedContactIds.length,
          selectedItems: _selectedContactIds
              .map((id) => lookupState.contacts.where((c) => c.id == id).firstOrNull?.fullName ?? '')
              .where((name) => name.isNotEmpty)
              .toList(),
          placeholder: 'Select contacts',
          icon: LucideIcons.users,
          isLoading: lookupState.isLoadingContacts,
          onTap: _showContactsPicker,
        ),

        const SizedBox(height: 16),

        // Assigned To Multi-Select
        _buildMultiSelectField(
          label: 'Assigned To',
          selectedCount: _selectedAssignedToIds.length,
          selectedItems: _selectedAssignedToIds
              .map((id) => lookupState.users.where((u) => u.id == id).firstOrNull?.displayName ?? '')
              .where((name) => name.isNotEmpty)
              .toList(),
          placeholder: 'Select assignees',
          icon: LucideIcons.userCheck,
          isLoading: lookupState.isLoadingUsers,
          onTap: _showAssignedToPicker,
        ),

        const SizedBox(height: 16),

        // Tags Multi-Select
        _buildMultiSelectField(
          label: 'Tags',
          selectedCount: _selectedTagIds.length,
          selectedItems: _selectedTagIds
              .map((id) => lookupState.tags.where((t) => t.id == id).firstOrNull?.name ?? '')
              .where((name) => name.isNotEmpty)
              .toList(),
          placeholder: 'Select tags',
          icon: LucideIcons.tag,
          isLoading: lookupState.isLoadingTags,
          onTap: _showTagsPicker,
        ),
      ],
    );
  }

  Widget _buildClassificationFields() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Opportunity Type Dropdown
        _buildDropdownField(
          label: 'Opportunity Type',
          value: _opportunityType.label,
          onTap: _showOpportunityTypePicker,
        ),

        const SizedBox(height: 16),

        // Lead Source Dropdown
        _buildDropdownField(
          label: 'Lead Source',
          value: _leadSource.label,
          onTap: _showLeadSourcePicker,
        ),
      ],
    );
  }

  Widget _buildDropdownField({
    required String label,
    required String value,
    Color? color,
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
                Expanded(
                  child: Text(
                    value,
                    style: AppTypography.body,
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
        ),
      ],
    );
  }

  Widget _buildSingleSelectField({
    required String label,
    required String? value,
    required String placeholder,
    required IconData icon,
    required bool isLoading,
    required VoidCallback onTap,
    VoidCallback? onClear,
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
          onTap: isLoading ? null : onTap,
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
                  child: isLoading
                      ? Row(
                          children: [
                            SizedBox(
                              width: 16,
                              height: 16,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                color: AppColors.textSecondary,
                              ),
                            ),
                            const SizedBox(width: 8),
                            Text(
                              'Loading...',
                              style: AppTypography.body.copyWith(
                                color: AppColors.gray400,
                              ),
                            ),
                          ],
                        )
                      : Text(
                          value ?? placeholder,
                          style: AppTypography.body.copyWith(
                            color: value != null ? AppColors.textPrimary : AppColors.gray400,
                          ),
                        ),
                ),
                if (onClear != null && value != null) ...[
                  GestureDetector(
                    onTap: onClear,
                    child: Icon(
                      LucideIcons.x,
                      size: 18,
                      color: AppColors.textSecondary,
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

  Widget _buildMultiSelectField({
    required String label,
    required int selectedCount,
    required List<String> selectedItems,
    required String placeholder,
    required IconData icon,
    required bool isLoading,
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
          onTap: isLoading ? null : onTap,
          child: Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
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
                  child: isLoading
                      ? Row(
                          children: [
                            SizedBox(
                              width: 16,
                              height: 16,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                color: AppColors.textSecondary,
                              ),
                            ),
                            const SizedBox(width: 8),
                            Text(
                              'Loading...',
                              style: AppTypography.body.copyWith(
                                color: AppColors.gray400,
                              ),
                            ),
                          ],
                        )
                      : selectedCount > 0
                          ? Wrap(
                              spacing: 4,
                              runSpacing: 4,
                              children: [
                                ...selectedItems.take(2).map((item) => _buildChip(item)),
                                if (selectedCount > 2)
                                  _buildChip('+${selectedCount - 2} more', isMore: true),
                              ],
                            )
                          : Text(
                              placeholder,
                              style: AppTypography.body.copyWith(
                                color: AppColors.gray400,
                              ),
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
        ),
      ],
    );
  }

  Widget _buildChip(String label, {bool isMore = false}) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: isMore ? AppColors.primary100 : AppColors.gray200,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        label,
        style: AppTypography.caption.copyWith(
          color: isMore ? AppColors.primary700 : AppColors.textPrimary,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }

  Widget _buildDateField({
    required String label,
    required DateTime? value,
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
                  LucideIcons.calendar,
                  size: 20,
                  color: AppColors.textSecondary,
                ),
                const SizedBox(width: 12),
                Text(
                  value != null ? _formatDate(value) : 'Select date',
                  style: AppTypography.body.copyWith(
                    color: value != null ? AppColors.textPrimary : AppColors.gray400,
                  ),
                ),
                const Spacer(),
                if (value != null)
                  GestureDetector(
                    onTap: () => setState(() => _closeDate = null),
                    child: Icon(
                      LucideIcons.x,
                      size: 18,
                      color: AppColors.textSecondary,
                    ),
                  ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  String _formatDate(DateTime date) {
    final months = [
      'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    ];
    return '${months[date.month - 1]} ${date.day}, ${date.year}';
  }

  Future<void> _selectCloseDate() async {
    final date = await showDatePicker(
      context: context,
      initialDate: _closeDate ?? DateTime.now(),
      firstDate: DateTime(2020),
      lastDate: DateTime(2030),
    );
    if (date != null) {
      setState(() => _closeDate = date);
    }
  }

  void _showStagePicker() {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => _PickerBottomSheet(
        title: 'Select Stage',
        options: DealStage.values
            .map((stage) => _PickerOption(
                  label: stage.label,
                  isSelected: _stage == stage,
                  color: stage.color,
                  onTap: () {
                    setState(() {
                      _stage = stage;
                      // Auto-update probability based on stage
                      _probabilityController.text = stage.defaultProbability.toString();
                    });
                    Navigator.pop(context);
                  },
                ))
            .toList(),
      ),
    );
  }

  void _showOpportunityTypePicker() {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => _PickerBottomSheet(
        title: 'Select Opportunity Type',
        options: OpportunityType.values
            .map((type) => _PickerOption(
                  label: type.label,
                  isSelected: _opportunityType == type,
                  onTap: () {
                    setState(() => _opportunityType = type);
                    Navigator.pop(context);
                  },
                ))
            .toList(),
      ),
    );
  }

  void _showLeadSourcePicker() {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => _PickerBottomSheet(
        title: 'Select Lead Source',
        options: OpportunitySource.values
            .map((source) => _PickerOption(
                  label: source.label,
                  isSelected: _leadSource == source,
                  onTap: () {
                    setState(() => _leadSource = source);
                    Navigator.pop(context);
                  },
                ))
            .toList(),
      ),
    );
  }

  void _showCurrencyPicker() {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => _PickerBottomSheet(
        title: 'Select Currency',
        options: Currency.values
            .map((curr) => _PickerOption(
                  label: '${curr.symbol} - ${curr.label}',
                  isSelected: _currency == curr,
                  onTap: () {
                    setState(() => _currency = curr);
                    Navigator.pop(context);
                  },
                ))
            .toList(),
      ),
    );
  }

  void _showAccountPicker() {
    final accounts = ref.read(lookupProvider).accounts;
    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.surface,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.6,
        minChildSize: 0.3,
        maxChildSize: 0.9,
        expand: false,
        builder: (context, scrollController) => _SearchablePickerSheet(
          title: 'Select Account',
          searchHint: 'Search accounts...',
          items: accounts,
          itemBuilder: (account) => _PickerOption(
            label: account.name,
            subtitle: account.website,
            isSelected: _selectedAccountId == account.id,
            onTap: () {
              setState(() => _selectedAccountId = account.id);
              Navigator.pop(context);
            },
          ),
          searchMatcher: (account, query) =>
              account.name.toLowerCase().contains(query.toLowerCase()),
          scrollController: scrollController,
          emptyMessage: 'No accounts found',
        ),
      ),
    );
  }

  void _showContactsPicker() {
    final contacts = ref.read(lookupProvider).contacts;
    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.surface,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.6,
        minChildSize: 0.3,
        maxChildSize: 0.9,
        expand: false,
        builder: (context, scrollController) => _MultiSelectPickerSheet<ContactLookup>(
          title: 'Select Contacts',
          searchHint: 'Search contacts...',
          items: contacts,
          selectedIds: _selectedContactIds,
          getId: (c) => c.id,
          getLabel: (c) => c.fullName,
          getSubtitle: (c) => c.email,
          searchMatcher: (contact, query) =>
              contact.fullName.toLowerCase().contains(query.toLowerCase()) ||
              (contact.email?.toLowerCase().contains(query.toLowerCase()) ?? false),
          scrollController: scrollController,
          emptyMessage: 'No contacts found',
          onDone: (selectedIds) {
            setState(() => _selectedContactIds = selectedIds);
          },
        ),
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
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.6,
        minChildSize: 0.3,
        maxChildSize: 0.9,
        expand: false,
        builder: (context, scrollController) => _MultiSelectPickerSheet<UserLookup>(
          title: 'Assign To',
          searchHint: 'Search users...',
          items: users,
          selectedIds: _selectedAssignedToIds,
          getId: (u) => u.id,
          getLabel: (u) => u.displayName,
          getSubtitle: (u) => u.email,
          searchMatcher: (user, query) =>
              user.displayName.toLowerCase().contains(query.toLowerCase()) ||
              user.email.toLowerCase().contains(query.toLowerCase()),
          scrollController: scrollController,
          emptyMessage: 'No users found',
          onDone: (selectedIds) {
            setState(() => _selectedAssignedToIds = selectedIds);
          },
        ),
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
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.6,
        minChildSize: 0.3,
        maxChildSize: 0.9,
        expand: false,
        builder: (context, scrollController) => _MultiSelectPickerSheet<TagLookup>(
          title: 'Select Tags',
          searchHint: 'Search tags...',
          items: tags,
          selectedIds: _selectedTagIds,
          getId: (t) => t.id,
          getLabel: (t) => t.name,
          getSubtitle: null,
          searchMatcher: (tag, query) =>
              tag.name.toLowerCase().contains(query.toLowerCase()),
          scrollController: scrollController,
          emptyMessage: 'No tags found',
          onDone: (selectedIds) {
            setState(() => _selectedTagIds = selectedIds);
          },
          tagColors: {for (var t in tags) t.id: t.color},
        ),
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
          Flexible(
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: options,
              ),
            ),
          ),
          const SizedBox(height: 16),
        ],
      ),
    );
  }
}

/// Picker option item
class _PickerOption extends StatelessWidget {
  final String label;
  final String? subtitle;
  final bool isSelected;
  final Color? color;
  final VoidCallback onTap;

  const _PickerOption({
    required this.label,
    this.subtitle,
    required this.isSelected,
    this.color,
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
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    label,
                    style: AppTypography.body.copyWith(
                      fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
                      color: isSelected
                          ? AppColors.primary600
                          : AppColors.textPrimary,
                    ),
                  ),
                  if (subtitle != null && subtitle!.isNotEmpty)
                    Text(
                      subtitle!,
                      style: AppTypography.caption.copyWith(
                        color: AppColors.textSecondary,
                      ),
                    ),
                ],
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

/// Searchable picker sheet for single selection
class _SearchablePickerSheet<T> extends StatefulWidget {
  final String title;
  final String searchHint;
  final List<T> items;
  final Widget Function(T item) itemBuilder;
  final bool Function(T item, String query) searchMatcher;
  final ScrollController scrollController;
  final String emptyMessage;

  const _SearchablePickerSheet({
    required this.title,
    required this.searchHint,
    required this.items,
    required this.itemBuilder,
    required this.searchMatcher,
    required this.scrollController,
    required this.emptyMessage,
  });

  @override
  State<_SearchablePickerSheet<T>> createState() => _SearchablePickerSheetState<T>();
}

class _SearchablePickerSheetState<T> extends State<_SearchablePickerSheet<T>> {
  final _searchController = TextEditingController();
  List<T> _filteredItems = [];

  @override
  void initState() {
    super.initState();
    _filteredItems = widget.items;
    _searchController.addListener(_onSearchChanged);
  }

  @override
  void dispose() {
    _searchController.removeListener(_onSearchChanged);
    _searchController.dispose();
    super.dispose();
  }

  void _onSearchChanged() {
    final query = _searchController.text;
    setState(() {
      if (query.isEmpty) {
        _filteredItems = widget.items;
      } else {
        _filteredItems = widget.items
            .where((item) => widget.searchMatcher(item, query))
            .toList();
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Column(
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
          child: Text(widget.title, style: AppTypography.h3),
        ),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: TextField(
            controller: _searchController,
            decoration: InputDecoration(
              hintText: widget.searchHint,
              prefixIcon: Icon(LucideIcons.search, size: 20),
              filled: true,
              fillColor: AppColors.gray50,
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: BorderSide.none,
              ),
              contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            ),
          ),
        ),
        const SizedBox(height: 8),
        Expanded(
          child: _filteredItems.isEmpty
              ? Center(
                  child: Text(
                    widget.emptyMessage,
                    style: AppTypography.body.copyWith(
                      color: AppColors.textSecondary,
                    ),
                  ),
                )
              : ListView.builder(
                  controller: widget.scrollController,
                  itemCount: _filteredItems.length,
                  itemBuilder: (context, index) =>
                      widget.itemBuilder(_filteredItems[index]),
                ),
        ),
      ],
    );
  }
}

/// Multi-select picker sheet
class _MultiSelectPickerSheet<T> extends StatefulWidget {
  final String title;
  final String searchHint;
  final List<T> items;
  final List<String> selectedIds;
  final String Function(T item) getId;
  final String Function(T item) getLabel;
  final String? Function(T item)? getSubtitle;
  final bool Function(T item, String query) searchMatcher;
  final ScrollController scrollController;
  final String emptyMessage;
  final void Function(List<String> selectedIds) onDone;
  final Map<String, String>? tagColors;

  const _MultiSelectPickerSheet({
    required this.title,
    required this.searchHint,
    required this.items,
    required this.selectedIds,
    required this.getId,
    required this.getLabel,
    this.getSubtitle,
    required this.searchMatcher,
    required this.scrollController,
    required this.emptyMessage,
    required this.onDone,
    this.tagColors,
  });

  @override
  State<_MultiSelectPickerSheet<T>> createState() => _MultiSelectPickerSheetState<T>();
}

class _MultiSelectPickerSheetState<T> extends State<_MultiSelectPickerSheet<T>> {
  final _searchController = TextEditingController();
  List<T> _filteredItems = [];
  late List<String> _selectedIds;

  @override
  void initState() {
    super.initState();
    _filteredItems = widget.items;
    _selectedIds = List.from(widget.selectedIds);
    _searchController.addListener(_onSearchChanged);
  }

  @override
  void dispose() {
    _searchController.removeListener(_onSearchChanged);
    _searchController.dispose();
    super.dispose();
  }

  void _onSearchChanged() {
    final query = _searchController.text;
    setState(() {
      if (query.isEmpty) {
        _filteredItems = widget.items;
      } else {
        _filteredItems = widget.items
            .where((item) => widget.searchMatcher(item, query))
            .toList();
      }
    });
  }

  void _toggleSelection(String id) {
    setState(() {
      if (_selectedIds.contains(id)) {
        _selectedIds.remove(id);
      } else {
        _selectedIds.add(id);
      }
    });
  }

  Color _getTagColor(String colorName) {
    final colors = {
      'gray': AppColors.gray400,
      'red': AppColors.danger500,
      'orange': AppColors.warning500,
      'amber': const Color(0xFFF59E0B),
      'yellow': const Color(0xFFEAB308),
      'lime': const Color(0xFF84CC16),
      'green': AppColors.success500,
      'emerald': const Color(0xFF10B981),
      'teal': AppColors.teal500,
      'cyan': const Color(0xFF06B6D4),
      'sky': const Color(0xFF0EA5E9),
      'blue': AppColors.primary500,
      'indigo': const Color(0xFF6366F1),
      'violet': AppColors.purple500,
      'purple': const Color(0xFFA855F7),
      'fuchsia': const Color(0xFFD946EF),
      'pink': const Color(0xFFEC4899),
      'rose': const Color(0xFFF43F5E),
    };
    return colors[colorName] ?? AppColors.gray400;
  }

  @override
  Widget build(BuildContext context) {
    return Column(
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
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(widget.title, style: AppTypography.h3),
              TextButton(
                onPressed: () {
                  widget.onDone(_selectedIds);
                  Navigator.pop(context);
                },
                child: Text(
                  'Done (${_selectedIds.length})',
                  style: AppTypography.label.copyWith(
                    color: AppColors.primary600,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ],
          ),
        ),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: TextField(
            controller: _searchController,
            decoration: InputDecoration(
              hintText: widget.searchHint,
              prefixIcon: Icon(LucideIcons.search, size: 20),
              filled: true,
              fillColor: AppColors.gray50,
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: BorderSide.none,
              ),
              contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            ),
          ),
        ),
        const SizedBox(height: 8),
        Expanded(
          child: _filteredItems.isEmpty
              ? Center(
                  child: Text(
                    widget.emptyMessage,
                    style: AppTypography.body.copyWith(
                      color: AppColors.textSecondary,
                    ),
                  ),
                )
              : ListView.builder(
                  controller: widget.scrollController,
                  itemCount: _filteredItems.length,
                  itemBuilder: (context, index) {
                    final item = _filteredItems[index];
                    final id = widget.getId(item);
                    final isSelected = _selectedIds.contains(id);
                    final subtitle = widget.getSubtitle?.call(item);
                    final tagColor = widget.tagColors?[id];

                    return InkWell(
                      onTap: () => _toggleSelection(id),
                      child: Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                        child: Row(
                          children: [
                            Container(
                              width: 24,
                              height: 24,
                              decoration: BoxDecoration(
                                color: isSelected
                                    ? AppColors.primary600
                                    : Colors.transparent,
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
                            if (tagColor != null) ...[
                              Container(
                                width: 12,
                                height: 12,
                                decoration: BoxDecoration(
                                  color: _getTagColor(tagColor),
                                  shape: BoxShape.circle,
                                ),
                              ),
                              const SizedBox(width: 8),
                            ],
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    widget.getLabel(item),
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
    );
  }
}
