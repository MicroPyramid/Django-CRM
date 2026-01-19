import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'app_colors.dart';

/// BottleCRM Typography System
/// Using Inter - a font designed specifically for screens
/// with excellent readability at small sizes
class AppTypography {
  AppTypography._();

  // ============================================
  // DISPLAY & HEADINGS
  // ============================================

  /// Display - KPIs, large numbers, hero text
  /// 28px, Bold, 1.2 line height
  static TextStyle get display => GoogleFonts.inter(
        fontSize: 28,
        fontWeight: FontWeight.w700,
        height: 1.2,
        color: AppColors.textPrimary,
        letterSpacing: -0.5,
      );

  /// H1 - Main page titles
  /// 22px, Semi-bold, 1.3 line height
  static TextStyle get h1 => GoogleFonts.inter(
        fontSize: 22,
        fontWeight: FontWeight.w600,
        height: 1.3,
        color: AppColors.textPrimary,
        letterSpacing: -0.3,
      );

  /// H2 - Section titles
  /// 18px, Semi-bold, 1.4 line height
  static TextStyle get h2 => GoogleFonts.inter(
        fontSize: 18,
        fontWeight: FontWeight.w600,
        height: 1.4,
        color: AppColors.textPrimary,
        letterSpacing: -0.2,
      );

  /// H3 - Card titles, subsections
  /// 16px, Semi-bold, 1.4 line height
  static TextStyle get h3 => GoogleFonts.inter(
        fontSize: 16,
        fontWeight: FontWeight.w600,
        height: 1.4,
        color: AppColors.textPrimary,
      );

  // ============================================
  // BODY TEXT
  // ============================================

  /// Body Large - Important body text
  /// 16px, Regular, 1.5 line height
  static TextStyle get bodyLarge => GoogleFonts.inter(
        fontSize: 16,
        fontWeight: FontWeight.w400,
        height: 1.5,
        color: AppColors.textPrimary,
      );

  /// Body - Default body text
  /// 15px, Regular, 1.5 line height
  static TextStyle get body => GoogleFonts.inter(
        fontSize: 15,
        fontWeight: FontWeight.w400,
        height: 1.5,
        color: AppColors.textPrimary,
      );

  /// Body Small - Secondary body text
  /// 14px, Regular, 1.4 line height
  static TextStyle get bodySmall => GoogleFonts.inter(
        fontSize: 14,
        fontWeight: FontWeight.w400,
        height: 1.4,
        color: AppColors.textPrimary,
      );

  // ============================================
  // LABELS & UI TEXT
  // ============================================

  /// Label - Input labels, list item titles
  /// 15px, Medium, 1.4 line height
  static TextStyle get label => GoogleFonts.inter(
        fontSize: 15,
        fontWeight: FontWeight.w500,
        height: 1.4,
        color: AppColors.textPrimary,
      );

  /// Label Small - Small labels, nav items
  /// 13px, Medium, 1.3 line height
  static TextStyle get labelSmall => GoogleFonts.inter(
        fontSize: 13,
        fontWeight: FontWeight.w500,
        height: 1.3,
        color: AppColors.textPrimary,
      );

  // ============================================
  // CAPTIONS & AUXILIARY
  // ============================================

  /// Caption - Timestamps, helper text
  /// 12px, Regular, 1.3 line height, Secondary color
  static TextStyle get caption => GoogleFonts.inter(
        fontSize: 12,
        fontWeight: FontWeight.w400,
        height: 1.3,
        color: AppColors.textSecondary,
      );

  /// Overline - Section labels, category headers
  /// 11px, Semi-bold, 0.5 letter spacing
  static TextStyle get overline => GoogleFonts.inter(
        fontSize: 11,
        fontWeight: FontWeight.w600,
        height: 1.3,
        letterSpacing: 0.5,
        color: AppColors.textSecondary,
      );

  // ============================================
  // NUMBERS & DATA
  // ============================================

  /// Number Large - Dashboard KPIs, large metrics
  /// 28px, Bold, Tabular figures
  static TextStyle get numberLarge => GoogleFonts.inter(
        fontSize: 28,
        fontWeight: FontWeight.w700,
        height: 1.2,
        color: AppColors.textPrimary,
        fontFeatures: const [FontFeature.tabularFigures()],
      );

  /// Number Medium - Card metrics
  /// 20px, Semi-bold, Tabular figures
  static TextStyle get numberMedium => GoogleFonts.inter(
        fontSize: 20,
        fontWeight: FontWeight.w600,
        height: 1.3,
        color: AppColors.textPrimary,
        fontFeatures: const [FontFeature.tabularFigures()],
      );

  /// Number Small - Inline numbers
  /// 14px, Medium, Tabular figures
  static TextStyle get numberSmall => GoogleFonts.inter(
        fontSize: 14,
        fontWeight: FontWeight.w500,
        height: 1.3,
        color: AppColors.textPrimary,
        fontFeatures: const [FontFeature.tabularFigures()],
      );

  // ============================================
  // BUTTON TEXT
  // ============================================

  /// Button Large - Primary action buttons
  /// 15px, Semi-bold
  static TextStyle get buttonLarge => GoogleFonts.inter(
        fontSize: 15,
        fontWeight: FontWeight.w600,
        height: 1.0,
        color: Colors.white,
      );

  /// Button - Standard buttons
  /// 14px, Semi-bold
  static TextStyle get button => GoogleFonts.inter(
        fontSize: 14,
        fontWeight: FontWeight.w600,
        height: 1.0,
        color: Colors.white,
      );

  /// Button Small - Compact buttons
  /// 13px, Semi-bold
  static TextStyle get buttonSmall => GoogleFonts.inter(
        fontSize: 13,
        fontWeight: FontWeight.w600,
        height: 1.0,
        color: Colors.white,
      );

  // ============================================
  // LINK TEXT
  // ============================================

  /// Link - Clickable text links
  /// 14px, Medium, Primary color
  static TextStyle get link => GoogleFonts.inter(
        fontSize: 14,
        fontWeight: FontWeight.w500,
        height: 1.4,
        color: AppColors.primary600,
      );

  /// Link Small - Small clickable links (e.g., "View all")
  /// 13px, Medium, Primary color
  static TextStyle get linkSmall => GoogleFonts.inter(
        fontSize: 13,
        fontWeight: FontWeight.w500,
        height: 1.3,
        color: AppColors.primary600,
      );

  // ============================================
  // HELPER METHODS
  // ============================================

  /// Get base text theme for Material theme
  static TextTheme get textTheme => TextTheme(
        displayLarge: display,
        displayMedium: h1,
        displaySmall: h2,
        headlineLarge: h1,
        headlineMedium: h2,
        headlineSmall: h3,
        titleLarge: h3,
        titleMedium: label,
        titleSmall: labelSmall,
        bodyLarge: bodyLarge,
        bodyMedium: body,
        bodySmall: bodySmall,
        labelLarge: buttonLarge,
        labelMedium: button,
        labelSmall: buttonSmall,
      );
}
