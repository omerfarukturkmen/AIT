import '../data/exercise_catalog.dart';
import 'backend_analysis_response.dart';

/// Result of one video analysis. Holds raw values and form-issue codes;
/// screens turn them into text in the user's language.
class AnalysisResult {
  final int? id;
  final DateTime createdAt;
  final ExerciseId exercise;
  final int score;
  final int repetitionCount;
  final int validReps;
  final int invalidReps;

  /// Pose-detection confidence, 0-100.
  final double confidencePercent;
  final double durationSeconds;
  final double? minKneeAngle;
  final double? averageMinKneeAngle;
  final double? kneeRangeOfMotion;

  /// Analyzer codes such as `insufficient_depth` or `elbows_flared`.
  final List<String> issueCodes;

  const AnalysisResult({
    required this.id,
    required this.createdAt,
    required this.exercise,
    required this.score,
    required this.repetitionCount,
    required this.validReps,
    required this.invalidReps,
    required this.confidencePercent,
    required this.durationSeconds,
    required this.minKneeAngle,
    required this.averageMinKneeAngle,
    required this.kneeRangeOfMotion,
    required this.issueCodes,
  });

  factory AnalysisResult.fromBackend(BackendAnalysisResponse response) {
    return AnalysisResult(
      id: response.analysisId,
      createdAt: response.createdAt ?? DateTime.now(),
      exercise:
          exerciseFromApiKey(response.exerciseType) ??
          exerciseFromApiKey(response.exercise) ??
          ExerciseId.squat,
      score: response.score.clamp(0, 100),
      repetitionCount: response.repetitionCount,
      validReps: response.validReps,
      invalidReps: response.invalidReps,
      confidencePercent: response.confidencePercent,
      durationSeconds: response.durationSeconds,
      minKneeAngle: response.minKneeAngle,
      averageMinKneeAngle: response.averageMinKneeAngle,
      kneeRangeOfMotion: response.kneeRangeOfMotion,
      issueCodes: response.errors.toSet().toList(),
    );
  }

  factory AnalysisResult.fromPayload(Map<String, dynamic> json) =>
      AnalysisResult.fromBackend(BackendAnalysisResponse.fromJson(json));
}
