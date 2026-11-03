import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../core/theme/app_theme.dart';
import 'app_card.dart';

/// Rounded square with a tinted icon, used as a leading visual.
class IconBadge extends StatelessWidget {
  final IconData icon;
  final Color? color;
  final double size;

  const IconBadge({super.key, required this.icon, this.color, this.size = 40});

  @override
  Widget build(BuildContext context) {
    final tint = color ?? context.colors.primary;
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        color: tint.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(size * 0.3),
      ),
      child: Icon(icon, color: tint, size: size * 0.5),
    );
  }
}

/// Compact metric: label, value and optional icon.
class StatTile extends StatelessWidget {
  final String label;
  final String value;
  final IconData? icon;
  final Color? valueColor;

  const StatTile({
    super.key,
    required this.label,
    required this.value,
    this.icon,
    this.valueColor,
  });

  @override
  Widget build(BuildContext context) {
    return AppCard(
      padding: const EdgeInsets.all(Gap.md + 2),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (icon != null) ...[
            Icon(icon, size: 20, color: context.tokens.textSecondary),
            const SizedBox(height: Gap.sm),
          ],
          Text(
            value,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: context.text.headlineSmall?.copyWith(color: valueColor),
          ),
          const SizedBox(height: 2),
          Text(
            label,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: context.text.labelMedium,
          ),
        ],
      ),
    );
  }
}

/// Small rounded label, e.g. a status or category.
class Pill extends StatelessWidget {
  final String label;
  final Color? color;
  final IconData? icon;

  const Pill({super.key, required this.label, this.color, this.icon});

  @override
  Widget build(BuildContext context) {
    final tint = color ?? context.tokens.textSecondary;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: Gap.sm + 2, vertical: 4),
      decoration: BoxDecoration(
        color: tint.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (icon != null) ...[
            Icon(icon, size: 14, color: tint),
            const SizedBox(width: 4),
          ],
          Text(
            label,
            style: context.text.labelMedium?.copyWith(
              color: tint,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}

/// Centered placeholder for lists without data, with an optional action.
class EmptyState extends StatelessWidget {
  final IconData icon;
  final String title;
  final String message;
  final String? actionLabel;
  final VoidCallback? onAction;

  const EmptyState({
    super.key,
    required this.icon,
    required this.title,
    required this.message,
    this.actionLabel,
    this.onAction,
  });

  @override
  Widget build(BuildContext context) {
    return AppCard(
      padding: const EdgeInsets.symmetric(
        horizontal: Gap.xl,
        vertical: Gap.xxl,
      ),
      child: Column(
        children: [
          IconBadge(icon: icon, size: 52),
          const SizedBox(height: Gap.lg),
          Text(
            title,
            style: context.text.titleMedium,
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: Gap.sm),
          Text(
            message,
            textAlign: TextAlign.center,
            style: context.text.bodyMedium?.copyWith(
              color: context.tokens.textSecondary,
            ),
          ),
          if (actionLabel != null) ...[
            const SizedBox(height: Gap.lg),
            FilledButton.tonal(onPressed: onAction, child: Text(actionLabel!)),
          ],
        ],
      ),
    );
  }
}

/// Circular 0-100 score indicator colored by quality.
class ScoreRing extends StatelessWidget {
  final int score;
  final double size;
  final double strokeWidth;
  final String? caption;

  const ScoreRing({
    super.key,
    required this.score,
    this.size = 120,
    this.strokeWidth = 10,
    this.caption,
  });

  @override
  Widget build(BuildContext context) {
    final color = context.tokens.scoreColor(score);
    final value = score.clamp(0, 100);
    return Semantics(
      label: '${caption ?? ''} $value / 100',
      excludeSemantics: true,
      child: SizedBox.square(
        dimension: size,
        child: CustomPaint(
          painter: _RingPainter(
            progress: value / 100,
            color: color,
            track: context.tokens.surfaceRaised,
            strokeWidth: strokeWidth,
          ),
          child: Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  '$value',
                  style: context.text.displaySmall?.copyWith(
                    fontSize: size * 0.3,
                    color: color,
                  ),
                ),
                if (caption != null)
                  Text(caption!, style: context.text.labelMedium),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _RingPainter extends CustomPainter {
  final double progress;
  final Color color;
  final Color track;
  final double strokeWidth;

  const _RingPainter({
    required this.progress,
    required this.color,
    required this.track,
    required this.strokeWidth,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final rect = Offset.zero & size;
    final arcRect = rect.deflate(strokeWidth / 2);
    final paint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = strokeWidth
      ..strokeCap = StrokeCap.round;

    canvas.drawArc(arcRect, 0, 2 * math.pi, false, paint..color = track);
    if (progress > 0) {
      canvas.drawArc(
        arcRect,
        -math.pi / 2,
        2 * math.pi * progress,
        false,
        paint..color = color,
      );
    }
  }

  @override
  bool shouldRepaint(covariant _RingPainter old) =>
      old.progress != progress || old.color != color || old.track != track;
}

/// App logo mark (gradient tile with a dumbbell).
class BrandMark extends StatelessWidget {
  final double size;

  const BrandMark({super.key, this.size = 44});

  @override
  Widget build(BuildContext context) {
    return ExcludeSemantics(
      child: Container(
        width: size,
        height: size,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(size * 0.28),
          gradient: const LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [Color(0xFF8B6CFF), Color(0xFF4F7BFF)],
          ),
        ),
        child: Icon(
          Icons.fitness_center_rounded,
          color: Colors.white,
          size: size * 0.52,
        ),
      ),
    );
  }
}
