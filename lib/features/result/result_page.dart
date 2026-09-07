import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';
import '../../../models/analysis_result_model.dart';
import '../../../widgets/glass_card.dart';
import '../../../widgets/premium_background.dart';
import '../../../widgets/premium_button.dart';

class ResultPage extends StatelessWidget {
  final AnalysisResult result;

  const ResultPage({super.key, required this.result});

  String get scoreLabel {
    if (result.score >= 90) return 'Mükemmel';
    if (result.score >= 75) return 'İyi';
    if (result.score >= 50) return 'Geliştirilmeli';
    return 'Riskli Form';
  }

  String get riskLevel {
    if (result.score >= 90) return 'Çok Düşük Risk';
    if (result.score >= 75) return 'Düşük Risk';
    if (result.score >= 50) return 'Orta Risk';
    return 'Yüksek Risk';
  }

  Color get scoreColor {
    if (result.score >= 90) return Colors.greenAccent;
    if (result.score >= 75) return AppColors.purpleGlow;
    if (result.score >= 50) return Colors.orangeAccent;
    return Colors.redAccent;
  }

  String get formattedDate {
    final now = DateTime.now();
    final day = now.day.toString().padLeft(2, '0');
    final month = now.month.toString().padLeft(2, '0');
    final year = now.year.toString();
    final hour = now.hour.toString().padLeft(2, '0');
    final minute = now.minute.toString().padLeft(2, '0');

    return '$day.$month.$year - $hour:$minute';
  }

  String get scoreDescription {
    if (result.score >= 90) {
      return 'Formun oldukça iyi görünüyor. Küçük teknik düzeltmelerle hareket kaliten daha da artabilir.';
    }

    if (result.score >= 75) {
      return 'Genel formun iyi seviyede. Bazı teknik detaylarda iyileştirme öneriliyor.';
    }

    if (result.score >= 50) {
      return 'Hareket formunda dikkat edilmesi gereken hatalar var. Kontrollü tekrar önerilir.';
    }

    return 'Form hataları sakatlanma riskini artırabilir. Hareketi daha yavaş ve kontrollü çalışmalısın.';
  }

  String _correctionForMistake(String mistake) {
    final lowerMistake = mistake.toLowerCase();
    final lowerExercise = result.exerciseName.toLowerCase();

    if (lowerExercise.contains('squat')) {
      if (lowerMistake.contains('diz')) {
        return 'Dizlerini içeri kapatma; dizlerini ayak parmaklarınla aynı hatta tut.';
      }
      if (lowerMistake.contains('sırt') || lowerMistake.contains('gövde')) {
        return 'Göğsünü açık tut, sırtını nötr pozisyonda koru ve kontrollü in.';
      }
      if (lowerMistake.contains('kontrollü') || lowerMistake.contains('hız')) {
        return 'İniş fazını yavaşlat, kalkarken ağırlığı topuklarına dengeli aktar.';
      }
      return 'Squat sırasında ayaklarını omuz genişliğinde aç, kalçanı geriye al ve kontrollü tekrar yap.';
    }

    if (lowerExercise.contains('push')) {
      if (lowerMistake.contains('kalça') || lowerMistake.contains('core')) {
        return 'Karın bölgeni sıkı tut, omuz-kalça-ayak hattını düz koru.';
      }
      if (lowerMistake.contains('dirsek')) {
        return 'Dirseklerini fazla dışa açma; gövdene yaklaşık 45 derece açıyla indir.';
      }
      if (lowerMistake.contains('omuz')) {
        return 'Omuzlarını kulaklarına yaklaştırma; kürek kemiklerini kontrollü tut.';
      }
      return 'Push-up sırasında gövdeni tek çizgi halinde tut ve göğsünü kontrollü şekilde indir.';
    }

    if (lowerExercise.contains('plank')) {
      if (lowerMistake.contains('bel') || lowerMistake.contains('kalça')) {
        return 'Belini çökertme, kalçanı aşırı kaldırma; core bölgeni aktif tut.';
      }
      return 'Plank sırasında omuz, kalça ve ayak hizanı sabit tut.';
    }

    if (lowerMistake.contains('hata') || lowerMistake.contains('teknik')) {
      return 'Hareketi daha yavaş yap, eklem hizalarını koru ve aynada/kamerada formunu kontrol et.';
    }

    return 'Hareketi kontrollü tempoda tekrar et, duruşunu koru ve kamerada tüm vücudunun göründüğünden emin ol.';
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
                _ResultHeader(onBackPressed: () => Navigator.pop(context)),
                const SizedBox(height: 14),
                _StatusBadgesRow(
                  scoreColor: scoreColor,
                  scoreLabel: scoreLabel,
                ),
                const SizedBox(height: 16),
                _AnalysisSummaryCard(
                  exerciseName: result.exerciseName,
                  formattedDate: formattedDate,
                  score: result.score,
                  repetitionCount: result.repetitionCount,
                  scoreColor: scoreColor,
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
                _MistakesWithCorrectionsCard(
                  mistakes: result.mistakes,
                  correctionBuilder: _correctionForMistake,
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

  const _ResultHeader({required this.onBackPressed});

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
            style: TextStyle(fontSize: 21, fontWeight: FontWeight.w900),
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

  const _StatusBadgesRow({required this.scoreColor, required this.scoreLabel});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: [
          _StatusBadge(
            text: 'Backend AI Result',
            color: scoreColor,
            icon: Icons.auto_awesome_rounded,
          ),
          const SizedBox(width: 10),
          const _StatusBadge(
            text: 'API Connected',
            color: AppColors.purpleGlow,
            icon: Icons.cloud_done_rounded,
          ),
          const SizedBox(width: 10),
          _StatusBadge(
            text: scoreLabel,
            color: scoreColor,
            icon: Icons.verified_rounded,
          ),
        ],
      ),
    );
  }
}

