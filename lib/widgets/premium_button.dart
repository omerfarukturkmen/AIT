import 'package:flutter/material.dart';

import '../core/constants/app_colors.dart';

class PremiumButton extends StatefulWidget {
  final IconData icon;
  final String text;
  final VoidCallback onPressed;

  const PremiumButton({
    super.key,
    required this.icon,
    required this.text,
    required this.onPressed,
  });

  @override
  State<PremiumButton> createState() => _PremiumButtonState();
}

class _PremiumButtonState extends State<PremiumButton> {
  bool isPressed = false;
  bool isHovered = false;

  @override
  Widget build(BuildContext context) {
    final double scale = isPressed
        ? 0.97
        : isHovered
        ? 1.025
        : 1;

    return MouseRegion(
      cursor: SystemMouseCursors.click,
      onEnter: (_) {
        setState(() {
          isHovered = true;
        });
      },
      onExit: (_) {
        setState(() {
          isHovered = false;
        });
      },
      child: AnimatedScale(
        scale: scale,
        duration: const Duration(milliseconds: 160),
        curve: Curves.easeOut,
        child: GestureDetector(
          onTapDown: (_) {
            setState(() {
              isPressed = true;
            });
          },
          onTapUp: (_) {
            setState(() {
              isPressed = false;
            });
          },
          onTapCancel: () {
            setState(() {
              isPressed = false;
            });
          },
          onTap: widget.onPressed,
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 220),
            padding: const EdgeInsets.symmetric(vertical: 17),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: isHovered
                    ? const [
                        AppColors.neonGreen,
                        AppColors.electricBlue,
                        AppColors.primary,
                      ]
                    : const [
                        AppColors.electricBlue,
                        AppColors.primary,
                        AppColors.primaryDark,
                      ],
              ),
              borderRadius: BorderRadius.circular(isHovered ? 24 : 20),
              border: Border.all(
                color: isHovered
                    ? Colors.white.withValues(alpha: 0.42)
                    : Colors.white24,
              ),
              boxShadow: [
                BoxShadow(
                  color: AppColors.primary.withValues(
                    alpha: isHovered
                        ? 0.48
                        : isPressed
                        ? 0.16
                        : 0.32,
                  ),
                  blurRadius: isHovered
                      ? 38
                      : isPressed
                      ? 14
                      : 28,
                  offset: const Offset(0, 12),
                ),
                BoxShadow(
                  color: AppColors.electricBlue.withValues(
                    alpha: isHovered
                        ? 0.34
                        : isPressed
                        ? 0.08
                        : 0.18,
                  ),
                  blurRadius: isHovered
                      ? 34
                      : isPressed
                      ? 12
                      : 24,
                  offset: const Offset(-6, -4),
                ),
              ],
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                AnimatedRotation(
                  turns: isHovered ? 0.03 : 0,
                  duration: const Duration(milliseconds: 180),
                  child: Icon(widget.icon, color: Colors.white),
                ),
                const SizedBox(width: 10),
                Flexible(
                  child: Text(
                    widget.text,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.w900,
                      fontSize: 16,
                      letterSpacing: 0.1,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
