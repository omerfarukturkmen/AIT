import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/state/body_progress_store.dart';
import '../../../models/body_progress_model.dart';
import '../../../widgets/glass_card.dart';
import '../../../widgets/premium_background.dart';

class ProgressPage extends StatelessWidget {
  const ProgressPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: PremiumBackground(
        child: SafeArea(
          child: ValueListenableBuilder<BodyProgress>(
            valueListenable: BodyProgressStore.progress,
            builder: (context, progress, child) {
              return SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(16, 18, 16, 24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    const Text(
                      'Gelişim Takibi',
                      style: TextStyle(
                        fontSize: 30,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'Kilo değişimini, hedef ilerlemeni ve vücut ölçülerindeki gelişimi takip et.',
                      style: TextStyle(color: AppColors.textSoft, height: 1.4),
                    ),
                    const SizedBox(height: 22),
                    _ProgressHeroCard(progress: progress),
                    const SizedBox(height: 16),
                    _WeightStatsGrid(progress: progress),
                    const SizedBox(height: 16),
                    _BmiCard(progress: progress),
                    const SizedBox(height: 16),
                    _WeightChartCard(progress: progress),
                    const SizedBox(height: 16),
                    _MeasurementsCard(progress: progress),
                    const SizedBox(height: 16),
                    const _ProgressInfoCard(),
                  ],
                ),
              );
            },
          ),
        ),
      ),
    );
  }
}

class _ProgressHeroCard extends StatelessWidget {
  final BodyProgress progress;

  const _ProgressHeroCard({required this.progress});

  @override
  Widget build(BuildContext context) {
    final percentage = (progress.progressRatio * 100).round();

    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(
                Icons.trending_down_rounded,
                color: AppColors.neonGreen,
                size: 34,
              ),
              const SizedBox(width: 12),
              const Expanded(
                child: Text(
                  'Hedef İlerlemesi',
                  style: TextStyle(fontSize: 21, fontWeight: FontWeight.w900),
                ),
              ),
              Text(
                '$percentage%',
                style: const TextStyle(
                  color: AppColors.neonGreen,
                  fontSize: 28,
                  fontWeight: FontWeight.w900,
                ),
              ),
            ],
          ),
          const SizedBox(height: 18),
          ClipRRect(
            borderRadius: BorderRadius.circular(99),
            child: LinearProgressIndicator(
              minHeight: 11,
              value: progress.progressRatio,
              backgroundColor: Colors.white.withValues(alpha: 0.08),
              valueColor: const AlwaysStoppedAnimation<Color>(
                AppColors.neonGreen,
              ),
            ),
          ),
          const SizedBox(height: 14),
          Text(
            '${progress.startWeight.toStringAsFixed(1)} kg başlangıçtan ${progress.currentWeight.toStringAsFixed(1)} kg seviyesine ulaşıldı.',
            style: const TextStyle(color: AppColors.textSoft, height: 1.45),
          ),
        ],
      ),
    );
  }
}

class _WeightStatsGrid extends StatelessWidget {
  final BodyProgress progress;

  const _WeightStatsGrid({required this.progress});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: _StatCard(
            title: 'Başlangıç',
            value: '${progress.startWeight.toStringAsFixed(1)} kg',
            icon: Icons.flag_rounded,
            color: AppColors.electricBlue,
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: _StatCard(
            title: 'Güncel',
            value: '${progress.currentWeight.toStringAsFixed(1)} kg',
            icon: Icons.monitor_weight_rounded,
            color: AppColors.primary,
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: _StatCard(
            title: 'Hedef',
            value: '${progress.targetWeight.toStringAsFixed(1)} kg',
            icon: Icons.track_changes_rounded,
            color: AppColors.neonGreen,
          ),
        ),
      ],
    );
  }
}

class _StatCard extends StatelessWidget {
  final String title;
  final String value;
  final IconData icon;
  final Color color;

  const _StatCard({
    required this.title,
    required this.value,
    required this.icon,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      padding: const EdgeInsets.all(14),
      child: Column(
        children: [
          Icon(icon, color: color, size: 26),
          const SizedBox(height: 10),
          Text(
            value,
            textAlign: TextAlign.center,
            style: TextStyle(
              color: color,
              fontSize: 17,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            title,
            textAlign: TextAlign.center,
            style: const TextStyle(color: AppColors.textSoft, fontSize: 11),
          ),
        ],
      ),
    );
  }
}

class _BmiCard extends StatelessWidget {
  final BodyProgress progress;

  const _BmiCard({required this.progress});

