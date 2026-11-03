import 'package:flutter/material.dart';

/// Semantic colors that Material's ColorScheme does not cover.
@immutable
class AppTokens extends ThemeExtension<AppTokens> {
  final Color surfaceRaised;
  final Color border;
  final Color textSecondary;
  final Color textTertiary;
  final Color success;
  final Color warning;
  final Color danger;
  final Color info;

  const AppTokens({
    required this.surfaceRaised,
    required this.border,
    required this.textSecondary,
    required this.textTertiary,
    required this.success,
    required this.warning,
    required this.danger,
    required this.info,
  });

  /// Green / amber / red for a 0-100 form score.
  Color scoreColor(int score) {
    if (score >= 80) return success;
    if (score >= 60) return warning;
    return danger;
  }

  @override
  AppTokens copyWith({
    Color? surfaceRaised,
    Color? border,
    Color? textSecondary,
    Color? textTertiary,
    Color? success,
    Color? warning,
    Color? danger,
    Color? info,
  }) {
    return AppTokens(
      surfaceRaised: surfaceRaised ?? this.surfaceRaised,
      border: border ?? this.border,
      textSecondary: textSecondary ?? this.textSecondary,
      textTertiary: textTertiary ?? this.textTertiary,
      success: success ?? this.success,
      warning: warning ?? this.warning,
      danger: danger ?? this.danger,
      info: info ?? this.info,
    );
  }

  @override
  AppTokens lerp(AppTokens? other, double t) {
    if (other == null) return this;
    return AppTokens(
      surfaceRaised: Color.lerp(surfaceRaised, other.surfaceRaised, t)!,
      border: Color.lerp(border, other.border, t)!,
      textSecondary: Color.lerp(textSecondary, other.textSecondary, t)!,
      textTertiary: Color.lerp(textTertiary, other.textTertiary, t)!,
      success: Color.lerp(success, other.success, t)!,
      warning: Color.lerp(warning, other.warning, t)!,
      danger: Color.lerp(danger, other.danger, t)!,
      info: Color.lerp(info, other.info, t)!,
    );
  }
}

extension AppThemeContext on BuildContext {
  AppTokens get tokens => Theme.of(this).extension<AppTokens>()!;
  ColorScheme get colors => Theme.of(this).colorScheme;
  TextTheme get text => Theme.of(this).textTheme;
}

/// Spacing scale (4 pt grid) and corner radii.
abstract final class Gap {
  static const double xs = 4;
  static const double sm = 8;
  static const double md = 12;
  static const double lg = 16;
  static const double xl = 24;
  static const double xxl = 32;

  /// Horizontal page padding.
  static const double page = 20;
}

abstract final class Radii {
  static const double sm = 10;
  static const double md = 14;
  static const double lg = 20;
}

abstract final class AppTheme {
  static const Color brand = Color(0xFF7C5CFF);

  static ThemeData dark() {
    const tokens = AppTokens(
      surfaceRaised: Color(0xFF1A2130),
      border: Color(0xFF262F40),
      textSecondary: Color(0xFFA3ADBD),
      textTertiary: Color(0xFF6E788A),
      success: Color(0xFF34D399),
      warning: Color(0xFFFBBF24),
      danger: Color(0xFFF87171),
      info: Color(0xFF38BDF8),
    );
    const scheme = ColorScheme(
      brightness: Brightness.dark,
      primary: Color(0xFF8B6CFF),
      onPrimary: Colors.white,
      primaryContainer: Color(0xFF261E52),
      onPrimaryContainer: Color(0xFFDAD2FF),
      secondary: Color(0xFF38BDF8),
      onSecondary: Color(0xFF04131C),
      secondaryContainer: Color(0xFF261E52),
      onSecondaryContainer: Color(0xFFDAD2FF),
      error: Color(0xFFF87171),
      onError: Color(0xFF2B0505),
      surface: Color(0xFF121826),
      onSurface: Color(0xFFF2F4F8),
      onSurfaceVariant: Color(0xFFA3ADBD),
      surfaceContainerHighest: Color(0xFF1A2130),
      outline: Color(0xFF3A4458),
      outlineVariant: Color(0xFF262F40),
      inverseSurface: Color(0xFFF2F4F8),
      onInverseSurface: Color(0xFF121826),
    );
    return _build(scheme, tokens, background: const Color(0xFF0B0F17));
  }

