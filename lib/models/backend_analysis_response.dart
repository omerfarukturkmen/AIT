/// Parsed result payload of a completed analysis (GET /analysis/{id}).
class BackendAnalysisResponse {
  final int? analysisId;
  final String exerciseType;
  final DateTime? createdAt;
  final String status;
  final String exercise;
  final int score;
  final int riskPercent;
  final String feedback;
  final int totalFrames;
  final int processedFrames;
  final int repetitionCount;
  final int validReps;
  final int invalidReps;
  final double confidencePercent;
  final double durationSeconds;
  final double meanLandmarkVisibility;
  final double landmarkDetectionRatio;
  final int landmarkFrames;
  final double? minKneeAngle;
  final double? averageMinKneeAngle;
  final double? kneeRangeOfMotion;
  final String selectedSide;
  final List<String> errors;
  final List<String> cameraWarnings;
  final List<Map<String, dynamic>> repHistory;
  final Map<String, dynamic> details;

  /// Diagnostic only — not for primary UI form metrics.
  final double averageMotion;

  const BackendAnalysisResponse({
    this.analysisId,
    this.exerciseType = '',
    this.createdAt,
    required this.status,
    required this.exercise,
    required this.score,
    required this.riskPercent,
    required this.feedback,
    required this.totalFrames,
    required this.processedFrames,
    required this.repetitionCount,
    required this.validReps,
    required this.invalidReps,
    required this.confidencePercent,
    required this.durationSeconds,
    required this.meanLandmarkVisibility,
    required this.landmarkDetectionRatio,
    required this.landmarkFrames,
    required this.minKneeAngle,
    required this.averageMinKneeAngle,
    required this.kneeRangeOfMotion,
    required this.selectedSide,
    required this.errors,
    required this.cameraWarnings,
    required this.repHistory,
    required this.details,
    required this.averageMotion,
  });

  factory BackendAnalysisResponse.fromJson(Map<String, dynamic> json) {
    final root = Map<String, dynamic>.from(json);
    final nested = root['data'] is Map
        ? Map<String, dynamic>.from(root['data'] as Map)
        : (root['analysis'] is Map
              ? Map<String, dynamic>.from(root['analysis'] as Map)
              : root);
    final details = nested['details'] is Map
        ? Map<String, dynamic>.from(nested['details'] as Map)
        : <String, dynamic>{};

    int asInt(dynamic v) {
      if (v == null) return 0;
      if (v is int) return v;
      if (v is double) return v.round();
      return int.tryParse(v.toString()) ?? 0;
    }

    double asDouble(dynamic v) {
      if (v == null) return 0.0;
      if (v is double) return v;
      if (v is int) return v.toDouble();
      return double.tryParse(v.toString()) ?? 0.0;
    }

    double? asNullableDouble(dynamic v) {
      if (v == null) return null;
      if (v is double) return v;
      if (v is int) return v.toDouble();
      return double.tryParse(v.toString());
    }

    List<String> asStringList(dynamic v) {
      if (v == null) return const [];
      if (v is List) return v.map((e) => e.toString()).toList();
      if (v is String && v.trim().isNotEmpty) return [v];
      return const [];
    }

    List<Map<String, dynamic>> asRepHistory(dynamic v) {
      if (v is! List) return const [];
      return v
          .whereType<Map>()
          .map((e) => Map<String, dynamic>.from(e))
          .toList();
    }

    final score = asInt(
      nested['score'] ??
          nested['accuracy'] ??
          root['score'] ??
          root['accuracy'],
    );
    final risk = asInt(
      nested['risk_percent'] ??
          details['risk_percent'] ??
          root['risk_percent'] ??
          (100 - score),
    );

    final rawId = nested['analysis_id'];
    final rawDate = nested['created_at'];

    return BackendAnalysisResponse(
      analysisId: rawId == null ? null : asInt(rawId),
      exerciseType: (nested['exercise_type'] ?? '').toString(),
      // The backend stores naive UTC timestamps.
      createdAt: rawDate == null
          ? null
          : DateTime.tryParse(
              rawDate.toString().endsWith('Z') ? '$rawDate' : '${rawDate}Z',
            )?.toLocal(),
      status: (nested['status'] ?? root['status'] ?? '').toString(),
      exercise:
          (nested['exercise_name'] ??
                  nested['exercise'] ??
                  root['exercise'] ??
                  '')
              .toString(),
      score: score,
      riskPercent: risk.clamp(0, 100),
      feedback: (nested['feedback'] ?? root['feedback'] ?? '').toString(),
      totalFrames: asInt(
        nested['total_frames'] ??
            details['total_frames'] ??
            root['total_frames'],
      ),
      processedFrames: asInt(
        nested['processed_frames'] ?? details['processed_frames'],
      ),
      repetitionCount: asInt(
        nested['repetition_count'] ?? root['repetition_count'],
      ),
      validReps: asInt(nested['valid_reps'] ?? details['valid_reps']),
      invalidReps: asInt(nested['invalid_reps'] ?? details['invalid_reps']),
      confidencePercent: asDouble(
        nested['confidence_percent'] ?? details['confidence_percent'],
      ),
      durationSeconds: asDouble(
        nested['duration_seconds'] ?? details['duration_seconds'],
      ),
      meanLandmarkVisibility: asDouble(
        nested['mean_landmark_visibility'] ??
            details['mean_landmark_visibility'] ??
            nested['ai_confidence'] ??
            details['ai_confidence'],
      ),
      landmarkDetectionRatio: asDouble(
        nested['landmark_detection_ratio'] ??
            details['landmark_detection_ratio'],
      ),
      landmarkFrames: asInt(
        nested['landmark_frames'] ?? details['landmark_frames'],
      ),
      minKneeAngle: asNullableDouble(
        nested['min_knee_angle'] ?? details['min_knee_angle'],
      ),
      averageMinKneeAngle: asNullableDouble(
        nested['average_min_knee_angle'] ?? details['average_min_knee_angle'],
      ),
      kneeRangeOfMotion: asNullableDouble(
        nested['knee_range_of_motion'] ?? details['knee_range_of_motion'],
      ),
      selectedSide:
          (nested['selected_side'] ?? details['selected_side'] ?? 'unavailable')
              .toString(),
      errors: asStringList(nested['errors']),
      cameraWarnings: asStringList(nested['camera_warnings']),
      repHistory: asRepHistory(nested['rep_history'] ?? details['rep_history']),
      details: details,
      averageMotion: asDouble(
        nested['average_motion'] ??
            details['average_motion'] ??
            details['average_movement'] ??
            root['average_motion'],
      ),
    );
  }
}
