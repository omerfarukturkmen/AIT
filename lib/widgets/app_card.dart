import 'package:flutter/material.dart';

import '../core/theme/app_theme.dart';

/// Borderless surface: set apart by tone in dark mode and by a soft shadow
/// in light mode. Tappable when [onTap] is set.
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
    final light = Theme.of(context).brightness == Brightness.light;
    return Material(
      color: color ?? context.colors.surface,
      elevation: light && color == null ? 2 : 0,
      shadowColor: const Color(0x22000000),
      shape: RoundedRectangleBorder(
        borderRadius: radius,
        side: borderColor == null
            ? BorderSide.none
            : BorderSide(color: borderColor!),
      ),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Padding(padding: padding, child: child),
      ),
    );
  }
}

/// Featured card: a near-black panel with a fine lime edge, like the logo.
/// Its content always uses the dark theme so it reads well in both modes.
class HeroCard extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry padding;

  const HeroCard({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(Gap.xl),
  });

  static const Color foreground = Colors.white;
  static const Color muted = Color(0xFFA1A1A6);

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: const Color(0xFF161618),
        borderRadius: BorderRadius.circular(Radii.lg),
        border: Border.all(color: AppTheme.lime.withValues(alpha: 0.28)),
        boxShadow: const [
          BoxShadow(
            color: Color(0x33000000),
            blurRadius: 24,
            offset: Offset(0, 10),
          ),
        ],
      ),
      child: Theme(
        data: AppTheme.dark(),
        child: Padding(padding: padding, child: child),
      ),
    );
  }
}

/// The brand's lime panel (as in the app icon) for the one main action on a
/// screen. Content uses [AppTheme.onLime]: black text and buttons.
class LimeCard extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry padding;

  const LimeCard({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(Gap.xl),
  });

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: AppTheme.lime,
        borderRadius: BorderRadius.circular(Radii.lg + 4),
        boxShadow: const [
          BoxShadow(
            color: Color(0x33000000),
            blurRadius: 24,
            offset: Offset(0, 10),
          ),
        ],
      ),
      child: Theme(
        data: AppTheme.onLime(),
        child: Padding(padding: padding, child: child),
      ),
    );
  }
}
