import 'package:flutter/material.dart';

/// BottleCRM Spacing & Layout System
/// Optimized for CRM-style dense, data-heavy interfaces
/// Based on a 4px base unit system for consistent rhythm
class AppSpacing {
  AppSpacing._();

  // ============================================
  // SPACING SCALE (4px base unit) - CRM Dense
  // ============================================
  static const double xs = 2.0;    // 2px - Micro spacing
  static const double sm = 4.0;    // 4px - Tight spacing
  static const double md = 8.0;    // 8px - Small spacing
  static const double lg = 12.0;   // 12px - Default spacing
  static const double xl = 16.0;   // 16px - Medium spacing
  static const double xxl = 20.0;  // 20px - Large spacing
  static const double xxxl = 24.0; // 24px - Section spacing

  // ============================================
  // SEMANTIC SPACING - CRM Optimized
  // ============================================

  /// Page horizontal padding
  static const double pagePadding = lg; // 12px

  /// Card internal padding
  static const double cardPadding = lg; // 12px

  /// Card margin/gap between cards
  static const double cardMargin = md; // 8px

  /// Section gap (between major sections)
  static const double sectionGap = xl; // 16px

  /// Item gap (between list items)
  static const double itemGap = md; // 8px

  /// Small item gap
  static const double itemGapSmall = sm; // 4px

  // ============================================
  // EDGE INSETS PRESETS
  // ============================================

  /// Standard page padding (horizontal only)
  static const EdgeInsets pageHorizontal = EdgeInsets.symmetric(horizontal: lg);

  /// Standard page padding (all sides)
  static const EdgeInsets page = EdgeInsets.all(lg);

  /// Card padding
  static const EdgeInsets card = EdgeInsets.all(lg);

  /// Form field padding
  static const EdgeInsets field = EdgeInsets.symmetric(vertical: sm);

  /// Button padding (large)
  static const EdgeInsets buttonLarge = EdgeInsets.symmetric(
    horizontal: xxl,
    vertical: md,
  );

  /// Button padding (medium)
  static const EdgeInsets buttonMedium = EdgeInsets.symmetric(
    horizontal: xl,
    vertical: md,
  );

  /// Button padding (small)
  static const EdgeInsets buttonSmall = EdgeInsets.symmetric(
    horizontal: lg,
    vertical: sm,
  );

  /// Section header padding
  static const EdgeInsets sectionHeader = EdgeInsets.only(
    left: lg,
    right: lg,
    top: xl,
    bottom: md,
  );

  /// List item padding
  static const EdgeInsets listItem = EdgeInsets.symmetric(
    horizontal: lg,
    vertical: md,
  );

  /// Chip/badge padding
  static const EdgeInsets chip = EdgeInsets.symmetric(
    horizontal: md,
    vertical: xs,
  );

  /// Input content padding
  static const EdgeInsets inputContent = EdgeInsets.symmetric(
    horizontal: lg,
    vertical: lg,
  );
}

/// BottleCRM Layout Constants - CRM Optimized
class AppLayout {
  AppLayout._();

  // ============================================
  // SCREEN CONSTRAINTS
  // ============================================
  static const double maxWidth = 430.0;
  static const double minTouchTarget = 40.0;

  // ============================================
  // COMPONENT HEIGHTS - CRM Dense
  // ============================================
  static const double appBarHeight = 52.0;
  static const double bottomNavHeight = 56.0;
  static const double inputHeight = 44.0;
  static const double buttonHeightLarge = 44.0;
  static const double buttonHeightMedium = 40.0;
  static const double buttonHeightSmall = 32.0;
  static const double fabSize = 52.0;
  static const double fabMiniSize = 44.0;
  static const double tabBarHeight = 44.0;
  static const double searchBarHeight = 40.0;
  static const double filterChipHeight = 32.0;

  // ============================================
  // BORDER RADIUS - Tighter for CRM
  // ============================================
  static const double radiusXs = 4.0;
  static const double radiusSm = 6.0;
  static const double radiusMd = 8.0;
  static const double radiusLg = 10.0;
  static const double radiusXl = 12.0;
  static const double radiusXxl = 16.0;
  static const double radiusFull = 9999.0;

  // ============================================
  // BORDER RADIUS PRESETS
  // ============================================
  static final BorderRadius borderRadiusXs = BorderRadius.circular(radiusXs);
  static final BorderRadius borderRadiusSm = BorderRadius.circular(radiusSm);
  static final BorderRadius borderRadiusMd = BorderRadius.circular(radiusMd);
  static final BorderRadius borderRadiusLg = BorderRadius.circular(radiusLg);
  static final BorderRadius borderRadiusXl = BorderRadius.circular(radiusXl);
  static final BorderRadius borderRadiusXxl = BorderRadius.circular(radiusXxl);
  static final BorderRadius borderRadiusFull = BorderRadius.circular(radiusFull);

  // ============================================
  // ICON SIZES
  // ============================================
  static const double iconXs = 14.0;
  static const double iconSm = 18.0;
  static const double iconMd = 20.0;
  static const double iconLg = 24.0;
  static const double iconXl = 32.0;
  static const double iconXxl = 48.0;

  // ============================================
  // AVATAR SIZES - CRM Compact
  // ============================================
  static const double avatarXs = 20.0;
  static const double avatarSm = 28.0;
  static const double avatarMd = 32.0;
  static const double avatarLg = 40.0;
  static const double avatarXl = 56.0;
  static const double avatarXxl = 72.0;

  // ============================================
  // SHADOWS
  // ============================================
  static List<BoxShadow> get shadowSm => [
        BoxShadow(
          color: Colors.black.withValues(alpha: 0.04),
          blurRadius: 4,
          offset: const Offset(0, 1),
        ),
      ];

  static List<BoxShadow> get shadowMd => [
        BoxShadow(
          color: Colors.black.withValues(alpha: 0.06),
          blurRadius: 8,
          offset: const Offset(0, 2),
        ),
      ];

  static List<BoxShadow> get shadowLg => [
        BoxShadow(
          color: Colors.black.withValues(alpha: 0.08),
          blurRadius: 16,
          offset: const Offset(0, 4),
        ),
      ];

  static List<BoxShadow> get shadowXl => [
        BoxShadow(
          color: Colors.black.withValues(alpha: 0.12),
          blurRadius: 24,
          offset: const Offset(0, 8),
        ),
      ];
}

/// BottleCRM Animation Constants
class AppDurations {
  AppDurations._();

  static const Duration fast = Duration(milliseconds: 150);
  static const Duration normal = Duration(milliseconds: 200);
  static const Duration slow = Duration(milliseconds: 300);
  static const Duration slower = Duration(milliseconds: 500);
  static const Duration splash = Duration(milliseconds: 2500);
}

/// Animation Curves
class AppCurves {
  AppCurves._();

  static const Curve defaultCurve = Curves.easeInOut;
  static const Curve enterCurve = Curves.easeOut;
  static const Curve exitCurve = Curves.easeIn;
  static const Curve bounceCurve = Curves.elasticOut;
  static const Curve sharpCurve = Curves.easeInOutCubic;
}
