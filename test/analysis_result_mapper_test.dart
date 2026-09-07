import 'package:flutter_application_1/data/analysis_result_mapper.dart';
import 'package:flutter_application_1/models/backend_analysis_response.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('mapper keeps repetitionCount separate from frame counts', () {
    final backend = BackendAnalysisResponse.fromJson({
      'status': 'success',
      'data': {
        'score': 85,
        'risk_percent': 15,
        'repetition_count': 2,
        'valid_reps': 2,
        'invalid_reps': 0,
        'total_frames': 332,
        'processed_frames': 320,
        'confidence_percent': 88.7,
        'duration_seconds': 11.08,
        'average_min_knee_angle': 78.5,
        'min_knee_angle': 76.0,
        'knee_range_of_motion': 85.0,
        'exercise_name': 'squat',
        'feedback': 'ok',
        'errors': <String>[],
        'details': {
          'total_frames': 332,
          'processed_frames': 320,
          'average_min_knee_angle': 78.5,
          'confidence_percent': 88.7,
          'risk_percent': 15,
        },
      },
    });

    final result = AnalysisResultMapper.fromBackend(backend);

    expect(result.repetitionCount, 2);
    expect(result.totalFrames, 332);
    expect(result.processedFrames, 320);
    expect(result.score, 85);
    expect(result.riskPercent, 15);
    expect(result.confidence, 88.7);
    expect(result.averageMinKneeAngle, 78.5);
    expect(result.repetitionCount, isNot(equals(result.totalFrames)));
    expect(result.repetitionCount, isNot(equals(result.processedFrames)));
  });

  test('mapper uses no-error message when errors empty', () {
    final backend = BackendAnalysisResponse.fromJson({
      'status': 'success',
      'data': {
        'score': 90,
        'risk_percent': 10,
        'repetition_count': 1,
        'total_frames': 100,
        'processed_frames': 90,
        'confidence_percent': 90.0,
        'duration_seconds': 3.0,
        'exercise_name': 'squat',
        'feedback': '',
        'errors': <String>[],
      },
    });
    final result = AnalysisResultMapper.fromBackend(backend);
    expect(result.mistakes, ['Belirgin form hatası algılanmadı.']);
  });
}
