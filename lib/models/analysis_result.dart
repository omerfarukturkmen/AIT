class AnalysisResult {
  final String status;
  final String exercise;
  final int accuracy;
  final String feedback;
  final double averageMotion;
  final int totalFrames;

  AnalysisResult({
    required this.status,
    required this.exercise,
    required this.accuracy,
    required this.feedback,
    required this.averageMotion,
    required this.totalFrames,
  });

  factory AnalysisResult.fromJson(Map<String, dynamic> json) {
    return AnalysisResult(
      status: json["status"] ?? "",
      exercise: json["exercise"] ?? "",
      accuracy: json["accuracy"] ?? 0,
      feedback: json["feedback"] ?? "",
      averageMotion: (json["average_motion"] ?? 0).toDouble(),
      totalFrames: json["total_frames"] ?? 0,
    );
  }
}
