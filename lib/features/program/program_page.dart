import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/state/workout_program_store.dart';
import '../../../data/weekly_workout_plan_data.dart';
import '../../../models/workout_plan_model.dart';
import '../../../widgets/glass_card.dart';
import '../../../widgets/premium_background.dart';
import '../exercise_detail/exercise_detail_page.dart';
import '../../../core/state/navigation_store.dart';
import '../../../core/state/selected_exercise_store.dart';
import '../../../widgets/premium_button.dart';

class ProgramPage extends StatelessWidget {
  const ProgramPage({super.key});

  String get todayName {
    final weekday = DateTime.now().weekday;

    switch (weekday) {
      case DateTime.monday:
        return 'Pazartesi';
      case DateTime.tuesday:
        return 'Salı';
      case DateTime.wednesday:
        return 'Çarşamba';
      case DateTime.thursday:
        return 'Perşembe';
      case DateTime.friday:
        return 'Cuma';
      case DateTime.saturday:
        return 'Cumartesi';
      case DateTime.sunday:
        return 'Pazar';
      default:
        return 'Pazartesi';
    }
  }

  @override
  Widget build(BuildContext context) {
    final todayPlan = weeklyWorkoutPlan.firstWhere(
      (plan) => plan.day == todayName,
      orElse: () => weeklyWorkoutPlan.first,
    );

    return Scaffold(
      body: PremiumBackground(
        child: SafeArea(
          child: ValueListenableBuilder<Set<String>>(
            valueListenable: WorkoutProgramStore.completedDays,
            builder: (context, completedDays, child) {
              final completedCount = completedDays.length;
              final progress = completedCount / weeklyWorkoutPlan.length;

              return SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(16, 18, 16, 24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    const Text(
                      'Haftalık Program',
                      style: TextStyle(
                        fontSize: 30,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'Egzersiz planını takip et, tamamladığın günleri işaretle ve hareket detaylarını incele.',
                      style: TextStyle(color: AppColors.textSoft, height: 1.4),
                    ),
                    const SizedBox(height: 22),
                    _ProgressCard(
                      completedCount: completedCount,
                      totalCount: weeklyWorkoutPlan.length,
                      progress: progress,
                    ),
                    const SizedBox(height: 18),
                    _TodayProgramCard(plan: todayPlan),
                    const SizedBox(height: 22),
                    const Text(
                      'Haftanın Planı',
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    const SizedBox(height: 14),
                    ...weeklyWorkoutPlan.map((plan) {
                      final isToday = plan.day == todayName;
                      final isCompleted = completedDays.contains(plan.day);

                      return Padding(
                        padding: const EdgeInsets.only(bottom: 14),
                        child: _DayPlanCard(
                          plan: plan,
                          isToday: isToday,
                          isCompleted: isCompleted,
                          onToggleCompleted: () {
                            WorkoutProgramStore.toggleCompleted(plan.day);
                          },
                        ),
                      );
                    }),
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

class _ProgressCard extends StatelessWidget {
  final int completedCount;
  final int totalCount;
  final double progress;

  const _ProgressCard({
    required this.completedCount,
    required this.totalCount,
    required this.progress,
  });

  @override
  Widget build(BuildContext context) {
    final percentage = (progress * 100).round();

    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(
                Icons.calendar_month_rounded,
                color: AppColors.purpleGlow,
                size: 30,
              ),
              const SizedBox(width: 12),
              const Expanded(
                child: Text(
                  'Haftalık İlerleme',
                  style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900),
                ),
              ),
              Text(
                '$percentage%',
                style: const TextStyle(
                  color: AppColors.purpleGlow,
                  fontSize: 24,
                  fontWeight: FontWeight.w900,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          ClipRRect(
            borderRadius: BorderRadius.circular(99),
            child: LinearProgressIndicator(
              minHeight: 10,
              value: progress,
              backgroundColor: Colors.white.withValues(alpha: 0.08),
              valueColor: const AlwaysStoppedAnimation<Color>(
                AppColors.purpleGlow,
              ),
            ),
          ),
          const SizedBox(height: 12),
          Text(
            '$completedCount / $totalCount gün tamamlandı',
            style: const TextStyle(color: AppColors.textSoft, fontSize: 13),
          ),
        ],
      ),
    );
  }
}

class _TodayProgramCard extends StatelessWidget {
  final DailyWorkoutPlan plan;

  const _TodayProgramCard({required this.plan});

  void _startTodayAnalysis(BuildContext context) {
    if (plan.isRestDay || plan.exercises.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Bugün dinlenme günü. Analiz başlatılmadı.'),
        ),
      );
      return;
    }

    final firstExercise = plan.exercises.first.name;

    SelectedExerciseStore.setExercise(firstExercise);
    NavigationStore.goHome();

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          '$firstExercise seçildi. Ana sayfadan video yükleyebilir veya canlı analiz başlatabilirsin.',
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const _Badge(
            text: 'Bugünün Programı',
            color: Colors.greenAccent,
            icon: Icons.today_rounded,
          ),
          const SizedBox(height: 14),
          Text(
            plan.day,
            style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w900),
          ),
          const SizedBox(height: 6),
          Text(
            plan.focus,
            style: const TextStyle(
              color: AppColors.textSoft,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 16),
          if (plan.isRestDay)
            const _RestDayBox()
          else ...[
            ...plan.exercises.map(
              (exercise) => Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: _CompactExerciseRow(exercise: exercise),
              ),
            ),
            const SizedBox(height: 10),
            PremiumButton(
              icon: Icons.play_arrow_rounded,
              text: 'Bugünkü Analize Başla',
              onPressed: () => _startTodayAnalysis(context),
            ),
          ],
        ],
      ),
    );
  }
}

class _DayPlanCard extends StatelessWidget {
  final DailyWorkoutPlan plan;
  final bool isToday;
  final bool isCompleted;
  final VoidCallback onToggleCompleted;

  const _DayPlanCard({
    required this.plan,
    required this.isToday,
    required this.isCompleted,
    required this.onToggleCompleted,
  });

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              _DayIcon(
                isToday: isToday,
                isCompleted: isCompleted,
                isRestDay: plan.isRestDay,
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      plan.day,
                      style: const TextStyle(
                        fontSize: 19,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      plan.focus,
                      style: const TextStyle(
                        color: AppColors.textSoft,
                        fontSize: 13,
                      ),
                    ),
                  ],
                ),
              ),
              if (isToday)
                const _Badge(
                  text: 'Bugün',
                  color: Colors.greenAccent,
                  icon: Icons.bolt_rounded,
                ),
            ],
          ),
          const SizedBox(height: 16),
          if (plan.isRestDay)
            const _RestDayBox()
          else
            ...plan.exercises.map(
              (exercise) => Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: _ExercisePlanTile(exercise: exercise),
              ),
            ),
          const SizedBox(height: 8),
          SizedBox(
            width: double.infinity,
            child: OutlinedButton.icon(
              onPressed: onToggleCompleted,
              icon: Icon(
                isCompleted
                    ? Icons.check_circle_rounded
                    : Icons.radio_button_unchecked_rounded,
              ),
              label: Text(isCompleted ? 'Tamamlandı' : 'Günü Tamamla'),
              style: OutlinedButton.styleFrom(
                foregroundColor: isCompleted
                    ? Colors.greenAccent
                    : Colors.white,
                side: BorderSide(
                  color: isCompleted
                      ? Colors.greenAccent.withValues(alpha: 0.5)
                      : AppColors.purpleGlow.withValues(alpha: 0.35),
                ),
                padding: const EdgeInsets.symmetric(vertical: 14),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                ),
                textStyle: const TextStyle(fontWeight: FontWeight.w800),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ExercisePlanTile extends StatelessWidget {
  final WorkoutExercise exercise;

  const _ExercisePlanTile({required this.exercise});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (_) => ExerciseDetailPage(exerciseName: exercise.name),
          ),
        );
      },
      child: Container(
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
                color: AppColors.purpleGlow.withValues(alpha: 0.13),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(
                  color: AppColors.purpleGlow.withValues(alpha: 0.22),
                ),
              ),
              child: const Icon(
                Icons.fitness_center_rounded,
                color: AppColors.purpleGlow,
                size: 22,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    exercise.name,
                    style: const TextStyle(
                      fontWeight: FontWeight.w900,
                      fontSize: 15,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    '${exercise.sets} • ${exercise.reps}',
                    style: const TextStyle(
                      color: AppColors.textSoft,
                      fontSize: 12,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    exercise.note,
                    style: const TextStyle(
                      color: AppColors.textSoft,
                      fontSize: 11,
                      height: 1.3,
                    ),
                  ),
                ],
              ),
            ),
            const Icon(
              Icons.arrow_forward_ios_rounded,
              color: AppColors.textSoft,
              size: 15,
            ),
          ],
        ),
      ),
    );
  }
}

