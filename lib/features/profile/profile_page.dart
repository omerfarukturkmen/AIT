import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/state/analysis_history_store.dart';
import '../../../data/fake_data.dart';
import '../../../models/analysis_result_model.dart';
import '../../../widgets/glass_card.dart';
import '../../../widgets/premium_background.dart';

class ProfilePage extends StatelessWidget {
  const ProfilePage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: PremiumBackground(
        child: SafeArea(
          child: ValueListenableBuilder<List<AnalysisResult>>(
            valueListenable: AnalysisHistoryStore.results,
            builder: (context, results, child) {
              final totalAnalyses = results.length;
              final averageScore = _calculateAverageScore(results);
              final bestScore = _calculateBestScore(results);

              return SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(16, 18, 16, 24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    const _ProfileHeaderCard(),
                    const SizedBox(height: 18),
                    Row(
                      children: [
                        Expanded(
                          child: _ProfileStatCard(
                            title: 'Analiz',
                            value: '$totalAnalyses',
                            icon: Icons.analytics_rounded,
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: _ProfileStatCard(
                            title: 'Ortalama',
                            value: '$averageScore',
                            icon: Icons.speed_rounded,
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: _ProfileStatCard(
                            title: 'En İyi',
                            value: '$bestScore',
                            icon: Icons.emoji_events_rounded,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 18),
                    _WeeklyProgressChartCard(results: results),
                    const SizedBox(height: 18),
                    const _AchievementsCard(),
                    const SizedBox(height: 18),
                    const _GoalCard(),
                  ],
                ),
              );
            },
          ),
        ),
      ),
    );
  }

  int _calculateAverageScore(List<AnalysisResult> results) {
    if (results.isEmpty) return 0;

    final total = results.fold<int>(0, (sum, result) => sum + result.score);

    return (total / results.length).round();
  }

  int _calculateBestScore(List<AnalysisResult> results) {
    if (results.isEmpty) return 0;

    return results
        .map((result) => result.score)
        .reduce((current, next) => current > next ? current : next);
  }
}

class _ProfileHeaderCard extends StatelessWidget {
  const _ProfileHeaderCard();

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Column(
        children: [
          Container(
            height: 86,
            width: 86,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: const LinearGradient(
                colors: [
                  Color(0xFF5B4B8A),
                  Color(0xFF3B2A6D),
                  Color(0xFF1F1A3D),
                ],
              ),
              boxShadow: [
                BoxShadow(
                  color: AppColors.purpleGlow.withValues(alpha: 0.32),
                  blurRadius: 32,
                  offset: const Offset(0, 12),
                ),
              ],
            ),
            child: const Icon(
              Icons.person_rounded,
              color: Colors.white,
              size: 48,
            ),
          ),
          const SizedBox(height: 16),
          const Text(
            'AIT Kullanıcısı',
            style: TextStyle(fontSize: 24, fontWeight: FontWeight.w900),
          ),
          const SizedBox(height: 6),
          const Text(
            'AI destekli fitness form takibi',
            style: TextStyle(color: AppColors.textSoft),
          ),
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            decoration: BoxDecoration(
              color: AppColors.purpleGlow.withValues(alpha: 0.14),
              borderRadius: BorderRadius.circular(99),
              border: Border.all(
                color: AppColors.purpleGlow.withValues(alpha: 0.28),
              ),
            ),
            child: const Text(
              'Active Training Mode',
              style: TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.w800,
                fontSize: 13,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ProfileStatCard extends StatelessWidget {
  final String title;
  final String value;
  final IconData icon;

  const _ProfileStatCard({
    required this.title,
    required this.value,
    required this.icon,
  });

  @override
  Widget build(BuildContext context) {
    final parsedValue = int.tryParse(value) ?? 0;

    return GlassCard(
      child: Column(
        children: [
          Icon(icon, color: AppColors.purpleGlow, size: 25),
          const SizedBox(height: 10),
          TweenAnimationBuilder<int>(
            tween: IntTween(begin: 0, end: parsedValue),
            duration: const Duration(milliseconds: 900),
            curve: Curves.easeOutCubic,
            builder: (context, animatedValue, child) {
              return Text(
                '$animatedValue',
                style: const TextStyle(
                  fontSize: 26,
                  fontWeight: FontWeight.w900,
                  color: AppColors.purpleGlow,
                ),
              );
            },
          ),
          const SizedBox(height: 4),
          Text(
            title,
            textAlign: TextAlign.center,
            style: const TextStyle(color: AppColors.textSoft, fontSize: 12),
          ),
        ],
      ),
    );
  }
}

class _WeeklyProgressChartCard extends StatelessWidget {
  final List<AnalysisResult> results;

  const _WeeklyProgressChartCard({required this.results});

  List<FlSpot> get spots {
    final latest = results.take(5).toList().reversed.toList();

    if (latest.isEmpty) {
      return const [
        FlSpot(0, 0),
        FlSpot(1, 0),
        FlSpot(2, 0),
        FlSpot(3, 0),
        FlSpot(4, 0),
      ];
    }

    return List.generate(
      latest.length,
      (index) => FlSpot(index.toDouble(), latest[index].score.toDouble()),
    );
  }

  int get bestScore {
    if (results.isEmpty) return 0;

    return results
        .map((result) => result.score)
        .reduce((current, next) => current > next ? current : next);
  }

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Haftalık Gelişim',
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900),
          ),
          const SizedBox(height: 6),
          const Text(
            'Son analiz skorlarına göre form gelişimin',
            style: TextStyle(color: AppColors.textSoft, fontSize: 13),
          ),
          const SizedBox(height: 18),
          Row(
            children: [
              Expanded(
                child: _MiniMetricCard(
                  title: 'Analiz',
                  value: '${results.length}',
                  icon: Icons.analytics_rounded,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _MiniMetricCard(
                  title: 'En İyi Skor',
                  value: '$bestScore',
                  icon: Icons.emoji_events_rounded,
                ),
              ),
            ],
          ),
          const SizedBox(height: 22),
          SizedBox(
            height: 190,
            child: TweenAnimationBuilder<double>(
              tween: Tween(begin: 0, end: 1),
              duration: const Duration(milliseconds: 1200),
              curve: Curves.easeOutCubic,
              builder: (context, value, child) {
                return LineChart(
                  LineChartData(
                    minY: 0,
                    maxY: 100,
                    gridData: FlGridData(
                      show: true,
                      drawVerticalLine: false,
                      horizontalInterval: 25,
                      getDrawingHorizontalLine: (gridValue) {
                        return FlLine(
                          color: Colors.white.withValues(alpha: 0.07),
                          strokeWidth: 1,
                        );
                      },
                    ),
                    titlesData: FlTitlesData(
                      leftTitles: const AxisTitles(
                        sideTitles: SideTitles(showTitles: false),
                      ),
                      topTitles: const AxisTitles(
                        sideTitles: SideTitles(showTitles: false),
                      ),
                      rightTitles: const AxisTitles(
                        sideTitles: SideTitles(showTitles: false),
                      ),
                      bottomTitles: AxisTitles(
                        sideTitles: SideTitles(
                          showTitles: true,
                          reservedSize: 28,
                          getTitlesWidget: (dayValue, meta) {
                            const labels = ['1', '2', '3', '4', '5'];

                            if (dayValue.toInt() < 0 ||
                                dayValue.toInt() >= labels.length) {
                              return const SizedBox();
                            }

                            return Text(
                              labels[dayValue.toInt()],
                              style: const TextStyle(
                                color: AppColors.textSoft,
                                fontSize: 12,
                              ),
                            );
                          },
                        ),
                      ),
                    ),
                    borderData: FlBorderData(show: false),
                    lineBarsData: [
                      LineChartBarData(
                        spots: spots
                            .map((spot) => FlSpot(spot.x, spot.y * value))
                            .toList(),
                        isCurved: true,
                        barWidth: 5,
                        color: AppColors.purpleGlow,
                        shadow: Shadow(
                          color: AppColors.purpleGlow.withValues(alpha: 0.6),
                          blurRadius: 18,
                        ),
                        belowBarData: BarAreaData(
                          show: true,
                          gradient: LinearGradient(
                            begin: Alignment.topCenter,
                            end: Alignment.bottomCenter,
                            colors: [
                              AppColors.purpleGlow.withValues(alpha: 0.35),
                              AppColors.purple.withValues(alpha: 0.03),
                            ],
                          ),
                        ),
                        dotData: FlDotData(
                          show: true,
                          getDotPainter: (spot, percent, barData, index) {
                            return FlDotCirclePainter(
                              radius: 5,
                              color: AppColors.purpleGlow,
                              strokeWidth: 3,
                              strokeColor: Colors.white.withValues(alpha: 0.75),
                            );
                          },
                        ),
                      ),
                    ],
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _MiniMetricCard extends StatelessWidget {
  final String title;
  final String value;
  final IconData icon;

  const _MiniMetricCard({
    required this.title,
    required this.value,
    required this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            AppColors.purpleGlow.withValues(alpha: 0.18),
            Colors.white.withValues(alpha: 0.04),
          ],
        ),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AppColors.purpleGlow.withValues(alpha: 0.2)),
      ),
      child: Row(
        children: [
          Icon(icon, color: AppColors.purpleGlow, size: 22),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  value,
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 11,
                    color: AppColors.textSoft,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _AchievementsCard extends StatelessWidget {
  const _AchievementsCard();

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Rozetler',
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900),
          ),
          const SizedBox(height: 14),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: achievements.map((achievement) {
              return Container(
                width: 135,
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: achievement.isUnlocked
                      ? AppColors.purpleGlow.withValues(alpha: 0.16)
                      : Colors.white.withValues(alpha: 0.04),
                  borderRadius: BorderRadius.circular(18),
                  border: Border.all(
                    color: achievement.isUnlocked
                        ? AppColors.purpleGlow.withValues(alpha: 0.35)
                        : Colors.white.withValues(alpha: 0.10),
                  ),
                ),
                child: Column(
                  children: [
                    Icon(
                      achievement.icon,
                      color: achievement.isUnlocked
                          ? AppColors.purpleGlow
                          : AppColors.textSoft,
                      size: 28,
                    ),
                    const SizedBox(height: 8),
                    Text(
                      achievement.title,
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontWeight: FontWeight.w800,
                        color: achievement.isUnlocked
                            ? Colors.white
                            : AppColors.textSoft,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      achievement.isUnlocked ? 'Açıldı' : 'Kilitli',
                      style: const TextStyle(
                        color: AppColors.textSoft,
                        fontSize: 11,
                      ),
                    ),
                  ],
                ),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }
}

class _GoalCard extends StatelessWidget {
  const _GoalCard();

  @override
  Widget build(BuildContext context) {
    return const GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Hedef',
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900),
          ),
          SizedBox(height: 10),
          Text(
            'Fitness hareketlerinde form hatalarını azaltmak, sakatlanma riskini düşürmek ve daha güvenli antrenman alışkanlığı geliştirmek.',
            style: TextStyle(color: AppColors.textSoft, height: 1.5),
          ),
        ],
      ),
    );
  }
}