  Color get bmiColor {
    final bmi = progress.bmi;

    if (bmi < 18.5) return Colors.orangeAccent;
    if (bmi < 25) return AppColors.neonGreen;
    if (bmi < 30) return AppColors.orange;
    return AppColors.red;
  }

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Row(
        children: [
          Container(
            height: 58,
            width: 58,
            decoration: BoxDecoration(
              color: bmiColor.withValues(alpha: 0.13),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: bmiColor.withValues(alpha: 0.28)),
            ),
            child: Icon(
              Icons.health_and_safety_rounded,
              color: bmiColor,
              size: 31,
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'BMI / VKİ',
                  style: TextStyle(color: AppColors.textSoft, fontSize: 13),
                ),
                const SizedBox(height: 4),
                Text(
                  progress.bmi.toStringAsFixed(1),
                  style: TextStyle(
                    color: bmiColor,
                    fontSize: 27,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  progress.bmiStatus,
                  style: const TextStyle(
                    color: AppColors.textSoft,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              const Text(
                'Verilen',
                style: TextStyle(color: AppColors.textSoft, fontSize: 12),
              ),
              const SizedBox(height: 4),
              Text(
                '-${progress.lostWeight.toStringAsFixed(1)} kg',
                style: const TextStyle(
                  color: AppColors.neonGreen,
                  fontSize: 21,
                  fontWeight: FontWeight.w900,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _WeightChartCard extends StatelessWidget {
  final BodyProgress progress;

  const _WeightChartCard({required this.progress});

  @override
  Widget build(BuildContext context) {
    final weights = progress.weeklyWeights;

    final minWeight =
        weights.map((entry) => entry.weight).reduce((a, b) => a < b ? a : b) -
        1;

    final maxWeight =
        weights.map((entry) => entry.weight).reduce((a, b) => a > b ? a : b) +
        1;

    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Haftalık Kilo Grafiği',
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900),
          ),
          const SizedBox(height: 6),
          const Text(
            'Haftalara göre kilo değişim trendin',
            style: TextStyle(color: AppColors.textSoft, fontSize: 13),
          ),
          const SizedBox(height: 22),
          SizedBox(
            height: 210,
            child: LineChart(
              LineChartData(
                minY: minWeight,
                maxY: maxWeight,
                gridData: FlGridData(
                  show: true,
                  drawVerticalLine: false,
                  horizontalInterval: 1,
                  getDrawingHorizontalLine: (value) {
                    return FlLine(
                      color: Colors.white.withValues(alpha: 0.07),
                      strokeWidth: 1,
                    );
                  },
                ),
                borderData: FlBorderData(show: false),
                titlesData: FlTitlesData(
                  leftTitles: const AxisTitles(
                    sideTitles: SideTitles(showTitles: false),
                  ),
                  rightTitles: const AxisTitles(
                    sideTitles: SideTitles(showTitles: false),
                  ),
                  topTitles: const AxisTitles(
                    sideTitles: SideTitles(showTitles: false),
                  ),
                  bottomTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      reservedSize: 28,
                      getTitlesWidget: (value, meta) {
                        final index = value.toInt();

                        if (index < 0 || index >= weights.length) {
                          return const SizedBox();
                        }

                        return Text(
                          '${index + 1}',
                          style: const TextStyle(
                            color: AppColors.textSoft,
                            fontSize: 12,
                          ),
                        );
                      },
                    ),
                  ),
                ),
                lineBarsData: [
                  LineChartBarData(
                    spots: List.generate(
                      weights.length,
                      (index) =>
                          FlSpot(index.toDouble(), weights[index].weight),
                    ),
                    isCurved: true,
                    barWidth: 5,
                    color: AppColors.neonGreen,
                    shadow: Shadow(
                      color: AppColors.neonGreen.withValues(alpha: 0.45),
                      blurRadius: 16,
                    ),
                    belowBarData: BarAreaData(
                      show: true,
                      gradient: LinearGradient(
                        begin: Alignment.topCenter,
                        end: Alignment.bottomCenter,
                        colors: [
                          AppColors.neonGreen.withValues(alpha: 0.28),
                          AppColors.neonGreen.withValues(alpha: 0.02),
                        ],
                      ),
                    ),
                    dotData: FlDotData(
                      show: true,
                      getDotPainter: (spot, percent, barData, index) {
                        return FlDotCirclePainter(
                          radius: 5,
                          color: AppColors.neonGreen,
                          strokeWidth: 3,
                          strokeColor: Colors.white.withValues(alpha: 0.75),
                        );
                      },
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _MeasurementsCard extends StatelessWidget {
  final BodyProgress progress;

  const _MeasurementsCard({required this.progress});

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Vücut Ölçüleri',
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900),
          ),
          const SizedBox(height: 14),
          ...progress.measurements.map(
            (measurement) => Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: _MeasurementRow(measurement: measurement),
            ),
          ),
        ],
      ),
    );
  }
}

class _MeasurementRow extends StatelessWidget {
  final BodyMeasurement measurement;

  const _MeasurementRow({required this.measurement});

  @override
  Widget build(BuildContext context) {
    final difference = measurement.difference;
    final isReduced = difference < 0;
    final color = isReduced ? AppColors.neonGreen : Colors.orangeAccent;

    return Container(
      padding: const EdgeInsets.all(13),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.045),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: Colors.white.withValues(alpha: 0.09)),
      ),
      child: Row(
        children: [
          Container(
            height: 42,
            width: 42,
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.13),
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: color.withValues(alpha: 0.24)),
            ),
            child: Icon(
              isReduced
                  ? Icons.trending_down_rounded
                  : Icons.trending_up_rounded,
              color: color,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              measurement.title,
              style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w900),
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                '${measurement.startValue.toStringAsFixed(0)} → ${measurement.currentValue.toStringAsFixed(0)} ${measurement.unit}',
                style: const TextStyle(fontWeight: FontWeight.w800),
              ),
              const SizedBox(height: 3),
              Text(
                '${difference.toStringAsFixed(1)} ${measurement.unit}',
                style: TextStyle(
                  color: color,
                  fontSize: 12,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _ProgressInfoCard extends StatelessWidget {
  const _ProgressInfoCard();

  @override
  Widget build(BuildContext context) {
    return const GlassCard(
      child: Row(
        children: [
          Icon(Icons.info_outline_rounded, color: AppColors.electricBlue),
          SizedBox(width: 12),
          Expanded(
            child: Text(
              'Bu ekran demo gelişim verileriyle hazırlanmıştır. Backend hazır olduğunda kilo ve vücut ölçümleri kullanıcı hesabına bağlı olarak kaydedilebilir.',
              style: TextStyle(
                color: AppColors.textSoft,
                height: 1.45,
                fontSize: 13,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
