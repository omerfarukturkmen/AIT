import 'app_localizations.dart';

/// A detected form issue and how to correct it, in the user's language.
class FormIssue {
  final String title;
  final String fix;

  const FormIssue(this.title, this.fix);
}

/// Maps analyzer codes (squat and push-up) to localized text. Several codes
/// are aliases produced by different analyzer versions.
FormIssue formIssue(AppLocalizations l10n, String code) {
  return switch (code) {
    'insufficient_depth' || 'squat_depth_reach' => FormIssue(
      l10n.issueInsufficientDepth,
      l10n.issueInsufficientDepthFix,
    ),
    'knee_angle_insufficient' => FormIssue(
      l10n.issueKneeAngle,
      l10n.issueKneeAngleFix,
    ),
    'too_deep_or_unstable' => FormIssue(
      l10n.issueTooDeep,
      l10n.issueTooDeepFix,
    ),
    'too_fast' => FormIssue(l10n.issueTooFast, l10n.issueTooFastFix),
    'incomplete_rep' => FormIssue(
      l10n.issueIncompleteRep,
      l10n.issueIncompleteRepFix,
    ),
    'no_completed_reps' => FormIssue(l10n.issueNoReps, l10n.issueNoRepsFix),
    'torso_lean' || 'excessive_forward_lean' => FormIssue(
      l10n.issueTorsoLean,
      l10n.issueTorsoLeanFix,
    ),
    'hip_flexion_mismatch' => FormIssue(
      l10n.issueHipHinge,
      l10n.issueHipHingeFix,
    ),
    'hips_sagging' || 'hips_not_aligned' => FormIssue(
      l10n.issueHipsSagging,
      l10n.issueHipsSaggingFix,
    ),
    'hips_too_high' => FormIssue(
      l10n.issueHipsTooHigh,
      l10n.issueHipsTooHighFix,
    ),
    'back_bent' ||
    'back_bending' => FormIssue(l10n.issueBackBent, l10n.issueBackBentFix),
    'not_low_enough' => FormIssue(
      l10n.issueNotLowEnough,
      l10n.issueNotLowEnoughFix,
    ),
    'incomplete_up' => FormIssue(
      l10n.issueIncompleteUp,
      l10n.issueIncompleteUpFix,
    ),
    'elbows_flared' => FormIssue(
      l10n.issueElbowsFlared,
      l10n.issueElbowsFlaredFix,
    ),
    'shoulder_alignment_issue' || 'shoulder_position' => FormIssue(
      l10n.issueShoulders,
      l10n.issueShouldersFix,
    ),
    _ => FormIssue(l10n.issueGeneric, l10n.issueGenericFix),
  };
}
