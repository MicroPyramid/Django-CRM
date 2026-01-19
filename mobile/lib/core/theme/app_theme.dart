import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'app_colors.dart';
import 'app_typography.dart';
import 'app_spacing.dart';

/// BottleCRM Theme Configuration
/// A cohesive, professional theme for the entire application
class AppTheme {
  AppTheme._();

  /// Light Theme (Primary)
  static ThemeData get light => ThemeData(
        useMaterial3: true,
        brightness: Brightness.light,

        // Color Scheme
        colorScheme: const ColorScheme.light(
          primary: AppColors.primary600,
          onPrimary: Colors.white,
          primaryContainer: AppColors.primary100,
          onPrimaryContainer: AppColors.primary900,
          secondary: AppColors.gray600,
          onSecondary: Colors.white,
          secondaryContainer: AppColors.gray100,
          onSecondaryContainer: AppColors.gray900,
          tertiary: AppColors.success600,
          onTertiary: Colors.white,
          tertiaryContainer: AppColors.success100,
          onTertiaryContainer: AppColors.success900,
          error: AppColors.danger600,
          onError: Colors.white,
          errorContainer: AppColors.danger100,
          onErrorContainer: AppColors.danger900,
          surface: AppColors.surface,
          onSurface: AppColors.textPrimary,
          surfaceContainerHighest: AppColors.surfaceDim,
          onSurfaceVariant: AppColors.textSecondary,
          outline: AppColors.border,
          outlineVariant: AppColors.borderLight,
        ),

        // Typography
        textTheme: AppTypography.textTheme,

        // Scaffold
        scaffoldBackgroundColor: AppColors.surfaceDim,

        // AppBar
        appBarTheme: AppBarTheme(
          elevation: 0,
          scrolledUnderElevation: 0,
          backgroundColor: AppColors.surface,
          foregroundColor: AppColors.textPrimary,
          surfaceTintColor: Colors.transparent,
          centerTitle: false,
          titleTextStyle: AppTypography.h3,
          toolbarHeight: AppLayout.appBarHeight,
          systemOverlayStyle: SystemUiOverlayStyle.dark,
          iconTheme: const IconThemeData(
            color: AppColors.textPrimary,
            size: AppLayout.iconMd,
          ),
        ),

        // Bottom Navigation Bar
        bottomNavigationBarTheme: const BottomNavigationBarThemeData(
          type: BottomNavigationBarType.fixed,
          backgroundColor: AppColors.surface,
          selectedItemColor: AppColors.primary600,
          unselectedItemColor: AppColors.gray400,
          elevation: 8,
          selectedLabelStyle: TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.w500,
          ),
          unselectedLabelStyle: TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.w400,
          ),
        ),

        // Navigation Bar (Material 3)
        navigationBarTheme: NavigationBarThemeData(
          height: AppLayout.bottomNavHeight,
          backgroundColor: AppColors.surface,
          indicatorColor: AppColors.primary100,
          labelTextStyle: WidgetStateProperty.resolveWith((states) {
            if (states.contains(WidgetState.selected)) {
              return AppTypography.labelSmall.copyWith(
                color: AppColors.primary600,
                fontWeight: FontWeight.w600,
              );
            }
            return AppTypography.labelSmall.copyWith(
              color: AppColors.gray500,
            );
          }),
          iconTheme: WidgetStateProperty.resolveWith((states) {
            if (states.contains(WidgetState.selected)) {
              return const IconThemeData(
                color: AppColors.primary600,
                size: AppLayout.iconMd,
              );
            }
            return const IconThemeData(
              color: AppColors.gray400,
              size: AppLayout.iconMd,
            );
          }),
        ),

        // Floating Action Button (Accent color like HubSpot)
        floatingActionButtonTheme: FloatingActionButtonThemeData(
          backgroundColor: AppColors.accent500,
          foregroundColor: Colors.white,
          elevation: 2,
          focusElevation: 4,
          hoverElevation: 4,
          highlightElevation: 4,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
        ),

        // Elevated Button
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            backgroundColor: AppColors.primary600,
            foregroundColor: Colors.white,
            elevation: 0,
            minimumSize: Size.fromHeight(AppLayout.buttonHeightLarge),
            padding: AppSpacing.buttonLarge,
            shape: RoundedRectangleBorder(
              borderRadius: AppLayout.borderRadiusMd,
            ),
            textStyle: AppTypography.buttonLarge,
          ),
        ),

        // Text Button
        textButtonTheme: TextButtonThemeData(
          style: TextButton.styleFrom(
            foregroundColor: AppColors.primary600,
            minimumSize: Size.fromHeight(AppLayout.buttonHeightMedium),
            padding: AppSpacing.buttonMedium,
            shape: RoundedRectangleBorder(
              borderRadius: AppLayout.borderRadiusMd,
            ),
            textStyle: AppTypography.button,
          ),
        ),

        // Outlined Button
        outlinedButtonTheme: OutlinedButtonThemeData(
          style: OutlinedButton.styleFrom(
            foregroundColor: AppColors.textPrimary,
            minimumSize: Size.fromHeight(AppLayout.buttonHeightLarge),
            padding: AppSpacing.buttonLarge,
            side: const BorderSide(color: AppColors.border),
            shape: RoundedRectangleBorder(
              borderRadius: AppLayout.borderRadiusMd,
            ),
            textStyle: AppTypography.button.copyWith(
              color: AppColors.textPrimary,
            ),
          ),
        ),

        // Input Decoration
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: AppColors.surface,
          contentPadding: AppSpacing.inputContent,
          border: OutlineInputBorder(
            borderRadius: AppLayout.borderRadiusMd,
            borderSide: const BorderSide(color: AppColors.border),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: AppLayout.borderRadiusMd,
            borderSide: const BorderSide(color: AppColors.border),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: AppLayout.borderRadiusMd,
            borderSide: const BorderSide(
              color: AppColors.primary500,
              width: 2,
            ),
          ),
          errorBorder: OutlineInputBorder(
            borderRadius: AppLayout.borderRadiusMd,
            borderSide: const BorderSide(color: AppColors.danger500),
          ),
          focusedErrorBorder: OutlineInputBorder(
            borderRadius: AppLayout.borderRadiusMd,
            borderSide: const BorderSide(
              color: AppColors.danger500,
              width: 2,
            ),
          ),
          hintStyle: AppTypography.body.copyWith(
            color: AppColors.textTertiary,
          ),
          labelStyle: AppTypography.body.copyWith(
            color: AppColors.textSecondary,
          ),
          floatingLabelStyle: AppTypography.labelSmall.copyWith(
            color: AppColors.primary600,
          ),
          errorStyle: AppTypography.caption.copyWith(
            color: AppColors.danger600,
          ),
          prefixIconColor: AppColors.gray400,
          suffixIconColor: AppColors.gray400,
        ),

        // Card (Flat design with border, no shadow)
        cardTheme: CardThemeData(
          color: AppColors.card,
          elevation: 0,
          margin: EdgeInsets.zero,
          shape: RoundedRectangleBorder(
            borderRadius: AppLayout.borderRadiusMd,
            side: const BorderSide(color: AppColors.border, width: 1),
          ),
        ),

        // Chip
        chipTheme: ChipThemeData(
          backgroundColor: AppColors.gray100,
          selectedColor: AppColors.primary100,
          labelStyle: AppTypography.labelSmall,
          padding: AppSpacing.chip,
          shape: RoundedRectangleBorder(
            borderRadius: AppLayout.borderRadiusFull,
          ),
        ),

        // Tab Bar
        tabBarTheme: TabBarThemeData(
          indicatorSize: TabBarIndicatorSize.tab,
          labelColor: AppColors.primary600,
          unselectedLabelColor: AppColors.textSecondary,
          labelStyle: AppTypography.label.copyWith(
            fontWeight: FontWeight.w600,
          ),
          unselectedLabelStyle: AppTypography.label,
          indicator: const UnderlineTabIndicator(
            borderSide: BorderSide(
              color: AppColors.primary600,
              width: 2,
            ),
          ),
        ),

        // Dialog
        dialogTheme: DialogThemeData(
          backgroundColor: AppColors.surface,
          elevation: 16,
          shape: RoundedRectangleBorder(
            borderRadius: AppLayout.borderRadiusXl,
          ),
          titleTextStyle: AppTypography.h3,
          contentTextStyle: AppTypography.body,
        ),

        // Bottom Sheet
        bottomSheetTheme: const BottomSheetThemeData(
          backgroundColor: AppColors.surface,
          elevation: 16,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.vertical(
              top: Radius.circular(AppLayout.radiusXl),
            ),
          ),
        ),

        // Snackbar
        snackBarTheme: SnackBarThemeData(
          backgroundColor: AppColors.gray900,
          contentTextStyle: AppTypography.body.copyWith(color: Colors.white),
          shape: RoundedRectangleBorder(
            borderRadius: AppLayout.borderRadiusMd,
          ),
          behavior: SnackBarBehavior.floating,
        ),

        // Divider
        dividerTheme: const DividerThemeData(
          color: AppColors.divider,
          thickness: 1,
          space: 0,
        ),

        // List Tile
        listTileTheme: ListTileThemeData(
          contentPadding: AppSpacing.listItem,
          horizontalTitleGap: AppSpacing.md,
          minVerticalPadding: AppSpacing.sm,
          titleTextStyle: AppTypography.label,
          subtitleTextStyle: AppTypography.caption,
        ),

        // Switch
        switchTheme: SwitchThemeData(
          thumbColor: WidgetStateProperty.resolveWith((states) {
            if (states.contains(WidgetState.selected)) {
              return AppColors.primary600;
            }
            return AppColors.gray400;
          }),
          trackColor: WidgetStateProperty.resolveWith((states) {
            if (states.contains(WidgetState.selected)) {
              return AppColors.primary200;
            }
            return AppColors.gray200;
          }),
        ),

        // Checkbox
        checkboxTheme: CheckboxThemeData(
          fillColor: WidgetStateProperty.resolveWith((states) {
            if (states.contains(WidgetState.selected)) {
              return AppColors.primary600;
            }
            return Colors.transparent;
          }),
          checkColor: WidgetStateProperty.all(Colors.white),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(4),
          ),
          side: const BorderSide(color: AppColors.gray300, width: 2),
        ),

        // Progress Indicator
        progressIndicatorTheme: const ProgressIndicatorThemeData(
          color: AppColors.primary600,
          linearTrackColor: AppColors.gray200,
          circularTrackColor: AppColors.gray200,
        ),

        // Splash
        splashColor: AppColors.primary100.withValues(alpha: 0.3),
        highlightColor: AppColors.primary100.withValues(alpha: 0.2),
      );

  /// Dark Theme (for future use)
  static ThemeData get dark => light.copyWith(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF0F172A),
        colorScheme: const ColorScheme.dark(
          primary: AppColors.primary500,
          onPrimary: Colors.white,
          surface: Color(0xFF1E293B),
          onSurface: Colors.white,
        ),
      );
}
