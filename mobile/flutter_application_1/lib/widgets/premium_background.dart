import 'package:flutter/material.dart';

import '../core/constants/app_colors.dart';
import '../core/state/app_settings_store.dart';

class PremiumBackground extends StatelessWidget {
  final Widget child;

  const PremiumBackground({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<AppSettings>(
      valueListenable: AppSettingsStore.settings,
      builder: (context, settings, _) {
        return Container(
          decoration: BoxDecoration(
            gradient: settings.isDarkMode
                ? const RadialGradient(
                    center: Alignment.topRight,
                    radius: 1.45,
                    colors: [
                      Color(0xFF312E81),
                      Color(0xFF0F172A),
                      Color(0xFF07111F),
                      Color(0xFF020617),
                    ],
                  )
                : const LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [
                      Color(0xFFE8EEF8),
                      Color(0xFFF1F5FB),
                      Color(0xFFEDE9FE),
                      Color(0xFFF8FAFC),
                    ],
                  ),
          ),
          child: Stack(
            children: [
              Positioned(
                top: -120,
                right: -90,
                child: GlowCircle(
                  size: 280,
                  color: settings.isDarkMode
                      ? AppColors.primary
                      : const Color(0xFF93C5FD),
                  opacity: settings.isDarkMode ? 0.25 : 0.20,
                ),
              ),
              Positioned(
                top: 170,
                left: -135,
                child: GlowCircle(
                  size: 255,
                  color: settings.isDarkMode
                      ? AppColors.electricBlue
                      : const Color(0xFFC4B5FD),
                  opacity: settings.isDarkMode ? 0.13 : 0.18,
                ),
              ),
              Positioned(
                bottom: -150,
                right: -120,
                child: GlowCircle(
                  size: 300,
                  color: settings.isDarkMode
                      ? AppColors.neonGreen
                      : const Color(0xFFA7F3D0),
                  opacity: settings.isDarkMode ? 0.09 : 0.14,
                ),
              ),
              Positioned.fill(
                child: IgnorePointer(
                  child: CustomPaint(
                    painter: _GridPainter(isDarkMode: settings.isDarkMode),
                  ),
                ),
              ),
              child,
            ],
          ),
        );
      },
    );
  }
}

class GlowCircle extends StatelessWidget {
  final double size;
  final Color color;
  final double opacity;

  const GlowCircle({
    super.key,
    required this.size,
    required this.color,
    required this.opacity,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      height: size,
      width: size,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: color.withValues(alpha: opacity),
        boxShadow: [
          BoxShadow(
            color: color.withValues(alpha: opacity),
            blurRadius: 90,
            spreadRadius: 45,
          ),
        ],
      ),
    );
  }
}

class _GridPainter extends CustomPainter {
  final bool isDarkMode;

  const _GridPainter({required this.isDarkMode});

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = isDarkMode
          ? Colors.white.withValues(alpha: 0.018)
          : const Color(0xFF64748B).withValues(alpha: 0.025)
      ..strokeWidth = 1;

    const spacing = 42.0;

    for (double x = 0; x < size.width; x += spacing) {
      canvas.drawLine(Offset(x, 0), Offset(x, size.height), paint);
    }

    for (double y = 0; y < size.height; y += spacing) {
      canvas.drawLine(Offset(0, y), Offset(size.width, y), paint);
    }
  }

  @override
  bool shouldRepaint(covariant _GridPainter oldDelegate) {
    return oldDelegate.isDarkMode != isDarkMode;
  }
}
