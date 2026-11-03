import '../data/exercise_catalog.dart';
import '../l10n/app_localizations.dart';

typedef LocalizedText = String Function(AppLocalizations l10n);

class WorkoutExercise {
  final ExerciseId exercise;
  final int sets;

  /// Either [reps] or [seconds] is set.
  final int? reps;
  final int? seconds;
  final LocalizedText note;

  const WorkoutExercise({
    required this.exercise,
    required this.sets,
    this.reps,
    this.seconds,
    required this.note,
  });

  String volume(AppLocalizations l10n) => seconds != null
      ? l10n.programSetsSeconds(sets, seconds!)
      : l10n.programSetsReps(sets, reps ?? 0);
}

class DailyWorkoutPlan {
  /// ISO weekday: 1 = Monday ... 7 = Sunday.
  final int weekday;
  final LocalizedText focus;
  final List<WorkoutExercise> exercises;

  const DailyWorkoutPlan({
    required this.weekday,
    required this.focus,
    this.exercises = const [],
  });

  bool get isRestDay => exercises.isEmpty;
}
