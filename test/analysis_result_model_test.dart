import 'package:flutter_application_1/core/state/analysis_history_store.dart';
import 'package:flutter_application_1/data/exercise_catalog.dart';
import 'package:flutter_application_1/l10n/analysis_messages.dart';
import 'package:flutter_application_1/l10n/form_issues.dart';
import 'package:flutter_application_1/models/analysis_result_model.dart';
import 'package:flutter_test/flutter_test.dart';

import 'helpers.dart';

void main() {
  test('parses a completed analysis payload', () {
    final result = AnalysisResult.fromPayload(
      resultPayload(
        analysisId: 12,
        score: 85,
        reps: 2,
        errors: ['torso_lean', 'torso_lean'],
      ),
    );

    expect(result.id, 12);
    expect(result.exercise, ExerciseId.squat);
    expect(result.score, 85);
    expect(result.repetitionCount, 2);
    expect(result.averageMinKneeAngle, 78.5);
    expect(result.confidencePercent, 88.7);
    expect(result.issueCodes, ['torso_lean']); // de-duplicated
    // Naive UTC timestamp from the server becomes local time.
    expect(result.createdAt, DateTime.utc(2026, 10, 26, 8, 15).toLocal());
  });

  test('rep count is not confused with frame counts', () {
    final result = AnalysisResult.fromPayload(resultPayload(reps: 2));
    expect(result.repetitionCount, 2);
  });

  test('push-up type maps to the push-up exercise', () {
    final result = AnalysisResult.fromPayload(
      resultPayload(exerciseType: 'push-up'),
    );
    expect(result.exercise, ExerciseId.pushUp);
  });

  test('every analyzer code has a specific localized text', () {
    const codes = [
      'insufficient_depth',
      'squat_depth_reach',
      'knee_angle_insufficient',
      'too_deep_or_unstable',
      'too_fast',
      'incomplete_rep',
      'torso_lean',
      'excessive_forward_lean',
      'hip_flexion_mismatch',
      'hips_sagging',
      'hips_not_aligned',
      'hips_too_high',
      'back_bent',
      'back_bending',
      'not_low_enough',
      'incomplete_up',
      'elbows_flared',
      'shoulder_alignment_issue',
      'shoulder_position',
    ];
    final generic = formIssue(trL10n, 'unknown_code');
    for (final code in codes) {
      expect(formIssue(trL10n, code).title, isNot(generic.title), reason: code);
      expect(
        formIssue(enL10n, code).title,
        isNot(formIssue(trL10n, code).title),
        reason: code,
      );
    }
  });

  test('only squat and push-up can be analyzed', () {
    expect(ExerciseId.values.where((e) => e.analysisSupported), [
      ExerciseId.squat,
      ExerciseId.pushUp,
    ]);
  });

  test('warning codes are read and localized; unknown ones are skipped', () {
    final result = AnalysisResult.fromPayload(
      resultPayload(warningCodes: ['low_frame_rate', 'something_new']),
    );
    expect(result.warningCodes, ['low_frame_rate', 'something_new']);
    expect(
      analysisWarningText(enL10n, 'low_frame_rate'),
      enL10n.warningLowFrameRate,
    );
    expect(analysisWarningText(trL10n, 'something_new'), isNull);
  });

  test('a video without a finished rep is not scored', () {
    final none = AnalysisResult.fromPayload(
      resultPayload(score: 0, reps: 0, errors: ['no_completed_reps']),
    );
    expect(none.isScored, isFalse);
    expect(AnalysisResult.fromPayload(resultPayload()).isScored, isTrue);
  });

  test('unscored analyses stay out of the average and best score', () {
    AnalysisHistoryStore.results.value = [
      AnalysisResult.fromPayload(resultPayload(score: 0, reps: 0)),
      AnalysisResult.fromPayload(resultPayload(score: 80)),
      AnalysisResult.fromPayload(resultPayload(score: 90)),
    ];
    addTearDown(AnalysisHistoryStore.clearHistory);
    expect(AnalysisHistoryStore.averageScore, 85);
    expect(AnalysisHistoryStore.bestScore, 90);
  });
}
