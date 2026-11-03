import 'package:flutter/material.dart';

import '../../app.dart';
import '../../core/state/analysis_history_store.dart';
import '../../core/state/auth_store.dart';
import '../../core/state/favorite_exercises_store.dart';
import '../../core/theme/app_theme.dart';
import '../../data/exercise_catalog.dart';
import '../../models/analysis_result_model.dart';
import '../../models/auth_session_model.dart';
import '../../widgets/app_card.dart';
import '../../widgets/common.dart';
import '../../widgets/page_scaffold.dart';
import '../auth/verify_email_sheet.dart';
import '../exercise_detail/exercise_detail_page.dart';
import '../settings/settings_page.dart';
import 'achievements.dart';

class ProfilePage extends StatelessWidget {
  const ProfilePage({super.key});

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    return ValueListenableBuilder<AuthSession?>(
      valueListenable: AuthStore.session,
      builder: (context, session, _) {
        return ValueListenableBuilder<List<AnalysisResult>>(
          valueListenable: AnalysisHistoryStore.results,
          builder: (context, results, _) {
            final user = session?.user;
            return PageScaffold(
              title: l10n.profileTitle,
              actions: [
                IconButton(
                  key: const Key('open_settings'),
                  tooltip: l10n.settingsTitle,
                  icon: const Icon(Icons.settings_outlined),
                  onPressed: () => Navigator.of(context).push(
                    MaterialPageRoute(builder: (_) => const SettingsPage()),
                  ),
                ),
              ],
              children: [
                if (user != null) _ProfileHeader(user: user),
                const SizedBox(height: Gap.md),
                Row(
                  children: [
                    Expanded(
                      child: StatTile(
                        label: l10n.profileAnalyses,
                        value: '${results.length}',
                        icon: Icons.insights_rounded,
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
                SectionHeader(title: l10n.profileAchievements),
                _AchievementGrid(results: results),
                const _Favorites(),
              ],
            );
          },
        );
      },
    );
  }
}

class _ProfileHeader extends StatelessWidget {
  final AuthUser user;

  const _ProfileHeader({required this.user});

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    return AppCard(
      child: Row(
        children: [
          CircleAvatar(
            radius: 30,
            backgroundColor: context.colors.primaryContainer,
            child: Text(
              user.initials,
              style: context.text.titleLarge?.copyWith(
                color: context.colors.onPrimaryContainer,
              ),
            ),
          ),
          const SizedBox(width: Gap.lg),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(user.fullName, style: context.text.titleLarge),
                const SizedBox(height: 2),
                Text(user.email, style: context.text.bodySmall),
                const SizedBox(height: Gap.sm),
                if (user.emailVerified)
                  Pill(
                    label: l10n.profileVerified,
                    icon: Icons.verified_rounded,
                    color: context.tokens.success,
                  )
                else
                  InkWell(
                    onTap: () => VerifyEmailSheet.show(context),
                    borderRadius: BorderRadius.circular(999),
                    child: Pill(
                      label: l10n.profileNotVerified,
                      icon: Icons.error_outline_rounded,
                      color: context.tokens.warning,
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

class _AchievementGrid extends StatelessWidget {
  final List<AnalysisResult> results;

  const _AchievementGrid({required this.results});

  @override
  Widget build(BuildContext context) {
    final items = achievementsFor(context.l10n, results);
    return LayoutBuilder(
      builder: (context, constraints) {
        final columns = constraints.maxWidth >= 560 ? 3 : 2;
        final width = (constraints.maxWidth - Gap.md * (columns - 1)) / columns;
        return Wrap(
          spacing: Gap.md,
          runSpacing: Gap.md,
          children: [
            for (final item in items)
              SizedBox(
                width: width,
                child: _AchievementTile(item: item),
              ),
          ],
        );
      },
    );
  }
}

class _AchievementTile extends StatelessWidget {
  final Achievement item;

  const _AchievementTile({required this.item});

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final muted = !item.unlocked;
    return Semantics(
      label:
          '${item.title}, ${item.unlocked ? l10n.achievementUnlocked : l10n.achievementLocked}. ${item.description}',
      excludeSemantics: true,
      child: AppCard(
        padding: const EdgeInsets.all(Gap.md + 2),
        child: Opacity(
          opacity: muted ? 0.55 : 1,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              IconBadge(
                icon: muted ? Icons.lock_outline_rounded : item.icon,
                color: muted
                    ? context.tokens.textTertiary
                    : context.tokens.warning,
                size: 36,
              ),
              const SizedBox(height: Gap.sm),
              Text(item.title, style: context.text.titleSmall),
              const SizedBox(height: 2),
              Text(
                item.description,
                style: context.text.bodySmall,
                maxLines: 3,
                overflow: TextOverflow.ellipsis,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _Favorites extends StatelessWidget {
  const _Favorites();

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    return ValueListenableBuilder<Set<ExerciseId>>(
      valueListenable: FavoriteExercisesStore.favorites,
      builder: (context, favorites, _) {
        if (favorites.isEmpty) return const SizedBox.shrink();
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            SectionHeader(title: l10n.profileFavorites),
            AppCard(
              padding: EdgeInsets.zero,
              child: Column(
                children: [
                  for (final exercise in favorites)
                    ListTile(
                      leading: IconBadge(icon: exercise.icon, size: 36),
                      title: Text(exercise.title(l10n)),
                      trailing: const Icon(Icons.chevron_right_rounded),
                      onTap: () => Navigator.of(context).push(
                        MaterialPageRoute(
                          builder: (_) =>
                              ExerciseDetailPage(exercise: exercise),
                        ),
                      ),
                    ),
                ],
              ),
            ),
          ],
        );
      },
    );
  }
}
