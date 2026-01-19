import 'package:flutter/material.dart';

/// BottleCRM Color System
/// A professional, modern color palette optimized for CRM workflows
/// Inspired by HubSpot mobile app design patterns
class AppColors {
  AppColors._();

  // ============================================
  // PRIMARY PALETTE (Blue - Trust & Professionalism)
  // ============================================
  static const Color primary50 = Color(0xFFEFF6FF);
  static const Color primary100 = Color(0xFFDBEAFE);
  static const Color primary200 = Color(0xFFBFDBFE);
  static const Color primary300 = Color(0xFF93C5FD);
  static const Color primary400 = Color(0xFF60A5FA);
  static const Color primary500 = Color(0xFF3B82F6);
  static const Color primary600 = Color(0xFF2563EB); // Main action color
  static const Color primary700 = Color(0xFF1D4ED8);
  static const Color primary800 = Color(0xFF1E40AF);
  static const Color primary900 = Color(0xFF1E3A8A);

  // ============================================
  // ACCENT PALETTE (Coral/Orange - CTAs & FAB)
  // ============================================
  static const Color accent50 = Color(0xFFFFF7ED);
  static const Color accent100 = Color(0xFFFFEDD5);
  static const Color accent200 = Color(0xFFFED7AA);
  static const Color accent300 = Color(0xFFFDBA74);
  static const Color accent400 = Color(0xFFFB923C);
  static const Color accent500 = Color(0xFFF97316); // Main accent color
  static const Color accent600 = Color(0xFFEA580C);
  static const Color accent700 = Color(0xFFC2410C);

  // ============================================
  // SUCCESS (Green - Wins & Completions)
  // ============================================
  static const Color success50 = Color(0xFFF0FDF4);
  static const Color success100 = Color(0xFFDCFCE7);
  static const Color success200 = Color(0xFFBBF7D0);
  static const Color success300 = Color(0xFF86EFAC);
  static const Color success400 = Color(0xFF4ADE80);
  static const Color success500 = Color(0xFF22C55E);
  static const Color success600 = Color(0xFF16A34A);
  static const Color success700 = Color(0xFF15803D);
  static const Color success800 = Color(0xFF166534);
  static const Color success900 = Color(0xFF14532D);

  // ============================================
  // WARNING (Amber - Attention & Urgency)
  // ============================================
  static const Color warning50 = Color(0xFFFFFBEB);
  static const Color warning100 = Color(0xFFFEF3C7);
  static const Color warning200 = Color(0xFFFDE68A);
  static const Color warning300 = Color(0xFFFCD34D);
  static const Color warning400 = Color(0xFFFBBF24);
  static const Color warning500 = Color(0xFFF59E0B);
  static const Color warning600 = Color(0xFFD97706);
  static const Color warning700 = Color(0xFFB45309);

  // ============================================
  // DANGER (Red - Errors & Lost Deals)
  // ============================================
  static const Color danger50 = Color(0xFFFEF2F2);
  static const Color danger100 = Color(0xFFFEE2E2);
  static const Color danger200 = Color(0xFFFECACA);
  static const Color danger300 = Color(0xFFFCA5A5);
  static const Color danger400 = Color(0xFFF87171);
  static const Color danger500 = Color(0xFFEF4444);
  static const Color danger600 = Color(0xFFDC2626);
  static const Color danger700 = Color(0xFFB91C1C);
  static const Color danger800 = Color(0xFF991B1B);
  static const Color danger900 = Color(0xFF7F1D1D);

  // ============================================
  // PURPLE (For Proposal Stage)
  // ============================================
  static const Color purple50 = Color(0xFFFAF5FF);
  static const Color purple100 = Color(0xFFF3E8FF);
  static const Color purple200 = Color(0xFFE9D5FF);
  static const Color purple300 = Color(0xFFD8B4FE);
  static const Color purple400 = Color(0xFFC084FC);
  static const Color purple500 = Color(0xFFA855F7);
  static const Color purple600 = Color(0xFF9333EA);
  static const Color purple700 = Color(0xFF7C3AED);

  // ============================================
  // TEAL (For Links & Dates - HubSpot style)
  // ============================================
  static const Color teal50 = Color(0xFFF0FDFA);
  static const Color teal100 = Color(0xFFCCFBF1);
  static const Color teal200 = Color(0xFF99F6E4);
  static const Color teal300 = Color(0xFF5EEAD4);
  static const Color teal400 = Color(0xFF2DD4BF);
  static const Color teal500 = Color(0xFF14B8A6);
  static const Color teal600 = Color(0xFF0D9488);
  static const Color teal700 = Color(0xFF0F766E);

  // ============================================
  // NEUTRAL GRAYS
  // ============================================
  static const Color gray50 = Color(0xFFF9FAFB);
  static const Color gray100 = Color(0xFFF3F4F6);
  static const Color gray200 = Color(0xFFE5E7EB);
  static const Color gray300 = Color(0xFFD1D5DB);
  static const Color gray400 = Color(0xFF9CA3AF);
  static const Color gray500 = Color(0xFF6B7280);
  static const Color gray600 = Color(0xFF4B5563);
  static const Color gray700 = Color(0xFF374151);
  static const Color gray800 = Color(0xFF1F2937);
  static const Color gray900 = Color(0xFF0F172A); // Primary text

  // ============================================
  // SURFACES
  // ============================================
  static const Color surface = Color(0xFFFFFFFF);
  static const Color surfaceDim = Color(0xFFF9FAFB); // Page background
  static const Color surfaceBright = Color(0xFFFFFFFF);

  // ============================================
  // SEMANTIC ALIASES
  // ============================================
  static const Color textPrimary = gray900;
  static const Color textSecondary = gray500;
  static const Color textTertiary = gray400;
  static const Color textDisabled = Color(0x809CA3AF); // gray400 at 50%

  static const Color border = gray200;
  static const Color borderLight = gray100;
  static const Color divider = gray200;

  static const Color background = surfaceDim;
  static const Color card = surface;

  // ============================================
  // STATUS COLORS FOR LEADS
  // ============================================
  static const Color statusNew = primary500;
  static const Color statusContacted = warning500;
  static const Color statusQualified = success500;
  static const Color statusLost = danger500;

  // ============================================
  // PIPELINE STAGE COLORS
  // ============================================
  static const Color stageProspecting = gray400;
  static const Color stageQualified = primary500;
  static const Color stageProposal = purple500;
  static const Color stageNegotiation = warning500;
  static const Color stageClosedWon = success500;
  static const Color stageClosedLost = danger500;

  // ============================================
  // PRIORITY COLORS
  // ============================================
  static const Color priorityLow = gray400;
  static const Color priorityMedium = warning500;
  static const Color priorityHigh = danger500;
  static const Color priorityUrgent = purple500;

  // ============================================
  // AVATAR BACKGROUND COLORS
  // ============================================
  static const List<Color> avatarColors = [
    Color(0xFF2563EB), // Blue
    Color(0xFF7C3AED), // Purple
    Color(0xFFDB2777), // Pink
    Color(0xFFDC2626), // Red
    Color(0xFFEA580C), // Orange
    Color(0xFFCA8A04), // Yellow
    Color(0xFF16A34A), // Green
    Color(0xFF0D9488), // Teal
    Color(0xFF0284C7), // Light Blue
    Color(0xFF4F46E5), // Indigo
  ];

  /// Get a deterministic avatar color based on a name
  static Color getAvatarColor(String name) {
    if (name.isEmpty) return avatarColors[0];
    final index = name.codeUnitAt(0) % avatarColors.length;
    return avatarColors[index];
  }
}
