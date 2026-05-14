import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../core/theme/theme.dart';
import '../../providers/auth_provider.dart';
import '../../routes/app_router.dart';
import '../../widgets/common/common.dart';

/// First step of the OTP login flow: collect the user's email and ask the
/// backend to send a 6-digit code. On success we push the code-entry screen
/// with the email pre-filled.
class MagicLinkEmailScreen extends ConsumerStatefulWidget {
  const MagicLinkEmailScreen({super.key});

  @override
  ConsumerState<MagicLinkEmailScreen> createState() =>
      _MagicLinkEmailScreenState();
}

class _MagicLinkEmailScreenState extends ConsumerState<MagicLinkEmailScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  bool _isLoading = false;

  @override
  void dispose() {
    _emailController.dispose();
    super.dispose();
  }

  Future<void> _handleSubmit() async {
    if (!_formKey.currentState!.validate()) return;

    final email = _emailController.text.trim().toLowerCase();
    setState(() => _isLoading = true);

    final ok = await ref.read(authProvider.notifier).requestMagicCode(email);

    if (!mounted) return;
    setState(() => _isLoading = false);

    if (ok) {
      context.push('${AppRoutes.magicLinkCode}?email=${Uri.encodeQueryComponent(email)}');
    } else {
      final error =
          ref.read(authProvider).error ?? 'Could not send code. Please try again.';
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(error),
          behavior: SnackBarBehavior.floating,
          backgroundColor: AppColors.danger600,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.surface,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(LucideIcons.chevronLeft),
          onPressed: () => context.pop(),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: AppSpacing.page,
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: 20),
                Container(
                  width: 64,
                  height: 64,
                  decoration: BoxDecoration(
                    color: AppColors.primary100,
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: const Icon(
                    LucideIcons.mail,
                    size: 32,
                    color: AppColors.primary600,
                  ),
                ),
                const SizedBox(height: 24),
                Text('Sign in with email', style: AppTypography.h1),
                const SizedBox(height: 8),
                Text(
                  "Enter your email and we'll send you a 6-digit code to sign in. No password needed.",
                  style: AppTypography.body.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
                const SizedBox(height: 32),
                FloatingLabelInput(
                  label: 'Email',
                  hint: 'you@company.com',
                  controller: _emailController,
                  keyboardType: TextInputType.emailAddress,
                  prefixIcon: LucideIcons.mail,
                  textInputAction: TextInputAction.done,
                  onSubmitted: (_) => _handleSubmit(),
                  validator: (value) {
                    if (value == null || value.trim().isEmpty) {
                      return 'Email is required';
                    }
                    if (!value.contains('@') || !value.contains('.')) {
                      return 'Please enter a valid email';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 24),
                PrimaryButton(
                  label: 'Send code',
                  onPressed: _isLoading ? null : _handleSubmit,
                  isLoading: _isLoading,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
