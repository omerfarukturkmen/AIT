/// UI-facing analysis result shown on ResultPage / history.
class AnalysisResult {
  final String exerciseName;
  final int score;
  final int riskPercent;
  final int repetitionCount;
  final int validReps;
  final int invalidReps;
  final double confidence;
  final double durationSeconds;
  final String duration;
  final int totalFrames;
  final int processedFrames;
  final double? minKneeAngle;
  final double? averageMinKneeAngle;
  final double? rangeOfMotion;
  final String selectedSide;
  final List<String> mistakes;
  final List<String> recommendations;

  /// Kept for compatibility; prefer [averageMinKneeAngle] on the result UI.
  final String movementAngle;

  const AnalysisResult({
    required this.exerciseName,
    required this.score,
    required this.riskPercent,
    required this.repetitionCount,
    required this.validReps,
    required this.invalidReps,
    required this.confidence,
    required this.durationSeconds,
    required this.duration,
    required this.totalFrames,
    required this.processedFrames,
    required this.minKneeAngle,
    required this.averageMinKneeAngle,
    required this.rangeOfMotion,
    required this.selectedSide,
    required this.mistakes,
    required this.recommendations,
    required this.movementAngle,
  });

  factory AnalysisResult.fromJson(Map<String, dynamic> json) {
    return AnalysisResult(
      exerciseName: json['exerciseName'] ?? '',
      score: json['score'] ?? 0,
      riskPercent: json['riskPercent'] ?? (100 - (json['score'] as int? ?? 0)),
      repetitionCount: json['repetitionCount'] ?? 0,
      validReps: json['validReps'] ?? 0,
      invalidReps: json['invalidReps'] ?? 0,
      confidence: (json['confidence'] ?? 0).toDouble(),
      durationSeconds: (json['durationSeconds'] ?? 0).toDouble(),
      duration: json['duration'] ?? '',
      totalFrames: json['totalFrames'] ?? 0,
      processedFrames: json['processedFrames'] ?? 0,
      minKneeAngle: (json['minKneeAngle'] as num?)?.toDouble(),
      averageMinKneeAngle: (json['averageMinKneeAngle'] as num?)?.toDouble(),
      rangeOfMotion: (json['rangeOfMotion'] as num?)?.toDouble(),
      selectedSide: json['selectedSide'] ?? 'unavailable',
      mistakes: List<String>.from(json['mistakes'] ?? []),
      recommendations: List<String>.from(json['recommendations'] ?? []),
      movementAngle: json['movementAngle'] ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'exerciseName': exerciseName,
      'score': score,
      'riskPercent': riskPercent,
      'repetitionCount': repetitionCount,
      'validReps': validReps,
      'invalidReps': invalidReps,
      'confidence': confidence,
      'durationSeconds': durationSeconds,
      'duration': duration,
      'totalFrames': totalFrames,
      'processedFrames': processedFrames,
      'minKneeAngle': minKneeAngle,
      'averageMinKneeAngle': averageMinKneeAngle,
      'rangeOfMotion': rangeOfMotion,
      'selectedSide': selectedSide,
      'mistakes': mistakes,
      'recommendations': recommendations,
      'movementAngle': movementAngle,
    };
  }
}
