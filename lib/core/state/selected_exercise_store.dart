import 'package:flutter/foundation.dart';

import '../../data/exercise_catalog.dart';

/// Exercise chosen for the next analysis (always one the AI supports).
class SelectedExerciseStore {
  static final ValueNotifier<ExerciseId> selectedExercise = ValueNotifier(
    ExerciseId.squat,
  );

  static void select(ExerciseId exercise) {
    if (exercise.analysisSupported) selectedExercise.value = exercise;
  }
}
