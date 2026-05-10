import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../../core/theme/theme.dart';
import '../../data/models/ticket.dart';
import '../../data/models/lookup_models.dart';
import '../../providers/tickets_provider.dart';
import '../../providers/lookup_provider.dart';
import '../../widgets/common/common.dart';

/// Shared create / edit form for tickets.
class TicketFormScreen extends ConsumerStatefulWidget {
  final String? ticketId;

  const TicketFormScreen({super.key, this.ticketId});

  bool get isEditMode => ticketId != null;

  @override
  ConsumerState<TicketFormScreen> createState() => _TicketFormScreenState();
}

class _TicketFormScreenState extends ConsumerState<TicketFormScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _descriptionController = TextEditingController();

  TicketStatus _status = TicketStatus.newStatus;
  TicketPriority _priority = TicketPriority.normal;
  TicketType _ticketType = TicketType.question;
  String? _accountId;

  bool _isLoading = false;
  bool _isFetching = false;
  String? _fetchError;

  @override
  void initState() {
    super.initState();
    if (widget.isEditMode) _fetchTicket();
  }

  @override
  void dispose() {
    _nameController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  Future<void> _fetchTicket() async {
    setState(() {
      _isFetching = true;
      _fetchError = null;
    });
    final c = await ref
        .read(ticketsProvider.notifier)
        .getTicketById(widget.ticketId!);
    if (!mounted) return;
    setState(() {
      _isFetching = false;
      if (c != null) {
        _nameController.text = c.name;
        _descriptionController.text = c.description ?? '';
        _status = c.status;
        _priority = c.priority;
        _ticketType = c.ticketType;
        _accountId = c.accountId;
      } else {
        _fetchError = 'Failed to load ticket';
      }
    });
  }

  Map<String, dynamic> _buildPayload() {
    final payload = <String, dynamic>{
      'name': _nameController.text.trim(),
      'status': _status.value,
      'priority': _priority.value,
      'case_type': _ticketType.value,
    };
    final desc = _descriptionController.text.trim();
    if (desc.isNotEmpty || widget.isEditMode) {
      payload['description'] = desc.isEmpty ? null : desc;
    }
    if (_accountId != null && _accountId!.isNotEmpty) {
      payload['account'] = _accountId;
    }
    return payload;
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    if (_accountId == null || _accountId!.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text('Please select an account.'),
          backgroundColor: AppColors.danger600,
          behavior: SnackBarBehavior.floating,
        ),
      );
      return;
    }
    setState(() => _isLoading = true);
    final notifier = ref.read(ticketsProvider.notifier);
    final payload = _buildPayload();
    final res = widget.isEditMode
        ? await notifier.updateTicket(widget.ticketId!, payload)
        : await notifier.createTicket(payload);
    if (!mounted) return;
    setState(() => _isLoading = false);
    if (res.success) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            widget.isEditMode
                ? 'Ticket updated successfully'
                : 'Ticket created successfully',
          ),
          behavior: SnackBarBehavior.floating,
        ),
      );
      context.pop(true);
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(res.message ?? 'Failed to save ticket'),
          backgroundColor: AppColors.danger600,
          behavior: SnackBarBehavior.floating,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.surface,
      appBar: AppBar(
        title: Text(widget.isEditMode ? 'Edit Ticket' : 'New Ticket'),
        backgroundColor: AppColors.surface,
        elevation: 0,
        scrolledUnderElevation: 1,
        leading: IconButton(
          icon: const Icon(LucideIcons.chevronLeft),
          onPressed: () => context.pop(),
        ),
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_isFetching) return const Center(child: CircularProgressIndicator());
    if (_fetchError != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(LucideIcons.alertCircle, size: 48, color: AppColors.danger500),
            const SizedBox(height: 16),
            Text(
              _fetchError!,
              style: AppTypography.body.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
            const SizedBox(height: 16),
            TextButton(onPressed: _fetchTicket, child: const Text('Retry')),
          ],
        ),
      );
    }
    final accounts = ref.watch(accountsProvider);

    return Form(
      key: _formKey,
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _section('Basic Information'),
            const SizedBox(height: 16),
            FloatingLabelInput(
              label: 'Ticket name',
              hint: 'e.g. Login fails on Safari',
              controller: _nameController,
              prefixIcon: LucideIcons.fileText,
              textInputAction: TextInputAction.next,
              validator: (v) {
                if (v == null || v.trim().isEmpty) {
                  return 'Ticket name is required';
                }
                return null;
              },
            ),
            const SizedBox(height: 16),
            _accountField(accounts),
            const SizedBox(height: 32),
            _section('Classification'),
            const SizedBox(height: 16),
            _dropdown(
              label: 'Status',
              value: _status.label,
              onTap: () => _pickStatus(),
            ),
            const SizedBox(height: 16),
            _dropdown(
              label: 'Priority',
              value: _priority.label,
              onTap: () => _pickPriority(),
            ),
            const SizedBox(height: 16),
            _dropdown(
              label: 'Type',
              value: _ticketType.label,
              onTap: () => _pickType(),
            ),
            const SizedBox(height: 32),
            _section('Description'),
            const SizedBox(height: 16),
            TextAreaField(
              label: 'Description',
              hint: 'What is happening? Include reproduction steps if known.',
              controller: _descriptionController,
              maxLines: 5,
            ),
            const SizedBox(height: 32),
            PrimaryButton(
              label: widget.isEditMode ? 'Update Ticket' : 'Create Ticket',
              onPressed: _isLoading ? null : _submit,
              isLoading: _isLoading,
            ),
            const SizedBox(height: 16),
            Center(
              child: GestureDetector(
                onTap: () => context.pop(),
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

  Widget _section(String title) {
    return Text(
      title.toUpperCase(),
      style: AppTypography.overline.copyWith(
        color: AppColors.textSecondary,
        letterSpacing: 1.2,
      ),
    );
  }

  Widget _accountField(List<AccountLookup> accounts) {
    final selected = accounts.where((a) => a.id == _accountId).firstOrNull;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Account',
          style: AppTypography.caption.copyWith(color: AppColors.textSecondary),
        ),
        const SizedBox(height: 8),
        GestureDetector(
          onTap: () => _pickAccount(accounts),
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
                  LucideIcons.building2,
                  size: 20,
                  color: AppColors.textSecondary,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    selected?.name ?? 'Select an account',
                    style: AppTypography.body.copyWith(
                      color: selected != null
                          ? AppColors.textPrimary
                          : AppColors.textSecondary,
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

  Widget _dropdown({
    required String label,
    required String value,
    required VoidCallback onTap,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: AppTypography.caption.copyWith(color: AppColors.textSecondary),
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
                Text(value, style: AppTypography.body),
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

  void _pickStatus() {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => _PickerSheet(
        title: 'Select Status',
        options: TicketStatus.values
            .map(
              (s) => _PickerOption(
                label: s.label,
                isSelected: _status == s,
                color: s.color,
                onTap: () {
                  setState(() => _status = s);
                  Navigator.pop(context);
                },
              ),
            )
            .toList(),
      ),
    );
  }

  void _pickPriority() {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => _PickerSheet(
        title: 'Select Priority',
        options: TicketPriority.values
            .map(
              (p) => _PickerOption(
                label: p.label,
                isSelected: _priority == p,
                color: p.color,
                onTap: () {
                  setState(() => _priority = p);
                  Navigator.pop(context);
                },
              ),
            )
            .toList(),
      ),
    );
  }

  void _pickType() {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => _PickerSheet(
        title: 'Select Type',
        options: TicketType.values
            .map(
              (t) => _PickerOption(
                label: t.label,
                isSelected: _ticketType == t,
                icon: t.icon,
                onTap: () {
                  setState(() => _ticketType = t);
                  Navigator.pop(context);
                },
              ),
            )
            .toList(),
      ),
    );
  }

  void _pickAccount(List<AccountLookup> accounts) {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.surface,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => DraggableScrollableSheet(
        initialChildSize: 0.6,
        minChildSize: 0.3,
        maxChildSize: 0.9,
        expand: false,
        builder: (ctx, controller) => Column(
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
              child: Text('Select Account', style: AppTypography.h3),
            ),
            Expanded(
              child: accounts.isEmpty
                  ? const Center(
                      child: EmptyState(
                        icon: LucideIcons.building2,
                        title: 'No accounts',
                        description:
                            'Create an account on the web to link tickets to it.',
                      ),
                    )
                  : ListView.builder(
                      controller: controller,
                      itemCount: accounts.length,
                      itemBuilder: (_, i) {
                        final a = accounts[i];
                        final isSelected = _accountId == a.id;
                        return InkWell(
                          onTap: () {
                            setState(() => _accountId = a.id);
                            Navigator.pop(context);
                          },
                          child: Padding(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 16,
                              vertical: 14,
                            ),
                            child: Row(
                              children: [
                                Icon(
                                  LucideIcons.building2,
                                  size: 18,
                                  color: AppColors.textSecondary,
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: Text(
                                    a.name,
                                    style: AppTypography.body.copyWith(
                                      fontWeight: isSelected
                                          ? FontWeight.w600
                                          : FontWeight.normal,
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
                      },
                    ),
            ),
          ],
        ),
      ),
    );
  }
}

class _PickerSheet extends StatelessWidget {
  final String title;
  final List<_PickerOption> options;
  const _PickerSheet({required this.title, required this.options});

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
                decoration: BoxDecoration(color: color, shape: BoxShape.circle),
              ),
              const SizedBox(width: 12),
            ],
            if (icon != null) ...[
              Icon(icon, size: 20, color: AppColors.textSecondary),
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
              Icon(LucideIcons.check, size: 20, color: AppColors.primary600),
          ],
        ),
      ),
    );
  }
}