  static ThemeData light() {
    const tokens = AppTokens(
      surfaceRaised: Color(0xFFF1F3F8),
      border: Color(0xFFE2E6EE),
      textSecondary: Color(0xFF4B5567),
      textTertiary: Color(0xFF8792A5),
      success: Color(0xFF15803D),
      warning: Color(0xFFB45309),
      danger: Color(0xFFDC2626),
      info: Color(0xFF0369A1),
    );
    const scheme = ColorScheme(
      brightness: Brightness.light,
      primary: Color(0xFF6243F0),
      onPrimary: Colors.white,
      primaryContainer: Color(0xFFEDE9FF),
      onPrimaryContainer: Color(0xFF2C1A8C),
      secondary: Color(0xFF0369A1),
      onSecondary: Colors.white,
      secondaryContainer: Color(0xFFEDE9FF),
      onSecondaryContainer: Color(0xFF2C1A8C),
      error: Color(0xFFDC2626),
      onError: Colors.white,
      surface: Colors.white,
      onSurface: Color(0xFF0E1525),
      onSurfaceVariant: Color(0xFF4B5567),
      surfaceContainerHighest: Color(0xFFF1F3F8),
      outline: Color(0xFFC7CDD9),
      outlineVariant: Color(0xFFE2E6EE),
      inverseSurface: Color(0xFF1A2130),
      onInverseSurface: Color(0xFFF2F4F8),
    );
    return _build(scheme, tokens, background: const Color(0xFFF5F6FA));
  }

  static ThemeData _build(
    ColorScheme scheme,
    AppTokens tokens, {
    required Color background,
  }) {
    final base = ThemeData(
      useMaterial3: true,
      colorScheme: scheme,
      brightness: scheme.brightness,
    );
    final text = _textTheme(base.textTheme, scheme, tokens);
    final buttonShape = RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(Radii.md),
    );

