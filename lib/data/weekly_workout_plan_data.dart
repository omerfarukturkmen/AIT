import '../models/workout_plan_model.dart';
import 'exercise_catalog.dart';

/// Default beginner weekly plan.
final List<DailyWorkoutPlan> weeklyWorkoutPlan = [
  DailyWorkoutPlan(
    weekday: DateTime.monday,
    focus: (l10n) => l10n.focusLowerBody,
    exercises: [
      WorkoutExercise(
        exercise: ExerciseId.squat,
        sets: 3,
        reps: 12,
        note: (l10n) => l10n.noteKneesOverToes,
      ),
      WorkoutExercise(
        exercise: ExerciseId.lunge,
        sets: 3,
        reps: 10,
        note: (l10n) => l10n.noteTorsoUpright,
      ),
      WorkoutExercise(
        exercise: ExerciseId.plank,
        sets: 3,
        seconds: 40,
        note: (l10n) => l10n.noteCoreBraced,
      ),
    ],
  ),
  DailyWorkoutPlan(
    weekday: DateTime.tuesday,
    focus: (l10n) => l10n.focusUpperBody,
    exercises: [
      WorkoutExercise(
        exercise: ExerciseId.pushUp,
        sets: 3,
        reps: 10,
        note: (l10n) => l10n.noteHipsShouldersLine,
      ),
      WorkoutExercise(
        exercise: ExerciseId.shoulderPress,
        sets: 3,
        reps: 12,
        note: (l10n) => l10n.noteNoLowerBackArch,
      ),
    ],
  ),
  DailyWorkoutPlan(
    weekday: DateTime.wednesday,
    focus: (l10n) => l10n.focusRecovery,
  ),
  DailyWorkoutPlan(
    weekday: DateTime.thursday,
    focus: (l10n) => l10n.focusFullBody,
    exercises: [
      WorkoutExercise(
        exercise: ExerciseId.squat,
        sets: 3,
        reps: 12,
        note: (l10n) => l10n.noteControlledDescent,
      ),
      WorkoutExercise(
        exercise: ExerciseId.pushUp,
        sets: 3,
        reps: 8,
        note: (l10n) => l10n.noteCoreStability,
      ),
      WorkoutExercise(
        exercise: ExerciseId.plank,
        sets: 3,
        seconds: 45,
        note: (l10n) => l10n.noteNoSag,
      ),
    ],
  ),
  DailyWorkoutPlan(
    weekday: DateTime.friday,
    focus: (l10n) => l10n.focusPosterior,
    exercises: [
      WorkoutExercise(
        exercise: ExerciseId.deadlift,
        sets: 3,
        reps: 10,
        note: (l10n) => l10n.noteNeutralBack,
      ),
      WorkoutExercise(
        exercise: ExerciseId.lunge,
        sets: 3,
        reps: 10,
        note: (l10n) => l10n.noteBalance,
      ),
    ],
  ),
  DailyWorkoutPlan(
    weekday: DateTime.saturday,
    focus: (l10n) => l10n.focusCoreMobility,
    exercises: [
      WorkoutExercise(
        exercise: ExerciseId.plank,
        sets: 4,
        seconds: 35,
        note: (l10n) => l10n.noteBreathing,
      ),
      WorkoutExercise(
        exercise: ExerciseId.squat,
        sets: 2,
        reps: 15,
        note: (l10n) => l10n.noteMobility,
      ),
    ],
  ),
  DailyWorkoutPlan(weekday: DateTime.sunday, focus: (l10n) => l10n.focusRest),
];

DailyWorkoutPlan planFor(int weekday) =>
    weeklyWorkoutPlan.firstWhere((plan) => plan.weekday == weekday);
