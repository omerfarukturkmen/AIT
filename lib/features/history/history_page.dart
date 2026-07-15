import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/state/analysis_history_store.dart';
import '../../../models/analysis_result_model.dart';
import '../../../widgets/glass_card.dart';
import '../../../widgets/premium_background.dart';

class HistoryPage extends StatelessWidget {
  const HistoryPage({super.key});

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
                    const Text(
                      'Analiz Geçmişi',
                      style: TextStyle(
                        fontSize: 30,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'Önceki antrenman analizlerini ve form gelişimini takip et.',
                      style: TextStyle(color: AppColors.textSoft, height: 1.4),
                    ),
                    const SizedBox(height: 22),
                    Row(
                      children: [
                        Expanded(
                          child: _SummaryCard(
                            title: 'Analiz',
                            value: '$totalAnalyses',
                            icon: Icons.analytics_rounded,
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: _SummaryCard(
                            title: 'Ortalama',
                            value: '$averageScore',
                            icon: Icons.speed_rounded,
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: _SummaryCard(
                            title: 'En İyi',
                            value: '$bestScore',
                            icon: Icons.emoji_events_rounded,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 22),
                    Row(
                      children: [
                        const Expanded(
                          child: Text(
                            'Son Analizler',
                            style: TextStyle(
                              fontSize: 20,
                              fontWeight: FontWeight.w900,
                            ),
                          ),
                        ),
                        if (results.isNotEmpty)
                          TextButton.icon(
                            onPressed: () {
                              AnalysisHistoryStore.clearHistory();
                            },
                            icon: const Icon(Icons.delete_outline_rounded),
                            label: const Text('Temizle'),
                            style: TextButton.styleFrom(
                              foregroundColor: AppColors.textSoft,
                            ),
                          ),
                      ],
                    ),
                    const SizedBox(height: 14),
                    if (results.isEmpty)
                      const _EmptyHistoryView()
                    else
                      ...results.map(
                        (result) => Padding(
                          padding: const EdgeInsets.only(bottom: 14),
                          child: _HistoryAnalysisCard(result: result),
                        ),
                      ),
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

class _SummaryCard extends StatelessWidget {
  final String title;
  final String value;
  final IconData icon;

  const _SummaryCard({
    required this.title,
    required this.value,
    required this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Column(
        children: [
          Icon(icon, color: AppColors.purpleGlow, size: 26),
          const SizedBox(height: 10),
          TweenAnimationBuilder<int>(
            tween: IntTween(begin: 0, end: int.tryParse(value) ?? 0),
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

class _HistoryAnalysisCard extends StatelessWidget {
  final AnalysisResult result;

  const _HistoryAnalysisCard({required this.result});

  String get scoreLabel {
    if (result.score >= 90) return 'Excellent';
    if (result.score >= 75) return 'Good';
    if (result.score >= 50) return 'Needs Improvement';
    return 'Risky Form';
  }

  Color get scoreColor {
    if (result.score >= 90) return Colors.greenAccent;
    if (result.score >= 75) return AppColors.purpleGlow;
    if (result.score >= 50) return Colors.orangeAccent;
    return Colors.redAccent;
  }

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              _ExerciseIconBox(exerciseName: result.exerciseName),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      result.exerciseName,
                      style: const TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    const SizedBox(height: 4),
                    const Text(
                      'Video analizi • Demo AI Result',
                      style: TextStyle(color: AppColors.textSoft, fontSize: 12),
                    ),
                  ],
                ),
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    '${result.score}',
                    style: TextStyle(
                      fontSize: 28,
                      fontWeight: FontWeight.w900,
                      color: scoreColor,
                    ),
                  ),
                  Text(
                    scoreLabel,
                    style: const TextStyle(
                      color: AppColors.textSoft,
                      fontSize: 11,
                    ),
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 16),
          ClipRRect(
            borderRadius: BorderRadius.circular(99),
            child: LinearProgressIndicator(
              minHeight: 8,
              value: result.score / 100,
              backgroundColor: Colors.white.withValues(alpha: 0.08),
              valueColor: AlwaysStoppedAnimation<Color>(scoreColor),
            ),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: _MiniInfo(
                  title: 'Tekrar',
                  value: '${result.repetitionCount}',
                  icon: Icons.repeat_rounded,
                ),
              ),
              Expanded(
                child: _MiniInfo(
                  title: 'Açı',
                  value: result.movementAngle,
                  icon: Icons.architecture_rounded,
                ),
              ),
              Expanded(
                child: _MiniInfo(
                  title: 'Güven',
                  value: '${result.confidence}%',
                  icon: Icons.psychology_rounded,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _ExerciseIconBox extends StatelessWidget {
  final String exerciseName;

  const _ExerciseIconBox({required this.exerciseName});

  IconData get icon {
    switch (exerciseName) {
      case 'Squat':
        return Icons.fitness_center_rounded;
      case 'Push-up':
        return Icons.accessibility_new_rounded;
      case 'Plank':
        return Icons.self_improvement_rounded;
      case 'Lunge':
        return Icons.directions_run_rounded;
      default:
        return Icons.sports_gymnastics_rounded;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 54,
      width: 54,
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF5B4B8A), Color(0xFF3B2A6D), Color(0xFF1F1A3D)],
        ),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: Colors.white.withValues(alpha: 0.18)),
      ),
      child: Icon(icon, color: Colors.white, size: 28),
    );
  }
}

class _MiniInfo extends StatelessWidget {
  final String title;
  final String value;
  final IconData icon;

  const _MiniInfo({
    required this.title,
    required this.value,
    required this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Icon(icon, color: AppColors.purpleGlow, size: 20),
        const SizedBox(height: 6),
        Text(
          value,
          style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 14),
        ),
        const SizedBox(height: 3),
        Text(
          title,
          style: const TextStyle(color: AppColors.textSoft, fontSize: 11),
        ),
      ],
    );
  }
}

class _EmptyHistoryView extends StatelessWidget {
  const _EmptyHistoryView();

  @override
  Widget build(BuildContext context) {
    return const GlassCard(
      child: Column(
        children: [
          Icon(Icons.history_rounded, color: AppColors.textSoft, size: 48),
          SizedBox(height: 14),
          Text(
            'Henüz analiz geçmişi yok.',
            style: TextStyle(fontWeight: FontWeight.w900, fontSize: 18),
          ),
          SizedBox(height: 8),
          Text(
            'İlk video analizini yaptığında sonuçların burada görünecek.',
            textAlign: TextAlign.center,
            style: TextStyle(color: AppColors.textSoft, height: 1.4),
          ),
        ],
      ),
    );
  }
}
