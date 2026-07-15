import '../models/analysis_result_model.dart';
import '../models/backend_analysis_response.dart';

/// Single mapping point: backend JSON model → UI AnalysisResult.
class AnalysisResultMapper {
  static AnalysisResult fromBackend(BackendAnalysisResponse backend) {
    final mistakes = backend.errors.isNotEmpty
        ? backend.errors.map(_humanizeError).toList()
        : const ['Belirgin form hatası algılanmadı.'];

    final depthLabel = backend.averageMinKneeAngle != null
        ? '${backend.averageMinKneeAngle!.toStringAsFixed(1)}°'
        : (backend.minKneeAngle != null
              ? '${backend.minKneeAngle!.toStringAsFixed(1)}°'
              : '-');

    final recommendations = <String>[
      if (backend.feedback.trim().isNotEmpty) backend.feedback,
      'Geçerli tekrar: ${backend.validReps}',
      'Geçersiz tekrar: ${backend.invalidReps}',
      'İşlenen frame: ${backend.processedFrames} / ${backend.totalFrames}',
      'Poz güveni: ${backend.confidencePercent.toStringAsFixed(1)}%',
      if (backend.selectedSide != 'unavailable')
        'Seçilen bacak/ortalama: ${backend.selectedSide}',
    ];

    return AnalysisResult(
      exerciseName: backend.exercise.isNotEmpty ? backend.exercise : 'squat',
      score: backend.score,
      riskPercent: backend.riskPercent,
      repetitionCount: backend.repetitionCount,
      validReps: backend.validReps,
      invalidReps: backend.invalidReps,
      confidence: backend.confidencePercent,
      durationSeconds: backend.durationSeconds,
      duration: backend.durationSeconds > 0
          ? '${backend.durationSeconds.toStringAsFixed(1)} sn'
          : '-',
      totalFrames: backend.totalFrames,
      processedFrames: backend.processedFrames,
      minKneeAngle: backend.minKneeAngle,
      averageMinKneeAngle: backend.averageMinKneeAngle,
      rangeOfMotion: backend.kneeRangeOfMotion,
      selectedSide: backend.selectedSide,
      mistakes: mistakes,
      recommendations: recommendations,
      movementAngle: depthLabel,
    );
  }

  static String _humanizeError(String code) {
    const map = {
      'insufficient_depth': 'Daha derine inmelisin.',
      'knee_angle_insufficient': 'Diz açın yeterli seviyeye ulaşmadı.',
      'too_deep_or_unstable':
          'Diz açın çok dar, hareketi kontrollü yapmalısın.',
      'too_fast': 'Hareketi daha kontrollü yapmalısın.',
      'incomplete_rep': 'Squat tekrarın tamamlanmadı.',
      'torso_lean': 'Üst gövdeni fazla öne egme.',
    };
    return map[code] ?? code;
  }
}
