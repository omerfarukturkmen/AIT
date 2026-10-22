import 'dart:io';

import '../../data/api_service.dart';
import '../../models/analysis_result_model.dart';

/// File-based entry point; shares upload, auth and error handling with
/// [ApiService].
class AnalysisService {
  Future<AnalysisResult> analyzeVideo({
    required File videoFile,
    required String exerciseName,
  }) async {
    return ApiService.uploadVideoBytes(
      videoBytes: await videoFile.readAsBytes(),
      fileName: videoFile.uri.pathSegments.last,
      exerciseName: exerciseName,
    );
  }
}
