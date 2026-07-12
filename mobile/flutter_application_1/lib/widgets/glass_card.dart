import 'dart:ui';

import 'package:flutter/material.dart';

import '../core/constants/app_colors.dart';
import '../core/state/app_settings_store.dart';

class GlassCard extends StatefulWidget {
  final Widget child;
  final EdgeInsetsGeometry padding;
  final double radius;
  final bool enableHover;

  const GlassCard({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(18),
    this.radius = 28,
    this.enableHover = true,
  });

  @override
  State<GlassCard> createState() => _GlassCardState();
}

class _GlassCardState extends State<GlassCard> {
  bool isHovered = false;

  @override
  Widget build(BuildContext context) {
    final double scale = widget.enableHover && isHovered ? 1.012 : 1;

    return ValueListenableBuilder<AppSettings>(
      valueListenable: AppSettingsStore.settings,
      builder: (context, settings, _) {
        final isDark = settings.isDarkMode;

        return MouseRegion(
          cursor: widget.enableHover
              ? SystemMouseCursors.click
              : SystemMouseCursors.basic,
          onEnter: (_) {
            if (!widget.enableHover) return;
            setState(() {
              isHovered = true;
            });
          },
          onExit: (_) {
            if (!widget.enableHover) return;
            setState(() {
              isHovered = false;
            });
          },
          child: AnimatedScale(
            scale: scale,
            duration: const Duration(milliseconds: 180),
            curve: Curves.easeOutCubic,
            child: ClipRRect(
              borderRadius: BorderRadius.circular(widget.radius),
              child: BackdropFilter(
                filter: ImageFilter.blur(
                  sigmaX: isHovered ? 24 : 18,
                  sigmaY: isHovered ? 24 : 18,
                ),
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 220),
                  curve: Curves.easeOutCubic,
                  padding: widget.padding,
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: isDark
                          ? isHovered
                                ? [
                                    Colors.white.withValues(alpha: 0.18),
                                    AppColors.electricBlue.withValues(
                                      alpha: 0.08,
                                    ),
                                    AppColors.primary.withValues(alpha: 0.08),
                                  ]
                                : [
                                    Colors.white.withValues(alpha: 0.13),
                                    Colors.white.withValues(alpha: 0.055),
                                    AppColors.primary.withValues(alpha: 0.045),
                                  ]
                          : isHovered
                          ? [
                              const Color(0xFFFFFFFF).withValues(alpha: 0.88),
                              const Color(0xFFE0F2FE).withValues(alpha: 0.66),
                              const Color(0xFFEDE9FE).withValues(alpha: 0.58),
                            ]
                          : [
                              const Color(0xFFFFFFFF).withValues(alpha: 0.76),
                              const Color(0xFFF8FAFC).withValues(alpha: 0.66),
                              const Color(0xFFEDE9FE).withValues(alpha: 0.34),
                            ],
                    ),
                    borderRadius: BorderRadius.circular(widget.radius),
                    border: Border.all(
                      color: isHovered
                          ? isDark
                                ? AppColors.electricBlue.withValues(alpha: 0.38)
                                : const Color(
                                    0xFF93C5FD,
                                  ).withValues(alpha: 0.65)
                          : isDark
                          ? Colors.white.withValues(alpha: 0.13)
                          : Colors.white.withValues(alpha: 0.85),
                    ),
                    boxShadow: [
                      BoxShadow(
                        color: isDark
                            ? AppColors.primary.withValues(
                                alpha: isHovered ? 0.24 : 0.13,
                              )
                            : const Color(
                                0xFF64748B,
                              ).withValues(alpha: isHovered ? 0.16 : 0.10),
                        blurRadius: isHovered ? 42 : 30,
                        offset: const Offset(0, 16),
                      ),
                      BoxShadow(
                        color: isDark
                            ? AppColors.electricBlue.withValues(
                                alpha: isHovered ? 0.14 : 0.06,
                              )
                            : const Color(
                                0xFF93C5FD,
                              ).withValues(alpha: isHovered ? 0.18 : 0.09),
                        blurRadius: isHovered ? 36 : 24,
                        offset: const Offset(-8, -8),
                      ),
                    ],
                  ),
                  child: DefaultTextStyle.merge(
                    style: TextStyle(
                      color: isDark ? AppColors.text : const Color(0xFF111827),
                    ),
                    child: widget.child,
                  ),
                ),
              ),
            ),
          ),
        );
      },
    );
  }
}
