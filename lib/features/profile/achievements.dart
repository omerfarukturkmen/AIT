import 'package:flutter/material.dart';

import '../../l10n/app_localizations.dart';
import '../../models/analysis_result_model.dart';

/// Achievement earned from the user's real analysis history.
class Achievement {
  final IconData icon;
  final String title;
  final String description;
  final bool unlocked;

  const Achievement({
    required this.icon,
    required this.title,
    required this.description,
    required this.unlocked,
  });
}

List<Achievement> achievementsFor(
  AppLocalizations l10n,
  List<AnalysisResult> results, {
  DateTime? now,
}) {
  final today = now ?? DateTime.now();
  final weekAgo = today.subtract(const Duration(days: 7));
  final activeDaysThisWeek = results
      .where((r) => r.createdAt.isAfter(weekAgo))
      .map(
        (r) => DateTime(r.createdAt.year, r.createdAt.month, r.createdAt.day),
      )
      .toSet()
      .length;

  return [
    Achievement(
      icon: Icons.flag_rounded,
      title: l10n.achievementFirstTitle,
      description: l10n.achievementFirstBody,
      unlocked: results.isNotEmpty,
    ),
    Achievement(
      icon: Icons.local_fire_department_rounded,
      title: l10n.achievementTenTitle,
      description: l10n.achievementTenBody(results.length.clamp(0, 10)),
      unlocked: results.length >= 10,
    ),
    Achievement(
      icon: Icons.emoji_events_rounded,
      title: l10n.achievementNinetyTitle,
      description: l10n.achievementNinetyBody,
      unlocked: results.any((r) => r.score >= 90),
    ),
    Achievement(
      icon: Icons.verified_rounded,
      title: l10n.achievementCleanTitle,
      description: l10n.achievementCleanBody,
      unlocked: results.any(
        (r) => r.issueCodes.isEmpty && r.repetitionCount > 0,
      ),
    ),
    Achievement(
      icon: Icons.swap_horiz_rounded,
      title: l10n.achievementBothTitle,
      description: l10n.achievementBothBody,
      unlocked: results.map((r) => r.exercise).toSet().length >= 2,
    ),
    Achievement(
      icon: Icons.calendar_month_rounded,
      title: l10n.achievementStreakTitle,
      description: l10n.achievementStreakBody(activeDaysThisWeek.clamp(0, 3)),
      unlocked: activeDaysThisWeek >= 3,
    ),
  ];
}
