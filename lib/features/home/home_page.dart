import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../app.dart';
import '../../core/state/analysis_history_store.dart';
import '../../core/state/auth_store.dart';
import '../../core/state/navigation_store.dart';
import '../../core/state/selected_exercise_store.dart';
import '../../core/theme/app_theme.dart';
import '../../data/exercise_catalog.dart';
import '../../data/weekly_workout_plan_data.dart';
import '../../l10n/app_localizations.dart';
import '../../models/analysis_result_model.dart';
import '../../models/auth_session_model.dart';
import '../../widgets/app_card.dart';
import '../../widgets/common.dart';
import '../../widgets/page_scaffold.dart';
import '../analysis/start_analysis.dart';
import '../auth/verify_email_sheet.dart';
import '../exercise_detail/exercise_detail_page.dart';
import '../navigation/app_menu.dart';
import '../result/result_page.dart';

/// "Good morning" 05-11, "Hi" 12-17, "Good evening" 18-04.
String timeOfDayGreeting(AppLocalizations l10n, String name, int hour) {
  if (hour >= 5 && hour < 12) return l10n.homeGreetingMorning(name);
  if (hour >= 18 || hour < 5) return l10n.homeGreetingEvening(name);
  return l10n.homeGreeting(name);
}

class HomePage extends StatelessWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    return ValueListenableBuilder<AuthSession?>(
      valueListenable: AuthStore.session,
      builder: (context, session, _) {
        final user = session?.user;
        final today = DateFormat.MMMMEEEEd(
          Localizations.localeOf(context).toLanguageTag(),
        ).format(DateTime.now());

        final greeting = user == null
            ? l10n.homeTitle
            : timeOfDayGreeting(l10n, user.firstName, DateTime.now().hour);

        return PageScaffold(
          title: greeting,
          subtitle: l10n.homeSubtitle(today),
          onRefresh: AnalysisHistoryStore.refresh,
          children: [
            if (user != null && !user.emailVerified) ...[
              const _VerifyEmailBanner(),
              const SizedBox(height: Gap.lg),
            ],
            const _NewAnalysisCard(),
            const _WeekSummary(),
            const _LatestAnalysis(),
            const _TodayPlan(),
            const _ExerciseLibrary(),
          ],
        );
      },
    );
  }
}

class _VerifyEmailBanner extends StatelessWidget {
  const _VerifyEmailBanner();

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    return AppCard(
      color: context.colors.primaryContainer.withValues(alpha: 0.5),
      borderColor: context.colors.primary.withValues(alpha: 0.3),
      child: Row(
        children: [
          Icon(Icons.mark_email_unread_outlined, color: context.colors.primary),
          const SizedBox(width: Gap.md),
          Expanded(
            child: Text(l10n.homeVerifyEmail, style: context.text.bodyMedium),
          ),
          TextButton(
            onPressed: () => VerifyEmailSheet.show(context),
            child: Text(l10n.verifyAction),
          ),
        ],
      ),
    );
  }
}

class _NewAnalysisCard extends StatelessWidget {
  const _NewAnalysisCard();

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final supported = ExerciseId.values
        .where((e) => e.analysisSupported)
        .toList();

