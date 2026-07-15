import 'package:flutter/foundation.dart';

class WorkoutProgramStore {
  static final ValueNotifier<Set<String>> completedDays =
      ValueNotifier<Set<String>>({});

  static bool isCompleted(String day) {
    return completedDays.value.contains(day);
  }

  static void toggleCompleted(String day) {
    final updatedDays = Set<String>.from(completedDays.value);

    if (updatedDays.contains(day)) {
      updatedDays.remove(day);
    } else {
      updatedDays.add(day);
    }

    completedDays.value = updatedDays;
  }

  static void clearCompletedDays() {
    completedDays.value = {};
  }

  static int completedCount() {
    return completedDays.value.length;
  }
}