class _AnalysisSummaryCard extends StatelessWidget {
  final String exerciseName;
  final String formattedDate;
  final int score;
  final int repetitionCount;
  final Color scoreColor;

  const _AnalysisSummaryCard({
    required this.exerciseName,
    required this.formattedDate,
    required this.score,
    required this.repetitionCount,
    required this.scoreColor,
  });

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(
                Icons.assignment_turned_in_rounded,
                color: AppColors.purpleGlow,
              ),
              SizedBox(width: 10),
              Expanded(
                child: Text(
                  'Analiz Özeti',
                  style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: _SummaryBox(
                  title: 'Hareket',
                  value: exerciseName,
                  icon: Icons.fitness_center_rounded,
                  color: AppColors.purpleGlow,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _SummaryBox(
                  title: 'Tarih',
                  value: formattedDate,
                  icon: Icons.calendar_month_rounded,
                  color: Colors.lightBlueAccent,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(
                child: _SummaryBox(
                  title: 'Skor',
                  value: '$score/100',
                  icon: Icons.speed_rounded,
                  color: scoreColor,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _SummaryBox(
                  title: 'Tekrar / Frame',
                  value: '$repetitionCount',
                  icon: Icons.repeat_rounded,
                  color: Colors.greenAccent,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _SummaryBox extends StatelessWidget {
  final String title;
  final String value;
  final IconData icon;
  final Color color;

  const _SummaryBox({
    required this.title,
    required this.value,
    required this.icon,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(13),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: color.withValues(alpha: 0.25)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: color, size: 22),
          const SizedBox(height: 8),
          Text(
            value,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: TextStyle(
              color: color,
              fontWeight: FontWeight.w900,
              fontSize: 16,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            title,
            style: const TextStyle(color: AppColors.textSoft, fontSize: 11),
          ),
        ],
      ),
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
                style: TextStyle(color: AppColors.textSoft),
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
              border: Border.all(color: scoreColor.withValues(alpha: 0.28)),
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
                  style: TextStyle(color: AppColors.textSoft, fontSize: 13),
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

  const _MetricsGrid({required this.result});

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Analiz Metrikleri',
            style: TextStyle(fontSize: 19, fontWeight: FontWeight.w900),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: _MetricItem(
                  icon: Icons.repeat_rounded,
                  title: 'Tekrar / Frame',
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
                  title: 'Ortalama Hareket',
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
        border: Border.all(color: Colors.white.withValues(alpha: 0.09)),
      ),
      child: Column(
        children: [
          Icon(icon, color: AppColors.purpleGlow, size: 26),
          const SizedBox(height: 8),
          Text(
            value,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 18),
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

class _MistakesWithCorrectionsCard extends StatelessWidget {
  final List<String> mistakes;
  final String Function(String mistake) correctionBuilder;

  const _MistakesWithCorrectionsCard({
    required this.mistakes,
    required this.correctionBuilder,
  });

  @override
  Widget build(BuildContext context) {
    final safeMistakes = mistakes.isEmpty
        ? ['Belirgin form hatası algılanmadı.']
        : mistakes;

    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.warning_amber_rounded, color: Colors.orangeAccent),
              SizedBox(width: 10),
              Expanded(
                child: Text(
                  'Tespit Edilen Hatalar ve Düzeltme Önerileri',
                  style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900),
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          ...safeMistakes.map(
            (mistake) => Container(
              width: double.infinity,
              margin: const EdgeInsets.only(bottom: 12),
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: Colors.orangeAccent.withValues(alpha: 0.09),
                borderRadius: BorderRadius.circular(18),
                border: Border.all(
                  color: Colors.orangeAccent.withValues(alpha: 0.22),
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(
                        Icons.error_outline_rounded,
                        size: 19,
                        color: Colors.orangeAccent,
                      ),
                      const SizedBox(width: 9),
                      Expanded(
                        child: Text(
                          mistake,
                          style: const TextStyle(
                            height: 1.4,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: AppColors.purpleGlow.withValues(alpha: 0.10),
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(
                        color: AppColors.purpleGlow.withValues(alpha: 0.22),
                      ),
                    ),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Icon(
                          Icons.build_circle_rounded,
                          color: AppColors.purpleGlow,
                          size: 18,
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            correctionBuilder(mistake),
                            style: const TextStyle(
                              color: AppColors.textSoft,
                              height: 1.45,
                              fontSize: 13,
                            ),
                          ),
                        ),
                      ],
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
    final safeItems = items.isEmpty ? ['Öneri bulunamadı.'] : items;

    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, color: iconColor),
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
          ...safeItems.map(
            (item) => Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(Icons.check_circle_rounded, size: 18, color: iconColor),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(item, style: const TextStyle(height: 1.4)),
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
              'Bu sonuç backend API üzerinden alınmıştır. Video FastAPI backend tarafına gönderilir, analiz edilir ve dönen sonuçlar bu ekranda kullanıcıya gösterilir.',
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
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.14),
        borderRadius: BorderRadius.circular(99),
        border: Border.all(color: color.withValues(alpha: 0.30)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: color, size: 14),
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
