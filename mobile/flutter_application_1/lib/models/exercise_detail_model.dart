class ExerciseDetail {
  final String name;
  final String description;
  final List<String> targetMuscles;
  final List<String> commonMistakes;
  final List<String> tips;

  const ExerciseDetail({
    required this.name,
    required this.description,
    required this.targetMuscles,
    required this.commonMistakes,
    required this.tips,
  });
}
