import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../app.dart';
import '../../core/state/selected_exercise_store.dart';
import '../../core/state/workout_program_store.dart';
import '../../core/theme/app_theme.dart';
import '../../data/exercise_catalog.dart';
import '../../data/weekly_workout_plan_data.dart';
import '../../models/workout_plan_model.dart';
import '../../widgets/app_card.dart';
import '../../widgets/common.dart';
import '../../widgets/page_scaffold.dart';
import '../analysis/start_analysis.dart';
import '../exercise_detail/exercise_detail_page.dart';

class ProgramPage extends StatelessWidget {
  const ProgramPage({super.key});

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final trainingDays = weeklyWorkoutPlan.where((d) => !d.isRestDay).length;
    final today = DateTime.now();
    final weekStart = DateTime(
      today.year,
      today.month,
      today.day,
    ).subtract(Duration(days: today.weekday - 1));
    final dayName = DateFormat.EEEE(
      Localizations.localeOf(context).toLanguageTag(),
    );

    return ValueListenableBuilder<Set<String>>(
      valueListenable: WorkoutProgramStore.completed,
      builder: (context, _, _) {
        final done = WorkoutProgramStore.completedThisWeek();
        return PageScaffold(
          title: l10n.programTitle,
          subtitle: l10n.programSubtitle,
          children: [
            AppCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          l10n.programThisWeek,
                          style: context.text.titleMedium,
                        ),
                      ),
                      Text(
                        l10n.programDaysDone(done, trainingDays),
                        style: context.text.labelLarge,
                      ),
                    ],
                  ),
                  const SizedBox(height: Gap.md),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(4),
                    child: LinearProgressIndicator(
                      value: trainingDays == 0
                          ? 0
                          : (done / trainingDays).clamp(0, 1),
                      minHeight: 8,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: Gap.lg),
            for (final plan in weeklyWorkoutPlan) ...[
              _DayCard(
                plan: plan,
                dayLabel: dayName.format(
                  weekStart.add(Duration(days: plan.weekday - 1)),
                ),
                isToday: plan.weekday == today.weekday,
              ),
              const SizedBox(height: Gap.md),
            ],
          ],
        );
      },
    );
  }
}

class _DayCard extends StatelessWidget {
  final DailyWorkoutPlan plan;
  final String dayLabel;
  final bool isToday;

  const _DayCard({
    required this.plan,
    required this.dayLabel,
    required this.isToday,
  });

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final completed = WorkoutProgramStore.isCompleted(plan.weekday);

    return AppCard(
      borderColor: isToday ? context.colors.primary : null,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Text(dayLabel, style: context.text.titleMedium),
                        if (isToday) ...[
                          const SizedBox(width: Gap.sm),
                          Pill(
                            label: l10n.programToday,
                            color: context.colors.primary,
                          ),
                        ],
                      ],
                    ),
                    const SizedBox(height: 2),
                    Text(plan.focus(l10n), style: context.text.bodySmall),
                  ],
                ),
              ),
              if (!plan.isRestDay)
                Semantics(
                  label: l10n.programMarkDone,
                  child: Checkbox(
                    value: completed,
                    onChanged: (_) => WorkoutProgramStore.toggle(plan.weekday),
                  ),
                ),
            ],
          ),
          if (plan.isRestDay) ...[
            const SizedBox(height: Gap.sm),
            Text(
              l10n.programRestDayBody,
              style: context.text.bodyMedium?.copyWith(
                color: context.tokens.textSecondary,
              ),
            ),
          ] else ...[
            const SizedBox(height: Gap.sm),
            for (final item in plan.exercises) _ExerciseRow(item: item),
          ],
        ],
      ),
    );
  }
}

class _ExerciseRow extends StatelessWidget {
  final WorkoutExercise item;

  const _ExerciseRow({required this.item});

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final exercise = item.exercise;

    return InkWell(
      borderRadius: BorderRadius.circular(Radii.sm),
      onTap: () => Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => ExerciseDetailPage(exercise: exercise),
        ),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: Gap.sm),
        child: Row(
          children: [
            IconBadge(icon: exercise.icon, size: 36),
            const SizedBox(width: Gap.md),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(exercise.title(l10n), style: context.text.titleSmall),
                  Text(
                    '${item.volume(l10n)} · ${item.note(l10n)}',
                    style: context.text.bodySmall,
                  ),
                ],
              ),
            ),
            if (exercise.analysisSupported)
              IconButton(
                tooltip: l10n.programAnalyze,
                icon: Icon(
                  Icons.videocam_outlined,
                  color: context.colors.primary,
                ),
                onPressed: () {
                  SelectedExerciseStore.select(exercise);
                  StartAnalysis.withCamera(context, exercise);
                },
              ),
          ],
        ),
      ),
    );
  }
}
