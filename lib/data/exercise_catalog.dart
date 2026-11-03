import 'package:flutter/material.dart';

import '../l10n/app_localizations.dart';

/// Exercises shown in the app. Only those with an [apiKey] can be analyzed;
/// the AI module currently supports squat and push-up.
enum ExerciseId { squat, pushUp, plank, lunge, deadlift, shoulderPress }

extension ExerciseInfo on ExerciseId {
  /// Identifier sent to the backend, or null if it cannot be analyzed yet.
  String? get apiKey => switch (this) {
    ExerciseId.squat => 'squat',
    ExerciseId.pushUp => 'push-up',
    _ => null,
  };

  bool get analysisSupported => apiKey != null;

  IconData get icon => switch (this) {
    ExerciseId.squat => Icons.accessibility_new_rounded,
    ExerciseId.pushUp => Icons.sports_gymnastics_rounded,
    ExerciseId.plank => Icons.self_improvement_rounded,
    ExerciseId.lunge => Icons.directions_walk_rounded,
    ExerciseId.deadlift => Icons.fitness_center_rounded,
    ExerciseId.shoulderPress => Icons.sports_martial_arts_rounded,
  };

  String title(AppLocalizations l10n) => switch (this) {
    ExerciseId.squat => l10n.exerciseSquat,
    ExerciseId.pushUp => l10n.exercisePushUp,
    ExerciseId.plank => l10n.exercisePlank,
    ExerciseId.lunge => l10n.exerciseLunge,
    ExerciseId.deadlift => l10n.exerciseDeadlift,
    ExerciseId.shoulderPress => l10n.exerciseShoulderPress,
  };

  String description(AppLocalizations l10n) => switch (this) {
    ExerciseId.squat => l10n.exerciseSquatDescription,
    ExerciseId.pushUp => l10n.exercisePushUpDescription,
    ExerciseId.plank => l10n.exercisePlankDescription,
    ExerciseId.lunge => l10n.exerciseLungeDescription,
    ExerciseId.deadlift => l10n.exerciseDeadliftDescription,
    ExerciseId.shoulderPress => l10n.exerciseShoulderPressDescription,
  };

  /// Anatomical names are the same in both languages except "core".
  List<String> targetMuscles(AppLocalizations l10n) => switch (this) {
    ExerciseId.squat => [
      'Quadriceps',
      'Gluteus maximus',
      'Hamstrings',
      l10n.muscleCore,
    ],
    ExerciseId.pushUp => [
      'Pectoralis major',
      'Triceps brachii',
      'Anterior deltoid',
      l10n.muscleCore,
    ],
    ExerciseId.plank => [
      'Rectus abdominis',
      'Transversus abdominis',
      'Obliques',
      'Gluteus',
    ],
    ExerciseId.lunge => [
      'Quadriceps',
      'Gluteus maximus',
      'Hamstrings',
      l10n.muscleCalves,
    ],
    ExerciseId.deadlift => [
      'Hamstrings',
      'Gluteus maximus',
      'Erector spinae',
      'Trapezius',
    ],
    ExerciseId.shoulderPress => [
      'Deltoid',
      'Triceps brachii',
      'Trapezius',
      l10n.muscleCore,
    ],
  };

  List<String> commonMistakes(AppLocalizations l10n) => switch (this) {
    ExerciseId.squat => [
      l10n.squatMistake1,
      l10n.squatMistake2,
      l10n.squatMistake3,
      l10n.squatMistake4,
    ],
    ExerciseId.pushUp => [
      l10n.pushUpMistake1,
      l10n.pushUpMistake2,
      l10n.pushUpMistake3,
      l10n.pushUpMistake4,
    ],
    ExerciseId.plank => [
      l10n.plankMistake1,
      l10n.plankMistake2,
      l10n.plankMistake3,
    ],
    ExerciseId.lunge => [
      l10n.lungeMistake1,
      l10n.lungeMistake2,
      l10n.lungeMistake3,
    ],
    ExerciseId.deadlift => [
      l10n.deadliftMistake1,
      l10n.deadliftMistake2,
      l10n.deadliftMistake3,
    ],
    ExerciseId.shoulderPress => [
      l10n.shoulderPressMistake1,
      l10n.shoulderPressMistake2,
      l10n.shoulderPressMistake3,
    ],
  };

  List<String> tips(AppLocalizations l10n) => switch (this) {
    ExerciseId.squat => [l10n.squatTip1, l10n.squatTip2, l10n.squatTip3],
    ExerciseId.pushUp => [l10n.pushUpTip1, l10n.pushUpTip2, l10n.pushUpTip3],
    ExerciseId.plank => [l10n.plankTip1, l10n.plankTip2, l10n.plankTip3],
    ExerciseId.lunge => [l10n.lungeTip1, l10n.lungeTip2, l10n.lungeTip3],
    ExerciseId.deadlift => [
      l10n.deadliftTip1,
      l10n.deadliftTip2,
      l10n.deadliftTip3,
    ],
    ExerciseId.shoulderPress => [
      l10n.shoulderPressTip1,
      l10n.shoulderPressTip2,
      l10n.shoulderPressTip3,
    ],
  };
}

ExerciseId? exerciseFromApiKey(String? key) {
  final value = (key ?? '').trim().toLowerCase().replaceAll('_', '-');
  return switch (value) {
    'squat' => ExerciseId.squat,
    'push-up' || 'pushup' || 'push up' => ExerciseId.pushUp,
    _ => null,
  };
}

ExerciseId? exerciseFromName(String? name) {
  for (final id in ExerciseId.values) {
    if (id.name == name) return id;
  }
  return null;
}