    return base.copyWith(
      scaffoldBackgroundColor: background,
      canvasColor: background,
      textTheme: text,
      extensions: [tokens],
      appBarTheme: AppBarTheme(
        backgroundColor: background,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: false,
        foregroundColor: scheme.onSurface,
        titleTextStyle: text.titleLarge,
      ),
      cardTheme: CardThemeData(
        color: scheme.surface,
        elevation: 0,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(Radii.lg),
          side: BorderSide(color: tokens.border),
        ),
      ),
      dividerTheme: DividerThemeData(
        color: tokens.border,
        thickness: 1,
        space: 1,
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          minimumSize: const Size(64, 52),
          shape: buttonShape,
          textStyle: text.labelLarge?.copyWith(fontSize: 15),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          minimumSize: const Size(64, 52),
          shape: buttonShape,
          foregroundColor: scheme.onSurface,
          side: BorderSide(color: scheme.outline),
          textStyle: text.labelLarge?.copyWith(fontSize: 15),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          shape: buttonShape,
          textStyle: text.labelLarge,
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: tokens.surfaceRaised,
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 14,
          vertical: 16,
        ),
        border: _inputBorder(tokens.border),
        enabledBorder: _inputBorder(tokens.border),
        focusedBorder: _inputBorder(scheme.primary, 1.6),
        errorBorder: _inputBorder(scheme.error),
        focusedErrorBorder: _inputBorder(scheme.error, 1.6),
        labelStyle: TextStyle(color: tokens.textSecondary),
        hintStyle: TextStyle(color: tokens.textTertiary),
      ),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: scheme.surface,
        surfaceTintColor: Colors.transparent,
        indicatorColor: scheme.primaryContainer,
        elevation: 0,
        height: 68,
        labelTextStyle: WidgetStateProperty.resolveWith(
          (states) => text.labelMedium?.copyWith(
            fontWeight: states.contains(WidgetState.selected)
                ? FontWeight.w600
                : FontWeight.w500,
            color: states.contains(WidgetState.selected)
                ? scheme.onSurface
                : tokens.textSecondary,
          ),
        ),
        iconTheme: WidgetStateProperty.resolveWith(
          (states) => IconThemeData(
            color: states.contains(WidgetState.selected)
                ? scheme.onPrimaryContainer
                : tokens.textSecondary,
          ),
        ),
      ),
      listTileTheme: ListTileThemeData(
        iconColor: tokens.textSecondary,
        contentPadding: const EdgeInsets.symmetric(horizontal: Gap.lg),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(Radii.md),
        ),
      ),
      chipTheme: base.chipTheme.copyWith(
        backgroundColor: tokens.surfaceRaised,
        side: BorderSide(color: tokens.border),
        labelStyle: text.labelMedium,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(Radii.sm),
        ),
      ),
      segmentedButtonTheme: SegmentedButtonThemeData(
        style: SegmentedButton.styleFrom(
          side: BorderSide(color: tokens.border),
          selectedBackgroundColor: scheme.primaryContainer,
          selectedForegroundColor: scheme.onPrimaryContainer,
          shape: buttonShape,
        ),
      ),
      snackBarTheme: SnackBarThemeData(
        behavior: SnackBarBehavior.floating,
        backgroundColor: scheme.inverseSurface,
        contentTextStyle: text.bodyMedium?.copyWith(
          color: scheme.onInverseSurface,
        ),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(Radii.md),
        ),
      ),
      dialogTheme: DialogThemeData(
        backgroundColor: scheme.surface,
        surfaceTintColor: Colors.transparent,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(Radii.lg),
        ),
        titleTextStyle: text.titleLarge,
        contentTextStyle: text.bodyMedium?.copyWith(
          color: tokens.textSecondary,
        ),
      ),
      bottomSheetTheme: BottomSheetThemeData(
        backgroundColor: scheme.surface,
        surfaceTintColor: Colors.transparent,
        showDragHandle: true,
        shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(Radii.lg)),
        ),
      ),
      progressIndicatorTheme: ProgressIndicatorThemeData(
        color: scheme.primary,
        linearTrackColor: tokens.surfaceRaised,
        circularTrackColor: tokens.surfaceRaised,
      ),
      switchTheme: SwitchThemeData(
        trackOutlineColor: WidgetStateProperty.resolveWith(
          (states) => states.contains(WidgetState.selected)
              ? Colors.transparent
              : scheme.outline,
        ),
      ),
    );
  }

  static OutlineInputBorder _inputBorder(Color color, [double width = 1]) {
    return OutlineInputBorder(
      borderRadius: BorderRadius.circular(Radii.md),
      borderSide: BorderSide(color: color, width: width),
    );
  }

  static TextTheme _textTheme(
    TextTheme base,
    ColorScheme scheme,
    AppTokens tokens,
  ) {
    final primary = scheme.onSurface;
    return base.copyWith(
      displaySmall: base.displaySmall?.copyWith(
        fontSize: 32,
        fontWeight: FontWeight.w700,
        letterSpacing: -0.8,
        color: primary,
      ),
      headlineMedium: base.headlineMedium?.copyWith(
        fontSize: 26,
        fontWeight: FontWeight.w700,
        letterSpacing: -0.5,
        color: primary,
      ),
      headlineSmall: base.headlineSmall?.copyWith(
        fontSize: 22,
        fontWeight: FontWeight.w700,
        letterSpacing: -0.3,
        color: primary,
      ),
      titleLarge: base.titleLarge?.copyWith(
        fontSize: 19,
        fontWeight: FontWeight.w700,
        letterSpacing: -0.2,
        color: primary,
      ),
      titleMedium: base.titleMedium?.copyWith(
        fontSize: 16,
        fontWeight: FontWeight.w600,
        color: primary,
      ),
      titleSmall: base.titleSmall?.copyWith(
        fontSize: 14,
        fontWeight: FontWeight.w600,
        color: primary,
      ),
      bodyLarge: base.bodyLarge?.copyWith(
        fontSize: 16,
        height: 1.5,
        color: primary,
      ),
      bodyMedium: base.bodyMedium?.copyWith(
        fontSize: 14,
        height: 1.45,
        color: primary,
      ),
      bodySmall: base.bodySmall?.copyWith(
        fontSize: 12.5,
        height: 1.4,
        color: tokens.textSecondary,
      ),
      labelLarge: base.labelLarge?.copyWith(
        fontSize: 14,
        fontWeight: FontWeight.w600,
        color: primary,
      ),
      labelMedium: base.labelMedium?.copyWith(
        fontSize: 12,
        fontWeight: FontWeight.w500,
        color: tokens.textSecondary,
      ),
      labelSmall: base.labelSmall?.copyWith(
        fontSize: 11,
        fontWeight: FontWeight.w600,
        letterSpacing: 0.4,
        color: tokens.textTertiary,
      ),
    );
  }
}
