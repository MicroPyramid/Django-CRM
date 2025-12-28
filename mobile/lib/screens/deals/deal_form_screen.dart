import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../../core/theme/theme.dart';
import '../../data/models/models.dart';
import '../../providers/deals_provider.dart';
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

  @override
  void initState() {
    super.initState();
    _probabilityController.text = _stage.defaultProbability.toString();
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
          _closeDate != _existingDeal!.closeDate;
    }
    return _nameController.text.isNotEmpty ||
        _amountController.text.isNotEmpty ||
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

  Deal _buildDeal() {
    final amount = double.tryParse(_amountController.text.trim()) ?? 0.0;
    final probability = int.tryParse(_probabilityController.text.trim()) ?? _stage.defaultProbability;

    return Deal(
      id: widget.dealId ?? '',
      title: _nameController.text.trim(),
      value: amount,
      stage: _stage,
      probability: probability,
      closeDate: _closeDate,
      companyName: _existingDeal?.companyName ?? '',
      accountId: _existingDeal?.accountId,
      assignedTo: _existingDeal?.assignedTo ?? '',
      assignedToIds: _existingDeal?.assignedToIds ?? [],
      priority: Priority.medium,
      labels: _existingDeal?.labels ?? [],
      tagIds: _existingDeal?.tagIds ?? [],
      contactIds: _existingDeal?.contactIds ?? [],
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
  final bool isSelected;
  final Color? color;
  final VoidCallback onTap;

  const _PickerOption({
    required this.label,
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
