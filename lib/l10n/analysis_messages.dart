import 'app_localizations.dart';

/// Why the backend could not analyze a video (`error_code` of a failed
/// analysis), in the user's language. Null for codes this app doesn't know.
String? analysisFailureText(AppLocalizations l10n, String? code) {
  return switch (code) {
    'no_person_visible' => l10n.analysisErrorNoPerson,
    'video_unreadable' => l10n.analysisErrorUnreadable,
    'video_too_short' => l10n.analysisErrorTooShort,
    'body_out_of_frame' => l10n.analysisErrorBodyOutOfFrame,
    'exercise_unsupported' => l10n.analysisErrorUnsupported,
    'video_unsuitable' => l10n.analysisErrorUnsuitable,
    'analysis_unavailable' => l10n.analysisErrorUnavailable,
    'analysis_interrupted' => l10n.analysisErrorInterrupted,
    'analysis_failed' => l10n.errorAnalysisFailed,
    _ => null,
  };
}

/// Recording-quality warnings of a finished analysis (`warning_codes`).
/// Null for codes this app doesn't know, so they are skipped.
String? analysisWarningText(AppLocalizations l10n, String code) {
  return switch (code) {
    'camera_too_far' => l10n.warningCameraTooFar,
    'camera_too_close' => l10n.warningCameraTooClose,
    'low_pose_confidence' => l10n.warningLowPoseConfidence,
    'body_partly_out_of_frame' => l10n.warningBodyPartlyOut,
    'low_frame_rate' => l10n.warningLowFrameRate,
    _ => null,
  };
}
