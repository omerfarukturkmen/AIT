import 'package:flutter/material.dart';

import '../core/theme/app_theme.dart';

/// Flat surface with a hairline border; tappable when [onTap] is set.
class AppCard extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry padding;
  final VoidCallback? onTap;
  final Color? color;
  final Color? borderColor;

  const AppCard({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(Gap.lg),
    this.onTap,
    this.color,
    this.borderColor,
  });

  @override
  Widget build(BuildContext context) {
    final radius = BorderRadius.circular(Radii.lg);
    return Material(
      color: color ?? context.colors.surface,
      shape: RoundedRectangleBorder(
        borderRadius: radius,
        side: BorderSide(color: borderColor ?? context.tokens.border),
      ),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Padding(padding: padding, child: child),
      ),
    );
  }
}

/// Featured card: black gradient with a volt glow and a fine volt edge. Its
/// content always uses the dark theme so it reads well in both modes.
class HeroCard extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry padding;

  const HeroCard({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(Gap.xl),
  });

  static const Color foreground = Color(0xFFF2F4F6);
  static const Color muted = Color(0xFFB9C0C8);

  @override
  Widget build(BuildContext context) {
    final radius = BorderRadius.circular(Radii.lg);
    return DecoratedBox(
      decoration: BoxDecoration(
        borderRadius: radius,
        border: Border.all(color: AppTheme.volt.withValues(alpha: 0.35)),
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFF0B0C0E), Color(0xFF15190F), Color(0xFF2B3A0C)],
          stops: [0, 0.55, 1],
        ),
      ),
      child: Theme(
        data: AppTheme.dark(),
        child: Padding(padding: padding, child: child),
      ),
    );
  }
}
