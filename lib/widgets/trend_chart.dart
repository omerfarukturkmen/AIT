import 'dart:math' as math;

import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../core/theme/app_theme.dart';

class TrendPoint {
  final DateTime date;
  final double value;

  const TrendPoint(this.date, this.value);
}

/// Single-series line over time: 2px line, ringed markers, faint area wash,
/// hairline grid and a touch tooltip. One series, so no legend; the section
/// title names it. Screen readers get a text summary.
class TrendChart extends StatelessWidget {
  final List<TrendPoint> points;
  final String Function(double value) format;
  final String semanticsLabel;
  final double? minY;
  final double? maxY;
  final double height;

  const TrendChart({
    super.key,
    required this.points,
    required this.format,
    required this.semanticsLabel,
    this.minY,
    this.maxY,
    this.height = 200,
  });

  @override
  Widget build(BuildContext context) {
    final color = context.colors.primary;
    final tokens = context.tokens;
    final locale = Localizations.localeOf(context).toLanguageTag();
    final dateFormat = DateFormat.MMMd(locale);

    final sorted = [...points]..sort((a, b) => a.date.compareTo(b.date));
    final origin = sorted.first.date;
    double x(DateTime date) => date.difference(origin).inHours / 24;

    final values = sorted.map((p) => p.value);
    final low = values.reduce(math.min);
    final high = values.reduce(math.max);
    final padding = math.max((high - low) * 0.15, 1.0);
    final yMin = minY ?? (low - padding);
    final yMax = maxY ?? (high + padding);
    final spanX = math.max(x(sorted.last.date), 1.0);

    final summary =
        '$semanticsLabel: ${format(sorted.first.value)} → ${format(sorted.last.value)}, '
        'min ${format(low)}, max ${format(high)}';

    return Semantics(
      label: summary,
      excludeSemantics: true,
      child: SizedBox(
        height: height,
        child: LineChart(
          LineChartData(
            minX: 0,
            maxX: spanX,
            minY: yMin,
            maxY: yMax,
            gridData: FlGridData(
              drawVerticalLine: false,
              horizontalInterval: (yMax - yMin) / 4,
              getDrawingHorizontalLine: (_) =>
                  FlLine(color: tokens.border, strokeWidth: 1),
            ),
            borderData: FlBorderData(show: false),
            titlesData: FlTitlesData(
              topTitles: const AxisTitles(),
              rightTitles: const AxisTitles(),
              leftTitles: AxisTitles(
                sideTitles: SideTitles(
                  showTitles: true,
                  reservedSize: 40,
                  interval: (yMax - yMin) / 4,
                  getTitlesWidget: (value, meta) {
                    if (value == meta.min || value == meta.max) {
                      return const SizedBox.shrink();
                    }
                    return Text(format(value), style: context.text.labelSmall);
                  },
                ),
              ),
              bottomTitles: AxisTitles(
                sideTitles: SideTitles(
                  showTitles: true,
                  reservedSize: 26,
                  interval: spanX,
                  getTitlesWidget: (value, meta) {
                    final date = origin.add(
                      Duration(hours: (value * 24).round()),
                    );
                    return Padding(
                      padding: const EdgeInsets.only(top: Gap.xs),
                      child: Text(
                        dateFormat.format(date),
                        style: context.text.labelSmall,
                      ),
                    );
                  },
                ),
              ),
            ),
            lineTouchData: LineTouchData(
              touchTooltipData: LineTouchTooltipData(
                getTooltipColor: (_) => context.colors.inverseSurface,
                tooltipRoundedRadius: Radii.sm,
                getTooltipItems: (spots) => [
                  for (final spot in spots)
                    LineTooltipItem(
                      '${format(spot.y)}\n',
                      context.text.labelLarge!.copyWith(
                        color: context.colors.onInverseSurface,
                      ),
                      children: [
                        TextSpan(
                          text: dateFormat.format(sorted[spot.spotIndex].date),
                          style: context.text.labelSmall?.copyWith(
                            color: context.colors.onInverseSurface.withValues(
                              alpha: 0.7,
                            ),
                          ),
                        ),
                      ],
                    ),
                ],
              ),
            ),
            lineBarsData: [
              LineChartBarData(
                spots: [for (final p in sorted) FlSpot(x(p.date), p.value)],
                barWidth: 2,
                isCurved: false,
                isStrokeCapRound: true,
                isStrokeJoinRound: true,
                color: color,
                belowBarData: BarAreaData(
                  show: true,
                  color: color.withValues(alpha: 0.1),
                ),
                dotData: FlDotData(
                  getDotPainter: (spot, percent, bar, index) =>
                      FlDotCirclePainter(
                        radius: 4,
                        color: color,
                        strokeWidth: 2,
                        strokeColor: context.colors.surface,
                      ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
