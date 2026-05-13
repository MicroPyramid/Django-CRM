import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../../core/theme/theme.dart';
import '../../providers/auth_provider.dart';
import '../../routes/app_router.dart';

/// Login Screen
///
/// Two passwordless paths: Google Sign-In or magic-link OTP code.
class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen>
    with SingleTickerProviderStateMixin {
  bool _isLoading = false;

  late AnimationController _animController;
  late Animation<double> _fadeAnimation;
  late Animation<Offset> _slideAnimation;

  @override
  void initState() {
    super.initState();
    _animController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    );

    _fadeAnimation = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(
        parent: _animController,
        curve: const Interval(0, 0.6, curve: Curves.easeOut),
      ),
    );

    _slideAnimation = Tween<Offset>(
      begin: const Offset(0, 0.1),
      end: Offset.zero,
    ).animate(CurvedAnimation(parent: _animController, curve: Curves.easeOut));

    _animController.forward();
  }

  @override
  void dispose() {
    _animController.dispose();
    super.dispose();
  }

  Future<void> _handleGoogleSignIn() async {
    setState(() => _isLoading = true);

    final success = await ref.read(authProvider.notifier).signInWithGoogle();

    if (mounted) {
      setState(() => _isLoading = false);

      if (success) {
        final authState = ref.read(authProvider);
        if (authState.needsOrgSelection) {
          context.go(AppRoutes.orgSelection);
        } else {
          context.go(AppRoutes.dashboard);
        }
      } else {
        final error = ref.read(authProvider).error;
        if (error != null) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(error),
              behavior: SnackBarBehavior.floating,
              backgroundColor: AppColors.danger600,
            ),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.surface,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: AppSpacing.page,
          child: FadeTransition(
            opacity: _fadeAnimation,
            child: SlideTransition(
              position: _slideAnimation,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SizedBox(height: 40),
                  _buildHeader(),
                  const SizedBox(height: 48),
                  _buildGoogleButton(),
                  const SizedBox(height: 12),
                  _buildMagicLinkButton(),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        ClipRRect(
          borderRadius: BorderRadius.circular(16),
          child: Image.asset(
            'assets/icon/icon.png',
            width: 56,
            height: 56,
            fit: BoxFit.cover,
          ),
        ),
        const SizedBox(height: 24),
        Text('Welcome back', style: AppTypography.h1),
        const SizedBox(height: 8),
        Text(
          'Sign in to continue to BottleCRM',
          style: AppTypography.body.copyWith(color: AppColors.textSecondary),
        ),
      ],
    );
  }

  Widget _buildGoogleButton() {
    return SizedBox(
      width: double.infinity,
      height: AppLayout.buttonHeightLarge,
      child: OutlinedButton.icon(
        onPressed: _isLoading ? null : _handleGoogleSignIn,
        icon: Container(
          width: 24,
          height: 24,
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(4),
          ),
          child: Center(
            child: Text(
              'G',
              style: TextStyle(
                color: Colors.red.shade600,
                fontWeight: FontWeight.bold,
                fontSize: 16,
              ),
            ),
          ),
        ),
        label: Text(
          'Continue with Google',
          style: AppTypography.button.copyWith(color: AppColors.textPrimary),
        ),
        style: OutlinedButton.styleFrom(
          side: const BorderSide(color: AppColors.border),
          shape: RoundedRectangleBorder(borderRadius: AppLayout.borderRadiusMd),
        ),
      ),
    );
  }

  Widget _buildMagicLinkButton() {
    return SizedBox(
      width: double.infinity,
      height: AppLayout.buttonHeightLarge,
      child: OutlinedButton.icon(
        onPressed: _isLoading
            ? null
            : () => context.push(AppRoutes.magicLinkEmail),
        icon: const Icon(
          LucideIcons.mail,
          size: 20,
          color: AppColors.textPrimary,
        ),
        label: Text(
          'Sign in with email code',
          style: AppTypography.button.copyWith(color: AppColors.textPrimary),
        ),
        style: OutlinedButton.styleFrom(
          side: const BorderSide(color: AppColors.border),
          shape: RoundedRectangleBorder(borderRadius: AppLayout.borderRadiusMd),
        ),
      ),
    );
  }
}
