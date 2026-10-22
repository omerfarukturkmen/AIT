import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';

/// Contrast-checked colors for the auth screens in light and dark mode.
class AuthPalette {
  final bool isDark;
  final Color text;
  final Color textMuted;
  final Color fieldFill;
  final Color fieldBorder;
  final Color focus;
  final Color error;
  final Color success;
  final Color link;
  final Color divider;

  const AuthPalette._({
    required this.isDark,
    required this.text,
    required this.textMuted,
    required this.fieldFill,
    required this.fieldBorder,
    required this.focus,
    required this.error,
    required this.success,
    required this.link,
    required this.divider,
  });

  factory AuthPalette.of(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    if (isDark) {
      return AuthPalette._(
        isDark: true,
        text: AppColors.text,
        textMuted: AppColors.textSoft,
        fieldFill: Colors.white.withValues(alpha: 0.05),
        fieldBorder: Colors.white.withValues(alpha: 0.16),
        focus: AppColors.primarySoft,
        error: const Color(0xFFF87171),
        success: const Color(0xFF4ADE80),
        link: AppColors.primarySoft,
        divider: Colors.white.withValues(alpha: 0.12),
      );
    }
    return const AuthPalette._(
      isDark: false,
      text: Color(0xFF0F172A),
      textMuted: Color(0xFF475569),
      fieldFill: Colors.white,
      fieldBorder: Color(0xFFCBD5E1),
      focus: Color(0xFF7C3AED),
      error: Color(0xFFDC2626),
      success: Color(0xFF15803D),
      link: Color(0xFF6D28D9),
      divider: Color(0xFFE2E8F0),
    );
  }
}
