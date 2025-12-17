import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../../core/theme/theme.dart';
import '../../routes/app_router.dart';
import '../../widgets/common/common.dart';

/// Onboarding Screen
/// 3-slide feature introduction carousel
class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key});

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final PageController _pageController = PageController();
  int _currentPage = 0;

  final List<_OnboardingSlide> _slides = [
    _OnboardingSlide(
      icon: LucideIcons.users,
      iconColor: AppColors.primary600,
      backgroundColor: AppColors.primary100,
      title: 'Track Your Leads',
      description:
          'Manage and organize all your leads in one place. Never miss a follow-up again.',
    ),
    _OnboardingSlide(
      icon: LucideIcons.trendingUp,
      iconColor: AppColors.success600,
      backgroundColor: AppColors.success100,
      title: 'Close More Deals',
      description:
          'Visualize your sales pipeline and move deals through stages effortlessly.',
    ),
    _OnboardingSlide(
      icon: LucideIcons.calendar,
      iconColor: AppColors.warning600,
      backgroundColor: AppColors.warning100,
      title: 'Stay Organized',
      description:
          'Keep track of tasks, meetings, and deadlines. Boost your productivity.',
    ),
  ];

  void _goToNextPage() {
    if (_currentPage < _slides.length - 1) {
      _pageController.nextPage(
        duration: AppDurations.slow,
        curve: AppCurves.defaultCurve,
      );
    } else {
      _completeOnboarding();
    }
  }

  void _completeOnboarding() {
    context.go(AppRoutes.login);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.surface,
      body: SafeArea(
        child: Column(
          children: [
            // Skip Button
            Align(
              alignment: Alignment.centerRight,
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: GestureDetector(
                  onTap: _completeOnboarding,
                  child: Text(
                    'Skip',
                    style: AppTypography.label.copyWith(
                      color: AppColors.textSecondary,
                    ),
                  ),
                ),
              ),
            ),

            // Page View
            Expanded(
              child: PageView.builder(
                controller: _pageController,
                onPageChanged: (index) {
                  setState(() => _currentPage = index);
                },
                itemCount: _slides.length,
                itemBuilder: (context, index) {
                  return _buildSlide(_slides[index], index);
                },
              ),
            ),

            // Bottom Section
            Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                children: [
                  // Dot Indicators
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: List.generate(
                      _slides.length,
                      (index) => _buildDot(index),
                    ),
                  ),

                  const SizedBox(height: 32),

                  // Action Button
                  PrimaryButton(
                    label: _currentPage == _slides.length - 1
                        ? 'Get Started'
                        : 'Next',
                    onPressed: _goToNextPage,
                    icon: _currentPage == _slides.length - 1
                        ? LucideIcons.arrowRight
                        : null,
                    iconRight: true,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSlide(_OnboardingSlide slide, int index) {
    return TweenAnimationBuilder<double>(
      tween: Tween(begin: 0, end: 1),
      duration: AppDurations.slow,
      builder: (context, value, child) {
        return Opacity(
          opacity: value,
          child: Transform.translate(
            offset: Offset(0, 20 * (1 - value)),
            child: child,
          ),
        );
      },
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // Illustration
            _buildIllustration(slide),

            const SizedBox(height: 48),

            // Title
            Text(
              slide.title,
              style: AppTypography.h1.copyWith(
                fontSize: 28,
              ),
              textAlign: TextAlign.center,
            ),

            const SizedBox(height: 16),

            // Description
            Text(
              slide.description,
              style: AppTypography.body.copyWith(
                color: AppColors.textSecondary,
                height: 1.6,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildIllustration(_OnboardingSlide slide) {
    return Stack(
      alignment: Alignment.center,
      children: [
        // Background decorative circles
        Container(
          width: 280,
          height: 280,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: slide.backgroundColor.withValues(alpha: 0.3),
          ),
        ),
        Container(
          width: 220,
          height: 220,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: slide.backgroundColor.withValues(alpha: 0.5),
          ),
        ),
        // Main circle with icon
        Container(
          width: 160,
          height: 160,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: slide.backgroundColor,
            boxShadow: [
              BoxShadow(
                color: slide.iconColor.withValues(alpha: 0.3),
                blurRadius: 30,
                offset: const Offset(0, 10),
              ),
            ],
          ),
          child: Icon(
            slide.icon,
            size: 72,
            color: slide.iconColor,
          ),
        ),
        // Floating accent elements
        Positioned(
          top: 40,
          right: 50,
          child: _buildFloatingElement(
            size: 20,
            color: slide.iconColor.withValues(alpha: 0.6),
          ),
        ),
        Positioned(
          bottom: 60,
          left: 40,
          child: _buildFloatingElement(
            size: 16,
            color: slide.iconColor.withValues(alpha: 0.4),
          ),
        ),
        Positioned(
          top: 80,
          left: 60,
          child: _buildFloatingElement(
            size: 12,
            color: slide.iconColor.withValues(alpha: 0.5),
            isSquare: true,
          ),
        ),
      ],
    );
  }

  Widget _buildFloatingElement({
    required double size,
    required Color color,
    bool isSquare = false,
  }) {
    return TweenAnimationBuilder<double>(
      tween: Tween(begin: 0, end: 1),
      duration: const Duration(milliseconds: 1500),
      curve: Curves.elasticOut,
      builder: (context, value, child) {
        return Transform.scale(
          scale: value,
          child: child,
        );
      },
      child: Container(
        width: size,
        height: size,
        decoration: BoxDecoration(
          color: color,
          borderRadius:
              isSquare ? BorderRadius.circular(4) : BorderRadius.circular(size),
        ),
      ),
    );
  }

  Widget _buildDot(int index) {
    final isActive = index == _currentPage;

    return GestureDetector(
      onTap: () {
        _pageController.animateToPage(
          index,
          duration: AppDurations.slow,
          curve: AppCurves.defaultCurve,
        );
      },
      child: AnimatedContainer(
        duration: AppDurations.normal,
        curve: AppCurves.defaultCurve,
        margin: const EdgeInsets.symmetric(horizontal: 4),
        height: 8,
        width: isActive ? 24 : 8,
        decoration: BoxDecoration(
          color: isActive ? AppColors.primary600 : AppColors.gray300,
          borderRadius: BorderRadius.circular(4),
        ),
      ),
    );
  }
}

class _OnboardingSlide {
  final IconData icon;
  final Color iconColor;
  final Color backgroundColor;
  final String title;
  final String description;

  const _OnboardingSlide({
    required this.icon,
    required this.iconColor,
    required this.backgroundColor,
    required this.title,
    required this.description,
  });
}
