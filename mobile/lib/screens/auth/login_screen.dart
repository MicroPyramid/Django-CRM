import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';
import 'package:url_launcher/url_launcher.dart';
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

  final List<TapGestureRecognizer> _linkRecognizers = [];

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
    for (final r in _linkRecognizers) {
      r.dispose();
    }
    super.dispose();
  }

  Future<void> _openUrl(String url) async {
    final uri = Uri.parse(url);
    if (!await launchUrl(uri, mode: LaunchMode.externalApplication)) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Could not open $url'),
            behavior: SnackBarBehavior.floating,
            backgroundColor: AppColors.danger600,
          ),
        );
      }
    }
  }

  TapGestureRecognizer _recognizerFor(String url) {
    final r = TapGestureRecognizer()..onTap = () => _openUrl(url);
    _linkRecognizers.add(r);
    return r;
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
        child: LayoutBuilder(
          builder: (context, constraints) {
            return SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: ConstrainedBox(
                constraints: BoxConstraints(minHeight: constraints.maxHeight),
                child: IntrinsicHeight(
                  child: FadeTransition(
                    opacity: _fadeAnimation,
                    child: SlideTransition(
                      position: _slideAnimation,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          const Spacer(flex: 3),
                          _buildHeader(),
                          const Spacer(flex: 4),
                          _buildGoogleButton(),
                          const SizedBox(height: 12),
                          _buildMagicLinkButton(),
                          const Spacer(flex: 2),
                          _buildFooter(),
                          const SizedBox(height: 8),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            );
          },
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Container(
          width: 88,
          height: 88,
          decoration: BoxDecoration(
            color: AppColors.gray50,
            borderRadius: BorderRadius.circular(22),
            border: Border.all(color: AppColors.borderLight),
          ),
          padding: const EdgeInsets.all(8),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(14),
            child: Image.asset('assets/icon/icon.png', fit: BoxFit.cover),
          ),
        ),
        const SizedBox(height: 28),
        Text(
          'Your pipeline,\nin your pocket.',
          textAlign: TextAlign.center,
          style: AppTypography.h1.copyWith(letterSpacing: -0.5, height: 1.15),
        ),
        const SizedBox(height: 10),
        Text(
          'Sign in to BottleCRM.',
          textAlign: TextAlign.center,
          style: AppTypography.body.copyWith(
            color: AppColors.textSecondary,
            height: 1.4,
          ),
        ),
      ],
    );
  }

  Widget _buildGoogleButton() {
    return SizedBox(
      width: double.infinity,
      height: 52,
      child: ElevatedButton(
        onPressed: _isLoading ? null : _handleGoogleSignIn,
        style: ButtonStyle(
          backgroundColor: WidgetStateProperty.resolveWith((states) {
            if (states.contains(WidgetState.pressed)) return AppColors.gray700;
            return AppColors.gray900;
          }),
          foregroundColor: const WidgetStatePropertyAll(Colors.white),
          overlayColor: const WidgetStatePropertyAll(Colors.transparent),
          elevation: const WidgetStatePropertyAll(0),
          shape: WidgetStatePropertyAll(
            RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          ),
        ),
        child: _isLoading
            ? const SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                ),
              )
            : Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Container(
                    width: 22,
                    height: 22,
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
                          fontSize: 14,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Text(
                    'Continue with Google',
                    style: AppTypography.button.copyWith(color: Colors.white),
                  ),
                ],
              ),
      ),
    );
  }

  Widget _buildMagicLinkButton() {
    return SizedBox(
      width: double.infinity,
      height: 52,
      child: OutlinedButton.icon(
        onPressed: _isLoading
            ? null
            : () => context.push(AppRoutes.magicLinkEmail),
        icon: Icon(
          LucideIcons.mail,
          size: 18,
          color: _isLoading ? AppColors.textTertiary : AppColors.textPrimary,
        ),
        label: Text(
          'Sign in with email code',
          style: AppTypography.button.copyWith(
            color: _isLoading ? AppColors.textTertiary : AppColors.textPrimary,
          ),
        ),
        style: ButtonStyle(
          side: WidgetStateProperty.resolveWith((states) {
            if (states.contains(WidgetState.pressed)) {
              return const BorderSide(color: AppColors.gray400);
            }
            return const BorderSide(color: AppColors.border);
          }),
          backgroundColor: WidgetStateProperty.resolveWith((states) {
            if (states.contains(WidgetState.pressed)) return AppColors.gray50;
            return Colors.transparent;
          }),
          overlayColor: const WidgetStatePropertyAll(Colors.transparent),
          shape: WidgetStatePropertyAll(
            RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          ),
        ),
      ),
    );
  }

  Widget _buildFooter() {
    final linkStyle = TextStyle(
      color: AppColors.textSecondary,
      fontWeight: FontWeight.w500,
      decoration: TextDecoration.underline,
      decorationColor: AppColors.borderLight,
    );
    return Text.rich(
      TextSpan(
        style: AppTypography.caption.copyWith(color: AppColors.textTertiary),
        children: [
          const TextSpan(text: 'By continuing you agree to our '),
          TextSpan(
            text: 'Terms',
            style: linkStyle,
            recognizer: _recognizerFor('https://bottlecrm.io/terms-of-service'),
          ),
          const TextSpan(text: ' and '),
          TextSpan(
            text: 'Privacy Policy',
            style: linkStyle,
            recognizer: _recognizerFor('https://bottlecrm.io/privacy-policy'),
          ),
        ],
      ),
      textAlign: TextAlign.center,
    );
  }
}