class _CompactExerciseRow extends StatelessWidget {
  final WorkoutExercise exercise;

  const _CompactExerciseRow({required this.exercise});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        const Icon(
          Icons.check_circle_rounded,
          color: AppColors.purpleGlow,
          size: 18,
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Text(
            '${exercise.name} • ${exercise.sets} • ${exercise.reps}',
            style: const TextStyle(fontWeight: FontWeight.w700),
          ),
        ),
      ],
    );
  }
}

class _RestDayBox extends StatelessWidget {
  const _RestDayBox();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.greenAccent.withValues(alpha: 0.10),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: Colors.greenAccent.withValues(alpha: 0.22)),
      ),
      child: const Row(
        children: [
          Icon(Icons.self_improvement_rounded, color: Colors.greenAccent),
          SizedBox(width: 10),
          Expanded(
            child: Text(
              'Bugün dinlenme ve toparlanma günü. Hafif mobilite veya yürüyüş tercih edebilirsin.',
              style: TextStyle(color: AppColors.textSoft, height: 1.4),
            ),
          ),
        ],
      ),
    );
  }
}

class _DayIcon extends StatelessWidget {
  final bool isToday;
  final bool isCompleted;
  final bool isRestDay;

  const _DayIcon({
    required this.isToday,
    required this.isCompleted,
    required this.isRestDay,
  });

  @override
  Widget build(BuildContext context) {
    Color color = AppColors.purpleGlow;
    IconData icon = Icons.calendar_today_rounded;

    if (isCompleted) {
      color = Colors.greenAccent;
      icon = Icons.check_circle_rounded;
    } else if (isRestDay) {
      color = Colors.lightBlueAccent;
      icon = Icons.self_improvement_rounded;
    } else if (isToday) {
      color = Colors.orangeAccent;
      icon = Icons.bolt_rounded;
    }

    return Container(
      height: 54,
      width: 54,
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.13),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: color.withValues(alpha: 0.25)),
      ),
      child: Icon(icon, color: color, size: 28),
    );
  }
}

class _Badge extends StatelessWidget {
  final String text;
  final Color color;
  final IconData icon;

  const _Badge({required this.text, required this.color, required this.icon});

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