    return ValueListenableBuilder<ExerciseId>(
      valueListenable: SelectedExerciseStore.selectedExercise,
      builder: (context, selected, _) {
        return HeroCard(
          child: Builder(
            builder: (context) => Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        l10n.homeNewAnalysis,
                        style: context.text.titleLarge,
                      ),
                    ),
                    Icon(
                      Icons.auto_awesome_rounded,
                      color: context.colors.primary,
                    ),
                  ],
                ),
                const SizedBox(height: Gap.xs),
                Text(
                  l10n.homeNewAnalysisBody,
                  style: context.text.bodyMedium?.copyWith(
                    color: context.tokens.textSecondary,
                  ),
                ),
                const SizedBox(height: Gap.lg),
                SegmentedButton<ExerciseId>(
                  showSelectedIcon: false,
                  segments: [
                    for (final exercise in supported)
                      ButtonSegment(
                        value: exercise,
                        label: Text(exercise.title(l10n)),
                        icon: Icon(exercise.icon, size: 18),
                      ),
                  ],
                  selected: {selected},
                  onSelectionChanged: (value) =>
                      SelectedExerciseStore.select(value.first),
                ),
                const SizedBox(height: Gap.lg),
                LayoutBuilder(
                  builder: (context, constraints) {
                    final upload = OutlinedButton.icon(
                      key: const Key('home_upload'),
                      onPressed: () =>
                          StartAnalysis.fromGallery(context, selected),
                      icon: const Icon(Icons.upload_rounded),
                      label: Text(l10n.homeUploadVideo),
                    );
                    final record = FilledButton.icon(
                      key: const Key('home_record'),
                      onPressed: () =>
                          StartAnalysis.withCamera(context, selected),
                      icon: const Icon(Icons.videocam_rounded),
                      label: Text(l10n.homeRecordVideo),
                    );
                    if (constraints.maxWidth < 360) {
                      return Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          record,
                          const SizedBox(height: Gap.sm),
                          upload,
                        ],
                      );
                    }
                    return Row(
                      children: [
                        Expanded(child: upload),
                        const SizedBox(width: Gap.md),
                        Expanded(child: record),
                      ],
                    );
                  },
                ),
                const SizedBox(height: Gap.md),
                Row(
                  children: [
                    Icon(
                      Icons.lightbulb_outline_rounded,
                      size: 16,
                      color: context.tokens.textTertiary,
                    ),
                    const SizedBox(width: Gap.xs + 2),
                    Expanded(
                      child: Text(
                        l10n.homeCaptureTip,
                        style: context.text.bodySmall,
                      ),
                    ),
                  ],
                ),
                const _WeekStreak(),
              ],
            ),
          ),
        );
      },
    );
  }
}

