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
