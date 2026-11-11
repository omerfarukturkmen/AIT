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
  /// Brand palette from the AIT COACH logo: ink black, lime and white. Lime
  /// marks actions and highlights; status colors (emerald / orange / red)
  /// stay distinct from it.
  static const Color lime = Color(0xFFD4FF00);
  static const Color limeSoft = Color(0xFFEEFF99);
  static const Color limeDeep = Color(0xFF4D6600);
  static const Color ink = Color(0xFF0F0F10);
  static const Color paper = Color(0xFFF2F2EE);
  static const Color brand = lime;

  /// Display font for the wordmark, headings and big numbers (bundled).
  static const String displayFont = 'Anton';

  static ThemeData dark() {
    const tokens = AppTokens(
      surfaceRaised: Color(0xFF222225),
      border: Color(0xFF2C2C30),
      textSecondary: Color(0xFFA1A1A6),
      textTertiary: Color(0xFF6E6E73),
      success: Color(0xFF34D399),
      warning: Color(0xFFFB923C),
      danger: Color(0xFFF87171),
      info: Color(0xFF60A5FA),
    );
    const scheme = ColorScheme(
      brightness: Brightness.dark,
      primary: lime,
      onPrimary: ink,
      primaryContainer: Color(0xFF2B3300),
      onPrimaryContainer: limeSoft,
      secondary: lime,
      onSecondary: ink,
      secondaryContainer: Color(0xFF262A12),
      onSecondaryContainer: Color(0xFFE6F59A),
      error: Color(0xFFF87171),
      onError: Color(0xFF2B0505),
      surface: Color(0xFF19191B),
      onSurface: Colors.white,
      onSurfaceVariant: Color(0xFFA1A1A6),
      surfaceContainerHighest: Color(0xFF222225),
      outline: Color(0xFF3F3F44),
      outlineVariant: Color(0xFF2C2C30),
      inverseSurface: Colors.white,
      onInverseSurface: ink,
    );
    return _build(scheme, tokens, background: ink);
  }

  static ThemeData light() {
    const tokens = AppTokens(
      surfaceRaised: Color(0xFFEAEAE5),
      border: Color(0xFFDEDED8),
      textSecondary: Color(0xFF5F5F63),
      textTertiary: Color(0xFF8E8E93),
      success: Color(0xFF047857),
      warning: Color(0xFFC2410C),
      danger: Color(0xFFDC2626),
      info: Color(0xFF1D4ED8),
    );
    // Lime is unreadable on white: light mode uses black buttons with lime
    // labels (as in the logo) and a deep olive for icons and tints.
    const scheme = ColorScheme(
      brightness: Brightness.light,
      primary: ink,
      onPrimary: lime,
      primaryContainer: Color(0xFFF1FFB0),
      onPrimaryContainer: Color(0xFF2B3300),
      secondary: limeDeep,
      onSecondary: Colors.white,
      secondaryContainer: Color(0xFFEEF7C4),
      onSecondaryContainer: Color(0xFF2B3300),
      error: Color(0xFFDC2626),
      onError: Colors.white,
      surface: Colors.white,
      onSurface: ink,
      onSurfaceVariant: Color(0xFF5F5F63),
      surfaceContainerHighest: Color(0xFFEAEAE5),
      outline: Color(0xFFC7C7C1),
      outlineVariant: Color(0xFFDEDED8),
      inverseSurface: Color(0xFF222225),
      onInverseSurface: Colors.white,
    );
    return _build(scheme, tokens, background: paper);
  }

  /// For content on a lime panel (the logo's tile): black text, black
  /// buttons with lime labels.
  static ThemeData onLime() {
    const tokens = AppTokens(
      surfaceRaised: Color(0xFFC4EC00),
      border: Color(0x330F0F10),
      textSecondary: Color(0xFF2F3800),
      textTertiary: Color(0xFF4A5500),
      success: Color(0xFF065F46),
      warning: Color(0xFF9A3412),
      danger: Color(0xFFB91C1C),
      info: Color(0xFF1E3A8A),
    );
    const scheme = ColorScheme(
      brightness: Brightness.light,
      primary: ink,
      onPrimary: lime,
      primaryContainer: ink,
      onPrimaryContainer: lime,
      secondary: ink,
      onSecondary: lime,
      secondaryContainer: Color(0xFFC4EC00),
      onSecondaryContainer: ink,
      error: Color(0xFFB91C1C),
      onError: Colors.white,
      surface: lime,
      onSurface: ink,
      onSurfaceVariant: Color(0xFF2F3800),
      surfaceContainerHighest: Color(0xFFC4EC00),
      outline: ink,
      outlineVariant: Color(0x330F0F10),
      inverseSurface: ink,
      onInverseSurface: lime,
    );
    return _build(scheme, tokens, background: lime);
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
        fontFamily: displayFont,
        fontSize: 32,
        fontWeight: FontWeight.w400,
        letterSpacing: 0.3,
        color: primary,
      ),
      headlineMedium: base.headlineMedium?.copyWith(
        fontFamily: displayFont,
        fontSize: 26,
        fontWeight: FontWeight.w400,
        letterSpacing: 0.3,
        color: primary,
      ),
      headlineSmall: base.headlineSmall?.copyWith(
        fontFamily: displayFont,
        fontSize: 22,
        fontWeight: FontWeight.w400,
        letterSpacing: 0.3,
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
