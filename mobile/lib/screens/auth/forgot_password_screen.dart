import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../../core/theme/theme.dart';
import '../../widgets/common/common.dart';

/// Forgot Password Screen
/// Password reset flow with email input and success confirmation
class ForgotPasswordScreen extends StatefulWidget {
  const ForgotPasswordScreen({super.key});

  @override
  State<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen>
    with SingleTickerProviderStateMixin {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  bool _isLoading = false;
  bool _submitted = false;

  late AnimationController _animController;

  @override
  void initState() {
    super.initState();
    _animController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 400),
    );
  }

  @override
  void dispose() {
    _animController.dispose();
    _emailController.dispose();
    super.dispose();
  }

  Future<void> _handleSubmit() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);

    // Simulate API call
    await Future.delayed(const Duration(milliseconds: 1500));

    if (mounted) {
      setState(() {
        _isLoading = false;
        _submitted = true;
      });
      _animController.forward();
    }
  }

  void _handleTryAgain() {
    setState(() => _submitted = false);
    _animController.reverse();
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
          child: AnimatedSwitcher(
            duration: AppDurations.slow,
            switchInCurve: Curves.easeOut,
            switchOutCurve: Curves.easeIn,
            child: _submitted
                ? _buildSuccessState()
                : _buildFormState(),
          ),
        ),
      ),
    );
  }

  Widget _buildFormState() {
    return Form(
      key: _formKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: 20),

          // Icon
          Container(
            width: 64,
            height: 64,
            decoration: BoxDecoration(
              color: AppColors.primary100,
              borderRadius: BorderRadius.circular(16),
            ),
            child: const Icon(
              LucideIcons.keyRound,
              size: 32,
              color: AppColors.primary600,
            ),
          ),

          const SizedBox(height: 24),

          // Title
          Text(
            'Reset Password',
            style: AppTypography.h1,
          ),

          const SizedBox(height: 8),

          // Description
          Text(
            "Enter your email address and we'll send you instructions to reset your password.",
            style: AppTypography.body.copyWith(
              color: AppColors.textSecondary,
              height: 1.5,
            ),
          ),

          const SizedBox(height: 32),

          // Email Field
          FloatingLabelInput(
            label: 'Email address',
            hint: 'Enter your email',
            controller: _emailController,
            keyboardType: TextInputType.emailAddress,
            prefixIcon: LucideIcons.mail,
            textInputAction: TextInputAction.done,
            onSubmitted: (_) => _handleSubmit(),
            validator: (value) {
              if (value == null || value.isEmpty) {
                return 'Email is required';
              }
              if (!value.contains('@') || !value.contains('.')) {
                return 'Please enter a valid email address';
              }
              return null;
            },
          ),

          const SizedBox(height: 24),

          // Submit Button
          PrimaryButton(
            label: 'Send Reset Link',
            onPressed: _isLoading ? null : _handleSubmit,
            isLoading: _isLoading,
          ),

          const SizedBox(height: 24),

          // Back to Login
          Center(
            child: GestureDetector(
              onTap: () => context.pop(),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(
                    LucideIcons.chevronLeft,
                    size: 18,
                    color: AppColors.primary600,
                  ),
                  const SizedBox(width: 4),
                  Text(
                    'Back to Sign In',
                    style: AppTypography.label.copyWith(
                      color: AppColors.primary600,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSuccessState() {
    return TweenAnimationBuilder<double>(
      tween: Tween(begin: 0.8, end: 1.0),
      duration: AppDurations.slow,
      curve: Curves.elasticOut,
      builder: (context, scale, child) {
        return Transform.scale(
          scale: scale,
          child: child,
        );
      },
      child: Column(
        children: [
          const SizedBox(height: 40),

          // Success Icon
          Container(
            width: 80,
            height: 80,
            decoration: const BoxDecoration(
              color: AppColors.success100,
              shape: BoxShape.circle,
            ),
            child: const Icon(
              LucideIcons.checkCircle2,
              size: 40,
              color: AppColors.success600,
            ),
          ),

          const SizedBox(height: 24),

          // Title
          Text(
            'Check Your Email',
            style: AppTypography.h1,
            textAlign: TextAlign.center,
          ),

          const SizedBox(height: 8),

          // Description
          RichText(
            textAlign: TextAlign.center,
            text: TextSpan(
              style: AppTypography.body.copyWith(
                color: AppColors.textSecondary,
              ),
              children: [
                const TextSpan(
                  text: "We've sent password reset instructions to ",
                ),
                TextSpan(
                  text: _emailController.text,
                  style: const TextStyle(fontWeight: FontWeight.w600),
                ),
              ],
            ),
          ),

          const SizedBox(height: 32),

          // Open Email App Button
          PrimaryButton(
            label: 'Open Email App',
            onPressed: () {
              // Would use url_launcher to open email app
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('Opening email app...'),
                  behavior: SnackBarBehavior.floating,
                ),
              );
            },
          ),

          const SizedBox(height: 12),

          // Back to Sign In
          SecondaryButton(
            label: 'Back to Sign In',
            onPressed: () => context.pop(),
          ),

          const SizedBox(height: 32),

          // Help Text
          Text(
            "Didn't receive the email? Check your spam folder or",
            style: AppTypography.caption,
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 4),
          GestureDetector(
            onTap: _handleTryAgain,
            child: Text(
              'try again',
              style: AppTypography.label.copyWith(
                color: AppColors.primary600,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
