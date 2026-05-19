class WorkoutExercise {
  final String name;
  final String sets;
  final String reps;
  final String note;

  const WorkoutExercise({
    required this.name,
    required this.sets,
    required this.reps,
    required this.note,
  });
}

class DailyWorkoutPlan {
  final String day;
  final String focus;
  final bool isRestDay;
  final List<WorkoutExercise> exercises;

  const DailyWorkoutPlan({
    required this.day,
    required this.focus,
    required this.isRestDay,
    required this.exercises,
  });
}