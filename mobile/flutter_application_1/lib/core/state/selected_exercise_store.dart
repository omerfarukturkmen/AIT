import 'package:flutter/foundation.dart';

class SelectedExerciseStore {
  static final ValueNotifier<String> selectedExercise =
      ValueNotifier<String>('Squat');

  static void setExercise(String exerciseName) {
    selectedExercise.value = exerciseName;
  }
}