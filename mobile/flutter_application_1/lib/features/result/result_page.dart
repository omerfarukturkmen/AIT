import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';
import '../../../models/analysis_result_model.dart';
import '../../../widgets/glass_card.dart';
import '../../../widgets/premium_background.dart';
import '../../../widgets/premium_button.dart';

class ResultPage extends StatelessWidget {
  final AnalysisResult result;

  const ResultPage({
    super.key,
    required this.result,
  });

  String get scoreLabel {
    if (result.score >= 90) return 'Excellent';
    if (result.score >= 75) return 'Good';
    if (result.score >= 50) return 'Needs Improvement';
    return 'Risky Form';
  }

  String get riskLevel {
    if (result.score >= 90) return 'Very Low Risk';
    if (result.score >= 75) return 'Low Risk';
    if (result.score >= 50) return 'Medium Risk';
    return 'High Risk';
  }

  Color get scoreColor {
    if (result.score >= 90) return Colors.greenAccent;
    if (result.score >= 75) return AppColors.purpleGlow;
    if (result.score >= 50) return Colors.orangeAccent;
    return Colors.redAccent;
  }

  String get scoreDescription {
    if (result.score >= 90) {
      return 'Formun oldukça iyi görünüyor. Küçük düzeltmelerle hareket kaliten daha da artabilir.';
    }

    if (result.score >= 75) {
      return 'Genel formun iyi seviyede. Bazı teknik detaylarda iyileştirme öneriliyor.';
    }

    if (result.score >= 50) {
      return 'Hareket formunda dikkat edilmesi gereken hatalar var. Kontrollü tekrar önerilir.';
    }

    return 'Form hataları sakatlanma riskini artırabilir. Hareketi daha yavaş ve kontrollü çalışmalısın.';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: PremiumBackground(
        child: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(16, 18, 16, 24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                _ResultHeader(
                  onBackPressed: () => Navigator.pop(context),
                ),
                const SizedBox(height: 14),
                _StatusBadgesRow(
                  scoreColor: scoreColor,
                  scoreLabel: scoreLabel,
                ),
                const SizedBox(height: 16),
                _ScoreReportCard(
                  result: result,
                  scoreLabel: scoreLabel,
                  scoreColor: scoreColor,
                  scoreDescription: scoreDescription,
                ),
                const SizedBox(height: 16),
                _RiskLevelCard(
                  riskLevel: riskLevel,
                  scoreColor: scoreColor,
                  score: result.score,
                ),
                const SizedBox(height: 16),
                _MetricsGrid(result: result),
                const SizedBox(height: 16),
                _InfoCard(
                  title: 'Tespit Edilen Form Hataları',
                  icon: Icons.warning_amber_rounded,
                  items: result.mistakes,
                  iconColor: Colors.orangeAccent,
                ),
                const SizedBox(height: 16),
                _InfoCard(
                  title: 'Antrenman Tavsiyeleri',
                  icon: Icons.lightbulb_rounded,
                  items: result.recommendations,
                  iconColor: AppColors.purpleGlow,
                ),
                const SizedBox(height: 16),
                const _ApiReadyInfoCard(),
                const SizedBox(height: 18),
                PremiumButton(
                  icon: Icons.replay_rounded,
                  text: 'Başka Video Analiz Et',
                  onPressed: () {
                    Navigator.pop(context);
                  },
                ),
                const SizedBox(height: 12),
                OutlinedButton.icon(
                  onPressed: () {
                    Navigator.popUntil(context, (route) => route.isFirst);
                  },
                  icon: const Icon(Icons.home_rounded),
                  label: const Text('Ana Sayfaya Dön'),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: Colors.white,
                    side: BorderSide(
                      color: AppColors.purpleGlow.withValues(alpha: 0.40),
                    ),
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(18),
                    ),
                    textStyle: const TextStyle(
                      fontWeight: FontWeight.w800,
                      fontSize: 16,
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

class _ResultHeader extends StatelessWidget {
  final VoidCallback onBackPressed;

  const _ResultHeader({
    required this.onBackPressed,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        IconButton(
          onPressed: onBackPressed,
          icon: const Icon(Icons.arrow_back_rounded),
        ),
        const Expanded(
          child: Text(
            'AI Analiz Raporu',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 21,
              fontWeight: FontWeight.w900,
            ),
          ),
        ),
        const SizedBox(width: 48),
      ],
    );
  }
}

class _StatusBadgesRow extends StatelessWidget {
  final Color scoreColor;
  final String scoreLabel;

  const _StatusBadgesRow({
    required this.scoreColor,
    required this.scoreLabel,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        _StatusBadge(
          text: 'Demo AI Result',
          color: scoreColor,
          icon: Icons.auto_awesome_rounded,
        ),
        const SizedBox(width: 10),
        const _StatusBadge(
          text: 'API Ready',
          color: AppColors.purpleGlow,
          icon: Icons.cloud_done_rounded,
        ),
        const Spacer(),
        _StatusBadge(
          text: scoreLabel,
          color: scoreColor,
          icon: Icons.verified_rounded,
        ),
      ],
    );
  }
}

class _ScoreReportCard extends StatelessWidget {
  final AnalysisResult result;
  final String scoreLabel;
  final Color scoreColor;
  final String scoreDescription;

  const _ScoreReportCard({
    required this.result,
    required this.scoreLabel,
    required this.scoreColor,
    required this.scoreDescription,
  });

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: TweenAnimationBuilder<int>(
        tween: IntTween(begin: 0, end: result.score),
        duration: const Duration(milliseconds: 1200),
        curve: Curves.easeOutCubic,
        builder: (context, value, child) {
          return Column(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              Text(
                result.exerciseName,
                style: const TextStyle(
                  color: AppColors.textSoft,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 8),
              const Text(
                'Genel Form Skoru',
                style: TextStyle(
                  color: AppColors.textSoft,
                ),
              ),
              const SizedBox(height: 12),
              Text(
                '$value/100',
                style: TextStyle(
                  fontSize: 58,
                  fontWeight: FontWeight.w900,
                  color: scoreColor,
                  letterSpacing: -1.2,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                scoreLabel,
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w900,
                  fontSize: 17,
                ),
              ),
              const SizedBox(height: 16),
              ClipRRect(
                borderRadius: BorderRadius.circular(99),
                child: LinearProgressIndicator(
                  minHeight: 9,
                  value: result.score / 100,
                  backgroundColor: Colors.white.withValues(alpha: 0.08),
                  valueColor: AlwaysStoppedAnimation<Color>(scoreColor),
                ),
              ),
              const SizedBox(height: 16),
              Text(
                scoreDescription,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  color: AppColors.textSoft,
                  height: 1.5,
                  fontSize: 13,
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}

class _RiskLevelCard extends StatelessWidget {
  final String riskLevel;
  final Color scoreColor;
  final int score;

  const _RiskLevelCard({
    required this.riskLevel,
    required this.scoreColor,
    required this.score,
  });

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Row(
        children: [
          Container(
            height: 54,
            width: 54,
            decoration: BoxDecoration(
              color: scoreColor.withValues(alpha: 0.14),
              borderRadius: BorderRadius.circular(18),
              border: Border.all(
                color: scoreColor.withValues(alpha: 0.28),
              ),
            ),
            child: Icon(
              Icons.health_and_safety_rounded,
              color: scoreColor,
              size: 29,
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Risk Seviyesi',
                  style: TextStyle(
                    color: AppColors.textSoft,
                    fontSize: 13,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  riskLevel,
                  style: TextStyle(
                    color: scoreColor,
                    fontSize: 19,
                    fontWeight: FontWeight.w900,
                  ),
                ),
              ],
            ),
          ),
          Text(
            '$score%',
            style: TextStyle(
              color: scoreColor,
              fontSize: 22,
              fontWeight: FontWeight.w900,
            ),
          ),
        ],
      ),
    );
  }
}

class _MetricsGrid extends StatelessWidget {
  final AnalysisResult result;

  const _MetricsGrid({
    required this.result,
  });

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Analiz Metrikleri',
            style: TextStyle(
              fontSize: 19,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: _MetricItem(
                  icon: Icons.repeat_rounded,
                  title: 'Tekrar',
                  value: '${result.repetitionCount}',
                ),
              ),
              Expanded(
                child: _MetricItem(
                  icon: Icons.psychology_rounded,
                  title: 'AI Güveni',
                  value: '${result.confidence}%',
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          Row(
            children: [
              Expanded(
                child: _MetricItem(
                  icon: Icons.timer_rounded,
                  title: 'Süre',
                  value: result.duration,
                ),
              ),
              Expanded(
                child: _MetricItem(
                  icon: Icons.architecture_rounded,
                  title: 'Hareket Açısı',
                  value: result.movementAngle,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _MetricItem extends StatelessWidget {
  final IconData icon;
  final String title;
  final String value;

  const _MetricItem({
    required this.icon,
    required this.title,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 5),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.045),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(
          color: Colors.white.withValues(alpha: 0.09),
        ),
      ),
      child: Column(
        children: [
          Icon(
            icon,
            color: AppColors.purpleGlow,
            size: 26,
          ),
          const SizedBox(height: 8),
          Text(
            value,
            style: const TextStyle(
              fontWeight: FontWeight.w900,
              fontSize: 18,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            title,
            textAlign: TextAlign.center,
            style: const TextStyle(
              color: AppColors.textSoft,
              fontSize: 12,
            ),
          ),
        ],
      ),
    );
  }
}

class _InfoCard extends StatelessWidget {
  final String title;
  final IconData icon;
  final List<String> items;
  final Color iconColor;

  const _InfoCard({
    required this.title,
    required this.icon,
    required this.items,
    required this.iconColor,
  });

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                icon,
                color: iconColor,
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  title,
                  style: const TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.w900,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          ...items.map(
            (item) => Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(
                    Icons.check_circle_rounded,
                    size: 18,
                    color: iconColor,
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      item,
                      style: const TextStyle(
                        height: 1.4,
                      ),
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

class _ApiReadyInfoCard extends StatelessWidget {
  const _ApiReadyInfoCard();

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Row(
        children: [
          Container(
            height: 48,
            width: 48,
            decoration: BoxDecoration(
              color: AppColors.purpleGlow.withValues(alpha: 0.14),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: AppColors.purpleGlow.withValues(alpha: 0.25),
              ),
            ),
            child: const Icon(
              Icons.cloud_sync_rounded,
              color: AppColors.purpleGlow,
            ),
          ),
          const SizedBox(width: 12),
          const Expanded(
            child: Text(
              'Bu sonuç demo servis ile oluşturulmuştur. Backend API hazır olduğunda aynı Result model yapısı gerçek analiz verileriyle çalışacaktır.',
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

class _StatusBadge extends StatelessWidget {
  final String text;
  final Color color;
  final IconData icon;

  const _StatusBadge({
    required this.text,
    required this.color,
    required this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: 10,
        vertical: 7,
      ),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.14),
        borderRadius: BorderRadius.circular(99),
        border: Border.all(
          color: color.withValues(alpha: 0.30),
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            icon,
            color: color,
            size: 14,
          ),
          const SizedBox(width: 5),
          Text(
            text,
            style: TextStyle(
              color: color,
              fontWeight: FontWeight.w900,
              fontSize: 10,
            ),
          ),
        ],
      ),
    );
  }
}