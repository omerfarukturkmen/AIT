class AnalysisResult {
  final String exerciseName;
  final int score;
  final String movementAngle;
  final int repetitionCount;
  final double confidence;
  final String duration;
  final List<String> mistakes;
  final List<String> recommendations;

  const AnalysisResult({
    required this.exerciseName,
    required this.score,
    required this.movementAngle,
    required this.repetitionCount,
    required this.confidence,
    required this.duration,
    required this.mistakes,
    required this.recommendations,
  });

  factory AnalysisResult.fromJson(Map<String, dynamic> json) {
    return AnalysisResult(
      exerciseName: json['exerciseName'] ?? '',
      score: json['score'] ?? 0,
      movementAngle: json['movementAngle'] ?? '',
      repetitionCount: json['repetitionCount'] ?? 0,
      confidence: (json['confidence'] ?? 0).toDouble(),
      duration: json['duration'] ?? '',
      mistakes: List<String>.from(json['mistakes'] ?? []),
      recommendations: List<String>.from(json['recommendations'] ?? []),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'exerciseName': exerciseName,
      'score': score,
      'movementAngle': movementAngle,
      'repetitionCount': repetitionCount,
      'confidence': confidence,
      'duration': duration,
      'mistakes': mistakes,
      'recommendations': recommendations,
    };
  }
}
