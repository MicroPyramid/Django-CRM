import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'app_colors.dart';

/// BottleCRM Typography System
/// Using Plus Jakarta Sans - a modern, professional geometric sans-serif
/// that's distinctive yet highly readable for data-dense interfaces
class AppTypography {
  AppTypography._();

  // ============================================
  // DISPLAY & HEADINGS
  // ============================================

  /// Display - Hero text, large numbers
  /// 32px, Bold, 1.2 line height
  static TextStyle get display => GoogleFonts.plusJakartaSans(
        fontSize: 32,
        fontWeight: FontWeight.w700,
        height: 1.2,
        color: AppColors.textPrimary,
        letterSpacing: -0.5,
      );

  /// H1 - Main page titles
  /// 24px, Bold, 1.3 line height
  static TextStyle get h1 => GoogleFonts.plusJakartaSans(
        fontSize: 24,
        fontWeight: FontWeight.w700,
        height: 1.3,
        color: AppColors.textPrimary,
        letterSpacing: -0.3,
      );

  /// H2 - Section titles
  /// 20px, Semi-bold, 1.4 line height
  static TextStyle get h2 => GoogleFonts.plusJakartaSans(
        fontSize: 20,
        fontWeight: FontWeight.w600,
        height: 1.4,
        color: AppColors.textPrimary,
        letterSpacing: -0.2,
      );

  /// H3 - Card titles, subsections
  /// 18px, Semi-bold, 1.4 line height
  static TextStyle get h3 => GoogleFonts.plusJakartaSans(
        fontSize: 18,
        fontWeight: FontWeight.w600,
        height: 1.4,
        color: AppColors.textPrimary,
      );

  // ============================================
  // BODY TEXT
  // ============================================

  /// Body Large - Prominent body text
  /// 16px, Regular, 1.5 line height
  static TextStyle get bodyLarge => GoogleFonts.plusJakartaSans(
        fontSize: 16,
        fontWeight: FontWeight.w400,
        height: 1.5,
        color: AppColors.textPrimary,
      );

  /// Body - Standard body text
  /// 14px, Regular, 1.5 line height
  static TextStyle get body => GoogleFonts.plusJakartaSans(
        fontSize: 14,
        fontWeight: FontWeight.w400,
        height: 1.5,
        color: AppColors.textPrimary,
      );

  /// Body Small - Secondary body text
  /// 12px, Regular, 1.4 line height
  static TextStyle get bodySmall => GoogleFonts.plusJakartaSans(
        fontSize: 12,
        fontWeight: FontWeight.w400,
        height: 1.4,
        color: AppColors.textPrimary,
      );

  // ============================================
  // LABELS & UI TEXT
  // ============================================

  /// Label - Input labels, button text
  /// 14px, Medium, 1.4 line height
  static TextStyle get label => GoogleFonts.plusJakartaSans(
        fontSize: 14,
        fontWeight: FontWeight.w500,
        height: 1.4,
        color: AppColors.textPrimary,
      );

  /// Label Small - Small labels, badges
  /// 12px, Medium, 1.3 line height
  static TextStyle get labelSmall => GoogleFonts.plusJakartaSans(
        fontSize: 12,
        fontWeight: FontWeight.w500,
        height: 1.3,
        color: AppColors.textPrimary,
      );

  // ============================================
  // CAPTIONS & AUXILIARY
  // ============================================

  /// Caption - Timestamps, helper text
  /// 12px, Regular, 1.3 line height, Secondary color
  static TextStyle get caption => GoogleFonts.plusJakartaSans(
        fontSize: 12,
        fontWeight: FontWeight.w400,
        height: 1.3,
        color: AppColors.textSecondary,
      );

  /// Overline - Section headers, category labels
  /// 12px, Semi-bold, 0.5 letter spacing, uppercase
  static TextStyle get overline => GoogleFonts.plusJakartaSans(
        fontSize: 12,
        fontWeight: FontWeight.w600,
        height: 1.3,
        letterSpacing: 0.5,
        color: AppColors.textSecondary,
      );

  // ============================================
  // NUMBERS & DATA
  // ============================================

  /// Number Large - KPI values, large amounts
  /// 28px, Bold, Tabular figures
  static TextStyle get numberLarge => GoogleFonts.plusJakartaSans(
        fontSize: 28,
        fontWeight: FontWeight.w700,
        height: 1.2,
        color: AppColors.textPrimary,
        fontFeatures: const [FontFeature.tabularFigures()],
      );

  /// Number - Standard numeric values
  /// 16px, Semi-bold, Tabular figures
  static TextStyle get number => GoogleFonts.plusJakartaSans(
        fontSize: 16,
        fontWeight: FontWeight.w600,
        height: 1.3,
        color: AppColors.textPrimary,
        fontFeatures: const [FontFeature.tabularFigures()],
      );

  /// Number Small - Small numeric values, percentages
  /// 14px, Medium, Tabular figures
  static TextStyle get numberSmall => GoogleFonts.plusJakartaSans(
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
  /// 16px, Semi-bold
  static TextStyle get buttonLarge => GoogleFonts.plusJakartaSans(
        fontSize: 16,
        fontWeight: FontWeight.w600,
        height: 1.0,
        color: Colors.white,
      );

  /// Button - Standard buttons
  /// 14px, Semi-bold
  static TextStyle get button => GoogleFonts.plusJakartaSans(
        fontSize: 14,
        fontWeight: FontWeight.w600,
        height: 1.0,
        color: Colors.white,
      );

  /// Button Small - Compact buttons
  /// 12px, Semi-bold
  static TextStyle get buttonSmall => GoogleFonts.plusJakartaSans(
        fontSize: 12,
        fontWeight: FontWeight.w600,
        height: 1.0,
        color: Colors.white,
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