/// Encouraging line when the user has trained this week.
class _WeekStreak extends StatelessWidget {
  const _WeekStreak();

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<List<AnalysisResult>>(
      valueListenable: AnalysisHistoryStore.results,
      builder: (context, results, _) {
        final weekAgo = DateTime.now().subtract(const Duration(days: 7));
        final count = results.where((r) => r.createdAt.isAfter(weekAgo)).length;
        if (count == 0) return const SizedBox.shrink();
        return Padding(
          padding: const EdgeInsets.only(top: Gap.md),
          child: Row(
            children: [
              Icon(
                Icons.local_fire_department_rounded,
                size: 18,
                color: context.colors.primary,
              ),
              const SizedBox(width: Gap.xs + 2),
              Expanded(
                child: Text(
                  context.l10n.homeHeroStreak(count),
                  style: context.text.labelLarge?.copyWith(
                    color: context.colors.primary,
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

class _WeekSummary extends StatelessWidget {
  const _WeekSummary();

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    return ValueListenableBuilder<List<AnalysisResult>>(
      valueListenable: AnalysisHistoryStore.results,
      builder: (context, results, _) {
        if (results.isEmpty) return const SizedBox.shrink();
        final weekAgo = DateTime.now().subtract(const Duration(days: 7));
        final thisWeek = results
            .where((r) => r.createdAt.isAfter(weekAgo))
            .length;

        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            SectionHeader(title: l10n.homeSummary),
            Row(
              children: [
                Expanded(
                  child: StatTile(
                    label: l10n.homeThisWeek,
                    value: '$thisWeek',
                    icon: Icons.event_available_outlined,
                  ),
                ),
                const SizedBox(width: Gap.md),
                Expanded(
                  child: StatTile(
                    label: l10n.homeAverageScore,
                    value: '${AnalysisHistoryStore.averageScore}',
                    icon: Icons.speed_rounded,
                  ),
                ),
                const SizedBox(width: Gap.md),
                Expanded(
                  child: StatTile(
                    label: l10n.homeBestScore,
                    value: '${AnalysisHistoryStore.bestScore}',
                    icon: Icons.emoji_events_outlined,
                  ),
                ),
              ],
            ),
          ],
        );
      },
    );
  }
}

class _LatestAnalysis extends StatelessWidget {
  const _LatestAnalysis();

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    return ValueListenableBuilder<List<AnalysisResult>>(
      valueListenable: AnalysisHistoryStore.results,
      builder: (context, results, _) {
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            SectionHeader(
              title: l10n.homeLatest,
              actionLabel: results.isEmpty ? null : l10n.commonSeeAll,
              onAction: () => AppMenu.open(context, MenuPage.history),
            ),
            if (results.isEmpty)
              EmptyState(
                icon: Icons.insights_rounded,
                title: l10n.homeEmptyTitle,
                message: l10n.homeEmptyBody,
              )
            else
              AnalysisListTile(result: results.first),
          ],
        );
      },
    );
  }
}

/// One analysis in a list: exercise, date, reps and score.
class AnalysisListTile extends StatelessWidget {
  final AnalysisResult result;

  const AnalysisListTile({super.key, required this.result});

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final date = DateFormat.yMMMd(
      Localizations.localeOf(context).toLanguageTag(),
    ).add_Hm().format(result.createdAt);
    final scored = result.isScored;
    final color = scored
        ? context.tokens.scoreColor(result.score)
        : context.tokens.textTertiary;

    return AppCard(
      onTap: () => Navigator.of(
        context,
      ).push(MaterialPageRoute(builder: (_) => ResultPage(result: result))),
      child: Row(
        children: [
          IconBadge(icon: result.exercise.icon),
          const SizedBox(width: Gap.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  result.exercise.title(l10n),
                  style: context.text.titleSmall,
                ),
                const SizedBox(height: 2),
                Text(
                  '$date · ${l10n.historyReps(result.repetitionCount)}',
                  style: context.text.bodySmall,
                ),
              ],
            ),
          ),
          Semantics(
            label: scored
                ? '${l10n.resultScoreCaption} ${result.score}'
                : l10n.resultNotScored,
            excludeSemantics: true,
            child: Container(
              width: 48,
              height: 48,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(Radii.md),
              ),
              child: Text(
                scored ? '${result.score}' : '–',
                style: context.text.titleMedium?.copyWith(color: color),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _TodayPlan extends StatelessWidget {
  const _TodayPlan();

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final plan = planFor(DateTime.now().weekday);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        SectionHeader(title: l10n.homeToday),
        AppCard(
          onTap: () => NavigationStore.go(AppTab.program),
          child: Row(
            children: [
              IconBadge(
                icon: plan.isRestDay
                    ? Icons.spa_outlined
                    : Icons.calendar_today_rounded,
                color: plan.isRestDay ? context.tokens.success : null,
              ),
              const SizedBox(width: Gap.md),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(plan.focus(l10n), style: context.text.titleSmall),
                    const SizedBox(height: 2),
                    Text(
                      plan.isRestDay
                          ? l10n.programRestDayBody
                          : plan.exercises
                                .map((e) => e.exercise.title(l10n))
                                .join(' · '),
                      style: context.text.bodySmall,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
              Icon(
                Icons.chevron_right_rounded,
                color: context.tokens.textTertiary,
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _ExerciseLibrary extends StatelessWidget {
  const _ExerciseLibrary();

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        SectionHeader(title: l10n.homeLibrary),
        SizedBox(
          height: 128,
          child: ListView.separated(
            scrollDirection: Axis.horizontal,
            itemCount: ExerciseId.values.length,
            separatorBuilder: (_, _) => const SizedBox(width: Gap.md),
            itemBuilder: (context, index) {
              final exercise = ExerciseId.values[index];
              return SizedBox(
                width: 140,
                child: AppCard(
                  padding: const EdgeInsets.all(Gap.md + 2),
                  onTap: () => Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) => ExerciseDetailPage(exercise: exercise),
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      IconBadge(icon: exercise.icon, size: 36),
                      const Spacer(),
                      Text(
                        exercise.title(l10n),
                        style: context.text.titleSmall,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      const SizedBox(height: 2),
                      Text(
                        exercise.analysisSupported
                            ? l10n.homeAiAnalysis
                            : l10n.commonComingSoon,
                        style: context.text.labelMedium?.copyWith(
                          color: exercise.analysisSupported
                              ? context.colors.primary
                              : null,
                        ),
                      ),
                    ],
                  ),
                ),
              );
            },
          ),
        ),
      ],
    );
  }
}
