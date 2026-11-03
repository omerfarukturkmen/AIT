import 'package:flutter/material.dart';

import '../../app.dart';
import '../../core/state/favorite_exercises_store.dart';
import '../../core/state/selected_exercise_store.dart';
import '../../core/theme/app_theme.dart';
import '../../data/exercise_catalog.dart';
import '../../widgets/app_card.dart';
import '../../widgets/common.dart';
import '../../widgets/page_scaffold.dart';
import '../analysis/start_analysis.dart';

class ExerciseDetailPage extends StatelessWidget {
  final ExerciseId exercise;

  const ExerciseDetailPage({super.key, required this.exercise});

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;

    return Scaffold(
      appBar: AppBar(
        title: Text(exercise.title(l10n)),
        actions: [
          ValueListenableBuilder<Set<ExerciseId>>(
            valueListenable: FavoriteExercisesStore.favorites,
            builder: (context, favorites, _) {
              final isFavorite = favorites.contains(exercise);
              return IconButton(
                onPressed: () => FavoriteExercisesStore.toggle(exercise),
                tooltip: isFavorite
                    ? l10n.detailUnfavorite
                    : l10n.detailFavorite,
                icon: Icon(
                  isFavorite
                      ? Icons.favorite_rounded
                      : Icons.favorite_border_rounded,
                  color: isFavorite ? context.tokens.danger : null,
                ),
              );
            },
          ),
        ],
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(
            Gap.page,
            Gap.sm,
            Gap.page,
            Gap.xxl,
          ),
          children: [
            Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(
                  maxWidth: PageScaffold.maxContentWidth,
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Row(
                      children: [
                        IconBadge(icon: exercise.icon, size: 56),
                        const SizedBox(width: Gap.lg),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                exercise.title(l10n),
                                style: context.text.headlineSmall,
                              ),
                              const SizedBox(height: Gap.xs),
                              Pill(
                                label: exercise.analysisSupported
                                    ? l10n.homeAiAnalysis
                                    : l10n.commonComingSoon,
                                color: exercise.analysisSupported
                                    ? context.colors.primary
                                    : null,
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: Gap.lg),
                    Text(
                      exercise.description(l10n),
                      style: context.text.bodyLarge?.copyWith(
                        color: context.tokens.textSecondary,
                      ),
                    ),
                    if (exercise.analysisSupported) ...[
                      const SizedBox(height: Gap.lg),
                      Row(
                        children: [
                          Expanded(
                            child: OutlinedButton.icon(
                              onPressed: () {
                                SelectedExerciseStore.select(exercise);
                                StartAnalysis.fromGallery(context, exercise);
                              },
                              icon: const Icon(Icons.upload_rounded),
                              label: Text(l10n.homeUploadVideo),
                            ),
                          ),
                          const SizedBox(width: Gap.md),
                          Expanded(
                            child: FilledButton.icon(
                              onPressed: () {
                                SelectedExerciseStore.select(exercise);
                                StartAnalysis.withCamera(context, exercise);
                              },
                              icon: const Icon(Icons.videocam_rounded),
                              label: Text(l10n.homeRecordVideo),
                            ),
                          ),
                        ],
                      ),
                    ] else ...[
                      const SizedBox(height: Gap.lg),
                      AppCard(
                        child: Row(
                          children: [
                            Icon(
                              Icons.schedule_rounded,
                              color: context.tokens.textSecondary,
                            ),
                            const SizedBox(width: Gap.md),
                            Expanded(
                              child: Text(
                                l10n.detailComingSoonBody,
                                style: context.text.bodyMedium,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                    SectionHeader(title: l10n.detailMuscles),
                    Wrap(
                      spacing: Gap.sm,
                      runSpacing: Gap.sm,
                      children: [
                        for (final muscle in exercise.targetMuscles(l10n))
                          Chip(label: Text(muscle)),
                      ],
                    ),
                    SectionHeader(title: l10n.detailMistakes),
                    _BulletCard(
                      items: exercise.commonMistakes(l10n),
                      icon: Icons.close_rounded,
                      color: context.tokens.danger,
                    ),
                    SectionHeader(title: l10n.resultTipsTitle),
                    _BulletCard(
                      items: exercise.tips(l10n),
                      icon: Icons.check_rounded,
                      color: context.tokens.success,
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _BulletCard extends StatelessWidget {
  final List<String> items;
  final IconData icon;
  final Color color;

  const _BulletCard({
    required this.items,
    required this.icon,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return AppCard(
      child: Column(
        children: [
          for (final item in items)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: Gap.xs + 2),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(icon, size: 18, color: color),
                  const SizedBox(width: Gap.sm + 2),
                  Expanded(child: Text(item, style: context.text.bodyMedium)),
                ],
              ),
            ),
        ],
      ),
    );
  }
}
