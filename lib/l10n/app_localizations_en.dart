// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get appName => 'AIT';

  @override
  String get appTagline => 'AI-powered form analysis';

  @override
  String get commonCancel => 'Cancel';

  @override
  String get commonClose => 'Close';

  @override
  String get commonContinue => 'Continue';

  @override
  String get commonSave => 'Save';

  @override
  String get commonDelete => 'Delete';

  @override
  String get commonRetry => 'Try again';

  @override
  String get commonOk => 'OK';

  @override
  String get commonSeeAll => 'See all';

  @override
  String get commonComingSoon => 'Coming soon';

  @override
  String get commonBack => 'Back';

  @override
  String get commonDone => 'Done';

  @override
  String get commonEdit => 'Edit';

  @override
  String get commonAdd => 'Add';

  @override
  String get commonNotSet => 'Not set';

  @override
  String get errorNetwork =>
      'Couldn\'t reach the server. Check your internet connection.';

  @override
  String get errorTimeout =>
      'The server took too long to respond. Please try again.';

  @override
  String get errorSessionExpired =>
      'Your session has expired. Please sign in again.';

  @override
  String get errorInvalidCredentials => 'Incorrect e-mail or password.';

  @override
  String get errorEmailTaken => 'An account with this e-mail already exists.';

  @override
  String get errorInvalidInput =>
      'Some details are invalid. Please check them.';

  @override
  String get errorInvalidCode => 'The code is invalid or has expired.';

  @override
  String get errorTooLarge => 'The video file is too large.';

  @override
  String get errorUnsupportedMedia =>
      'This file isn\'t a valid video. Upload an MP4, MOV or AVI file.';

  @override
  String get errorRateLimited =>
      'Too many requests. Please try again in a moment.';

  @override
  String get errorNotConfigured => 'This feature hasn\'t been set up yet.';

  @override
  String get errorUnavailable =>
      'This service is unavailable right now. Please try again later.';

  @override
  String get errorAnalysisFailed =>
      'The video couldn\'t be analyzed. Try a clear video that shows your whole body.';

  @override
  String get analysisErrorNoPerson =>
      'Your body wasn\'t clearly visible in the video. Keep the phone steady, get your whole body in frame and record again in good light.';

  @override
  String get analysisErrorUnreadable =>
      'The video couldn\'t be opened or is incomplete. The file may be damaged; record it again with your phone\'s camera and upload it.';

  @override
  String get analysisErrorTooShort =>
      'The video is too short. Upload a video of at least 2 seconds with at least one full repetition.';

  @override
  String get analysisErrorBodyOutOfFrame =>
      'Part of your body (usually your feet or knees) was out of frame. Move the phone back so you\'re visible from head to toe.';

  @override
  String get analysisErrorUnsupported =>
      'This exercise can\'t be analyzed yet.';

  @override
  String get analysisErrorUnsuitable =>
      'The video couldn\'t be read or isn\'t suitable for analysis. Upload a clear, short video.';

  @override
  String get analysisErrorUnavailable =>
      'The analysis service isn\'t ready right now. Please try again later.';

  @override
  String get analysisErrorInterrupted =>
      'The analysis was interrupted because the server restarted. Please upload the video again.';

  @override
  String get warningTitle => 'About this recording';

  @override
  String get warningCameraTooFar =>
      'The camera was too far away; move a little closer next time.';

  @override
  String get warningCameraTooClose =>
      'The camera was too close; step back a little next time.';

  @override
  String get warningLowPoseConfidence =>
      'Your body wasn\'t clearly detected at times; make sure your whole body is in frame.';

  @override
  String get warningBodyPartlyOut =>
      'Your body wasn\'t fully visible in some frames; keep that in mind when reading the results.';

  @override
  String get warningLowFrameRate =>
      'The video\'s frame rate is low, so the results may be less reliable.';

  @override
  String get errorServer =>
      'Something went wrong on our side. Please try again.';

  @override
  String get errorUnknown => 'Something went wrong. Please try again.';

  @override
  String get exerciseSquat => 'Squat';

  @override
  String get exercisePushUp => 'Push-up';

  @override
  String get exercisePlank => 'Plank';

  @override
  String get exerciseLunge => 'Lunge';

  @override
  String get exerciseDeadlift => 'Deadlift';

  @override
  String get exerciseShoulderPress => 'Shoulder press';

  @override
  String get exerciseSquatDescription =>
      'A fundamental compound movement for lower-body strength. Hip, knee and ankle control determine good form.';

  @override
  String get exercisePushUpDescription =>
      'A functional movement that builds chest, shoulder and arm strength while training trunk stability.';

  @override
  String get exercisePlankDescription =>
      'An isometric exercise that builds core endurance and postural stability.';

  @override
  String get exerciseLungeDescription =>
      'A lower-body movement that builds single-leg strength, balance and coordination.';

  @override
  String get exerciseDeadliftDescription =>
      'A fundamental strength exercise built on the hip hinge that strengthens the posterior chain.';

  @override
  String get exerciseShoulderPressDescription =>
      'A pressing movement for shoulder and arm strength that requires trunk control.';

  @override
  String get muscleCore => 'Core muscles';

  @override
  String get muscleCalves => 'Calves';

  @override
  String get squatMistake1 => 'Knees caving inward';

  @override
  String get squatMistake2 => 'Leaning the torso too far forward';

  @override
  String get squatMistake3 => 'Heels lifting off the floor';

  @override
  String get squatMistake4 => 'Not squatting deep enough';

  @override
  String get squatTip1 => 'Place your feet shoulder-width apart.';

  @override
  String get squatTip2 => 'Keep your knees in line with your toes.';

  @override
  String get squatTip3 => 'Keep a controlled tempo on the way down and up.';

  @override
  String get pushUpMistake1 => 'Hips sagging';

  @override
  String get pushUpMistake2 => 'Elbows flaring out too wide';

  @override
  String get pushUpMistake3 => 'Pushing the head forward';

  @override
  String get pushUpMistake4 => 'Not completing the full range';

  @override
  String get pushUpTip1 => 'Keep shoulders, hips and feet in one line.';

  @override
  String get pushUpTip2 => 'Bend your elbows at about 45° to your body.';

  @override
  String get pushUpTip3 =>
      'Lower your chest close to the floor and press until your arms are straight.';

  @override
  String get plankMistake1 => 'Lower back sagging';

  @override
  String get plankMistake2 => 'Hips raised too high';

  @override
  String get plankMistake3 => 'Neck not kept neutral';

  @override
  String get plankTip1 => 'Keep your elbows under your shoulders.';

  @override
  String get plankTip2 => 'Brace your abs and glutes.';

  @override
  String get plankTip3 => 'Don\'t hold your breath; breathe steadily.';

  @override
  String get lungeMistake1 => 'Front knee travelling far past the toes';

  @override
  String get lungeMistake2 => 'Torso dropping forward';

  @override
  String get lungeMistake3 => 'Losing balance';

  @override
  String get lungeTip1 => 'Take a long enough step.';

  @override
  String get lungeTip2 => 'Keep your torso upright.';

  @override
  String get lungeTip3 => 'Lower your back knee close to the floor.';

  @override
  String get deadliftMistake1 => 'Rounding the back';

  @override
  String get deadliftMistake2 => 'Letting the bar drift away from the body';

  @override
  String get deadliftMistake3 => 'Starting the lift with the lower back';

  @override
  String get deadliftTip1 => 'Start the movement by hinging at the hips.';

  @override
  String get deadliftTip2 => 'Keep the bar close to your legs.';

  @override
  String get deadliftTip3 => 'Keep your back neutral and braced.';

  @override
  String get shoulderPressMistake1 => 'Over-arching the lower back';

  @override
  String get shoulderPressMistake2 => 'Elbows flaring out too wide';

  @override
  String get shoulderPressMistake3 => 'Using a partial range of motion';

  @override
  String get shoulderPressTip1 => 'Brace your core to keep your torso stable.';

  @override
  String get shoulderPressTip2 =>
      'Press the weight in a straight line overhead.';

  @override
  String get shoulderPressTip3 => 'Lower the weight with control.';

  @override
  String get issueInsufficientDepth => 'You didn\'t squat deep enough.';

  @override
  String get issueInsufficientDepthFix =>
      'Aim to lower your hips to knee level.';

  @override
  String get issueKneeAngle => 'Your knees didn\'t bend enough.';

  @override
  String get issueKneeAngleFix =>
      'Push your hips back and bend your knees further.';

  @override
  String get issueTooDeep =>
      'You went too deep or lost stability at the bottom.';

  @override
  String get issueTooDeepFix =>
      'Stay at a depth where you can stay in control at the bottom.';

  @override
  String get issueTooFast => 'You moved too fast.';

  @override
  String get issueTooFastFix =>
      'Take about 2 seconds on the way down and rise with control.';

  @override
  String get issueIncompleteRep => 'Some repetitions weren\'t completed.';

  @override
  String get issueIncompleteRepFix =>
      'Go all the way down and all the way up on every rep.';

  @override
  String get issueTorsoLean => 'Your torso leaned too far forward.';

  @override
  String get issueTorsoLeanFix => 'Keep your chest up and look ahead.';

  @override
  String get issueHipHinge => 'You didn\'t hinge at the hips on the way down.';

  @override
  String get issueHipHingeFix => 'Start the descent by pushing your hips back.';

  @override
  String get issueHipsSagging => 'Your hips sagged.';

  @override
  String get issueHipsSaggingFix =>
      'Brace your abs and glutes to keep your body straight.';

  @override
  String get issueHipsTooHigh => 'Your hips were too high.';

  @override
  String get issueHipsTooHighFix =>
      'Lower your hips in line with your shoulders and heels.';

  @override
  String get issueBackBent => 'Your back appears bent.';

  @override
  String get issueBackBentFix => 'Form a straight line from head to heels.';

  @override
  String get issueNotLowEnough => 'Your chest didn\'t get low enough.';

  @override
  String get issueNotLowEnoughFix =>
      'Lower until your elbows bend to about 90°.';

  @override
  String get issueIncompleteUp => 'Your arms didn\'t fully extend.';

  @override
  String get issueIncompleteUpFix =>
      'Fully straighten your arms at the top of every rep.';

  @override
  String get issueElbowsFlared => 'Your elbows flared out too wide.';

  @override
  String get issueElbowsFlaredFix =>
      'Keep your elbows at about 45° to your body.';

  @override
  String get issueShoulders => 'Your shoulder alignment slipped.';

  @override
  String get issueShouldersFix =>
      'Place your hands directly under your shoulders.';

  @override
  String get issueGeneric => 'There\'s something to improve in your form.';

  @override
  String get issueGenericFix => 'Repeat the movement slowly and with control.';

  @override
  String get issueNoReps => 'No completed repetition was found.';

  @override
  String get issueNoRepsFix =>
      'Complete the movement fully at least once and make sure the camera sees your whole body.';

  @override
  String get issueNoneTitle => 'No clear form issues found.';

  @override
  String get issueNoneMessage =>
      'Keep the same control and gradually increase your repetitions.';

  @override
  String programSetsReps(int sets, int reps) {
    return '$sets sets × $reps reps';
  }

  @override
  String programSetsSeconds(int sets, int seconds) {
    return '$sets sets × $seconds s';
  }

  @override
  String get focusLowerBody => 'Lower body';

  @override
  String get focusUpperBody => 'Upper body';

  @override
  String get focusRecovery => 'Recovery';

  @override
  String get focusFullBody => 'Full body';

  @override
  String get focusPosterior => 'Posterior chain';

  @override
  String get focusCoreMobility => 'Core and mobility';

  @override
  String get focusRest => 'Rest';

  @override
  String get noteKneesOverToes => 'Keep knees in line with your toes.';

  @override
  String get noteTorsoUpright => 'Keep your torso upright.';

  @override
  String get noteCoreBraced => 'Keep your core braced.';

  @override
  String get noteHipsShouldersLine => 'Keep hips and shoulders in line.';

  @override
  String get noteNoLowerBackArch => 'Don\'t over-arch your lower back.';

  @override
  String get noteControlledDescent => 'Lower with control.';

  @override
  String get noteCoreStability => 'Keep your trunk stable.';

  @override
  String get noteNoSag => 'Don\'t let your lower back sag.';

  @override
  String get noteNeutralBack => 'Keep your back neutral.';

  @override
  String get noteBalance => 'Focus on balance.';

  @override
  String get noteBreathing => 'Keep breathing steadily.';

  @override
  String get noteMobility => 'Focus on range of motion.';

  @override
  String get onboardingSkip => 'Skip';

  @override
  String get onboardingStart => 'Get started';

  @override
  String get onboardingCaptureTitle => 'Record your exercise';

  @override
  String get onboardingCaptureBody =>
      'Record with your camera or pick a video from your gallery. A short clip showing your whole body is enough.';

  @override
  String get onboardingAnalyzeTitle => 'Get your form assessed';

  @override
  String get onboardingAnalyzeBody =>
      'The AI counts your reps, scores your form and shows what to correct.';

  @override
  String get onboardingProgressTitle => 'Track your progress';

  @override
  String get onboardingProgressBody =>
      'Your analyses are saved to your account. See how your score, weight and measurements change over time.';

  @override
  String get commonPleaseWait => 'Please wait…';

  @override
  String get validationNameRequired => 'Your full name is required.';

  @override
  String get validationNameFull => 'Please enter your first and last name.';

  @override
  String get validationEmailRequired => 'E-mail address is required.';

  @override
  String get validationEmailInvalid =>
      'Enter a valid e-mail address (e.g. name@example.com).';

  @override
  String get validationPasswordRequired => 'Password is required.';

  @override
  String validationPasswordMin(int min) {
    return 'Password must be at least $min characters.';
  }

  @override
  String validationPasswordMax(int max) {
    return 'Password can be at most $max characters.';
  }

  @override
  String get validationPasswordLetterDigit =>
      'Password must contain at least one letter and one digit.';

  @override
  String get validationConfirmRequired => 'Re-enter your password.';

  @override
  String get validationPasswordsMismatch => 'Passwords don\'t match.';

  @override
  String get validationCode => 'Enter the 6-digit code.';

  @override
  String get authShowPassword => 'Show password';

  @override
  String get authHidePassword => 'Hide password';

  @override
  String get authGoogleContinue => 'Continue with Google';

  @override
  String get authGoogleSignUp => 'Sign up with Google';

  @override
  String get authAppleContinue => 'Continue with Apple';

  @override
  String get authAppleSignUp => 'Sign up with Apple';

  @override
  String get authOr => 'or';

  @override
  String authWelcomeBack(String name) {
    return 'Welcome back, $name!';
  }

  @override
  String authAccountCreated(String name) {
    return 'Your account is ready. Welcome, $name!';
  }

  @override
  String get authEmail => 'E-mail address';

  @override
  String get authEmailHint => 'name@example.com';

  @override
  String get authPassword => 'Password';

  @override
  String get authConfirmPassword => 'Confirm password';

  @override
  String get authFullName => 'Full name';

  @override
  String get authFullNameHint => 'Jane Smith';

  @override
  String get authRememberMe => 'Remember me';

  @override
  String get authForgotPassword => 'Forgot password?';

  @override
  String get authSignIn => 'Sign in';

  @override
  String get authSigningIn => 'Signing in…';

  @override
  String get authSignUp => 'Sign up';

  @override
  String get authCreateAccount => 'Create account';

  @override
  String get authCreatingAccount => 'Creating account…';

  @override
  String get authNoAccount => 'Don\'t have an account?';

  @override
  String get authHaveAccount => 'Already have an account?';

  @override
  String get authTermsPrefix => 'I have read and accept the ';

  @override
  String get authTermsMiddle => ' and the ';

  @override
  String get authTermsSuffix => '.';

  @override
  String get authTermsRequired => 'You need to accept the terms to continue.';

  @override
  String authSocialNotConfigured(String provider) {
    return 'Sign-in with $provider isn\'t available on this device yet. You can continue with e-mail and password for now.';
  }

  @override
  String get authLoginTitle => 'Welcome back';

  @override
  String get authLoginSubtitle => 'Sign in to pick up where you left off.';

  @override
  String get authRegisterTitle => 'Create your account';

  @override
  String get authRegisterSubtitle =>
      'Your analyses are saved to your account so you can follow your progress on any device.';

  @override
  String get authHeroTitle => 'Better form,\nrep after rep.';

  @override
  String get authHeroBody =>
      'Upload a video and let the AI count your reps and assess your form.';

  @override
  String get authFeatureCaptureTitle => 'Record or upload';

  @override
  String get authFeatureCaptureBody =>
      'Record with your camera or pick a video.';

  @override
  String get authFeatureFeedbackTitle => 'Clear feedback';

  @override
  String get authFeatureFeedbackBody =>
      'Form score, rep count and specific corrections.';

  @override
  String get authFeatureProgressTitle => 'Progress tracking';

  @override
  String get authFeatureProgressBody =>
      'How your score and measurements change over time.';

  @override
  String passwordRuleLength(int min) {
    return 'At least $min characters';
  }

  @override
  String get passwordRuleLetter => 'One letter';

  @override
  String get passwordRuleDigit => 'One digit';

  @override
  String get passwordRuleMet => 'met';

  @override
  String get passwordRuleUnmet => 'not met';

  @override
  String get resetTitle => 'Reset password';

  @override
  String get resetIntro =>
      'Enter your account\'s e-mail address and we\'ll send you a 6-digit code.';

  @override
  String resetCodeSentBody(String email) {
    return 'If an account exists for $email, we sent a code. Enter it with your new password.';
  }

  @override
  String get resetSendCode => 'Send code';

  @override
  String get resetCode => 'Verification code';

  @override
  String get resetNewPassword => 'New password';

  @override
  String get resetSetPassword => 'Change password';

  @override
  String get resetResend => 'Resend code';

  @override
  String resetResendIn(int seconds) {
    return 'You can resend in ${seconds}s';
  }

  @override
  String get resetSuccess =>
      'Your password was changed. You can sign in with your new password.';

  @override
  String get verifyTitle => 'Verify your e-mail';

  @override
  String verifyBody(String email) {
    return 'Enter the 6-digit code we sent to $email.';
  }

  @override
  String get verifyAction => 'Verify';

  @override
  String get verifyResend => 'Send a new code';

  @override
  String get verifyCodeSent => 'A new code was sent to your e-mail.';

  @override
  String get verifySuccess => 'Your e-mail is verified.';

  @override
  String get legalTermsTitle => 'Terms of Use';

  @override
  String get legalPrivacyTitle => 'Privacy Policy';

  @override
  String get navHome => 'Home';

  @override
  String get navProgram => 'Plan';

  @override
  String get navProgress => 'Progress';

  @override
  String get navHistory => 'History';

  @override
  String get navProfile => 'Profile';

  @override
  String unitSeconds(int seconds) {
    return '${seconds}s';
  }

  @override
  String recordTitle(String exercise) {
    return 'Record $exercise';
  }

  @override
  String get recordSwitchCamera => 'Switch camera';

  @override
  String get recordFramingHint =>
      'Prop up your phone, step back 2-3 meters and make sure your whole body is in the frame.';

  @override
  String get recordGetReady => 'Get ready…';

  @override
  String get recordRecordingHint =>
      'Move with control. Tap stop when you\'re done; up to 60 seconds are recorded.';

  @override
  String get recordGo => 'Go';

  @override
  String get recordStart => 'Start recording';

  @override
  String get recordStop => 'Stop recording';

  @override
  String get recordCameraError =>
      'Couldn\'t access the camera. Check camera permission and try again, or upload a video instead.';

  @override
  String get progressTitle => 'Analysis';

  @override
  String get progressUploading => 'Uploading video';

  @override
  String get progressQueued => 'Waiting to be analyzed';

  @override
  String get progressProcessing => 'Analyzing your movement';

  @override
  String progressVideoSize(String size) {
    return '$size MB video';
  }

  @override
  String get progressLeaveHint =>
      'You can leave this screen; the result will appear in History when it\'s ready.';

  @override
  String get progressFailedTitle => 'Analysis couldn\'t be completed';

  @override
  String voiceResultSummary(int score, int reps, String issue) {
    return 'Analysis complete. Your score is $score. $reps reps. $issue';
  }

  @override
  String get scoreExcellent => 'Excellent';

  @override
  String get scoreGood => 'Good';

  @override
  String get scoreFair => 'Fair';

  @override
  String get scoreNeedsWork => 'Needs work';

  @override
  String get resultScoreCaption => 'form score';

  @override
  String get resultNotScored => 'Not scored';

  @override
  String get resultNotScoredBody =>
      'No completed repetition was found in the video, so it wasn\'t scored. Complete the movement fully at least once and try again.';

  @override
  String get resultReps => 'Reps';

  @override
  String get resultDuration => 'Duration';

  @override
  String get resultConfidence => 'Detection';

  @override
  String resultValidRepsNote(int valid, int total) {
    return '$valid of $total reps were completed with good form.';
  }

  @override
  String get resultSummaryClean => 'No clear form issues found. Great work!';

  @override
  String resultSummaryIssues(int count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: 'There are $count things to improve.',
      one: 'There is 1 thing to improve.',
    );
    return '$_temp0';
  }

  @override
  String get resultDepthTitle => 'Depth';

  @override
  String get resultAvgKneeAngle => 'Average lowest knee angle';

  @override
  String get resultAvgKneeAngleHelp =>
      'Lower means deeper; around 90° is a common target.';

  @override
  String get resultRangeOfMotion => 'Range of motion';

  @override
  String get resultRangeOfMotionHelp =>
      'Difference between your knee\'s most open and most bent position.';

  @override
  String get resultIssuesTitle => 'What to improve';

  @override
  String get resultTipsTitle => 'Tips';

  @override
  String get resultNewAnalysis => 'New analysis';

  @override
  String get resultDisclaimer =>
      'This assessment is generated by AI and isn\'t medical advice. Stop if you feel pain.';

  @override
  String get homeTitle => 'Home';

  @override
  String homeGreeting(String name) {
    return 'Hi, $name';
  }

  @override
  String get homeVerifyEmail =>
      'Verify your e-mail; it\'s how you\'ll recover your account if you forget your password.';

  @override
  String get homeNewAnalysis => 'New analysis';

  @override
  String get homeNewAnalysisBody =>
      'Choose the exercise, then upload a video or record one.';

  @override
  String get homeUploadVideo => 'Upload video';

  @override
  String get homeRecordVideo => 'Record';

  @override
  String get homeCaptureTip =>
      'For best results, keep your whole body in frame and the room well lit.';

  @override
  String get homeSummary => 'Summary';

  @override
  String get homeThisWeek => 'This week';

  @override
  String get homeAverageScore => 'Average';

  @override
  String get homeBestScore => 'Best';

  @override
  String get homeLatest => 'Latest analysis';

  @override
  String get homeEmptyTitle => 'No analyses yet';

  @override
  String get homeEmptyBody =>
      'Your results will appear here after your first analysis.';

  @override
  String get homeToday => 'Today\'s plan';

  @override
  String get homeLibrary => 'Exercises';

  @override
  String get homeAiAnalysis => 'AI analysis';

  @override
  String get historyTitle => 'History';

  @override
  String historyCount(int count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: '$count analyses',
      one: '1 analysis',
    );
    return '$_temp0';
  }

  @override
  String historyReps(int count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: '$count reps',
      one: '1 rep',
    );
    return '$_temp0';
  }

  @override
  String get historyAll => 'All';

  @override
  String get historyErrorTitle => 'Couldn\'t load history';

  @override
  String get historyNoMatch => 'No analyses for this exercise';

  @override
  String get historyNoMatchBody => 'Choose another filter.';

  @override
  String get detailFavorite => 'Add to favorites';

  @override
  String get detailUnfavorite => 'Remove from favorites';

  @override
  String get detailComingSoonBody =>
      'AI analysis isn\'t available for this exercise yet. Squats and push-ups can be analyzed today.';

  @override
  String get detailMuscles => 'Target muscles';

  @override
  String get detailMistakes => 'Common mistakes';

  @override
  String get progressPageTitle => 'Progress';

  @override
  String get progressPageSubtitle =>
      'Track your form score, weight and measurements.';

  @override
  String get progressLocalNote =>
      'Weight and measurements are stored only on this device.';

  @override
  String get progressScoreTitle => 'Form score';

  @override
  String get progressScoreEmptyTitle =>
      'At least 2 analyses needed for a trend';

  @override
  String get progressScoreEmptyBody =>
      'As you do more analyses, you\'ll see how your form score changes here.';

  @override
  String get progressWeightTitle => 'Weight';

  @override
  String get progressGoalAndHeight => 'Goal and height';

  @override
  String get progressWeightEmptyTitle => 'Log your weight';

  @override
  String get progressWeightEmptyBody =>
      'Log your weight regularly to see how it changes over time.';

  @override
  String get progressAddWeight => 'Log weight';

  @override
  String progressGoal(String target) {
    return 'Goal: $target kg';
  }

  @override
  String get progressHeight => 'Height';

  @override
  String get progressTargetWeight => 'Target weight';

  @override
  String progressRangeError(String min, String max, String unit) {
    return 'Enter a value between $min and $max $unit.';
  }

  @override
  String get progressMeasurementsTitle => 'Body measurements';

  @override
  String get progressMeasurementsEmptyTitle => 'No measurements yet';

  @override
  String get progressMeasurementsEmptyBody =>
      'Add measurements like waist and hips to track how they change.';

  @override
  String get progressAddMeasurement => 'Add measurement';

  @override
  String progressMeasurementFrom(String value) {
    return 'Started at $value cm';
  }

  @override
  String get measureWaist => 'Waist';

  @override
  String get measureHip => 'Hips';

  @override
  String get measureChest => 'Chest';

  @override
  String get measureArm => 'Arm';

  @override
  String get measureThigh => 'Thigh';

  @override
  String get bmiTitle => 'Body mass index';

  @override
  String get bmiUnder => 'Underweight';

  @override
  String get bmiNormal => 'Normal';

  @override
  String get bmiOver => 'Overweight';

  @override
  String get bmiObese => 'Obese';

  @override
  String get bmiNote => 'BMI doesn\'t account for muscle mass.';

  @override
  String get programTitle => 'Plan';

  @override
  String get programSubtitle =>
      'Your weekly beginner plan. Tick off the days you complete.';

  @override
  String get programThisWeek => 'This week';

  @override
  String programDaysDone(int done, int total) {
    return '$done/$total days';
  }

  @override
  String get programToday => 'Today';

  @override
  String get programMarkDone => 'Mark day as done';

  @override
  String get programAnalyze => 'Record and analyze';

  @override
  String get programRestDayBody =>
      'Rest day. A light walk or some stretching is fine.';

  @override
  String get profileTitle => 'Profile';

  @override
  String get profileAnalyses => 'Analyses';

  @override
  String get profileAchievements => 'Achievements';

  @override
  String get profileFavorites => 'Favorite exercises';

  @override
  String get profileVerified => 'Verified';

  @override
  String get profileNotVerified => 'Not verified';

  @override
  String get achievementUnlocked => 'unlocked';

  @override
  String get achievementLocked => 'locked';

  @override
  String get achievementFirstTitle => 'First step';

  @override
  String get achievementFirstBody => 'Complete your first analysis.';

  @override
  String get achievementTenTitle => 'Committed';

  @override
  String achievementTenBody(int count) {
    return 'Complete 10 analyses ($count/10).';
  }

  @override
  String get achievementNinetyTitle => 'Near perfect';

  @override
  String get achievementNinetyBody => 'Score 90 or more in an analysis.';

  @override
  String get achievementCleanTitle => 'Clean form';

  @override
  String get achievementCleanBody => 'Finish a set with no form issues.';

  @override
  String get achievementBothTitle => 'All-rounder';

  @override
  String get achievementBothBody => 'Analyze both squats and push-ups.';

  @override
  String get achievementStreakTitle => 'Weekly streak';

  @override
  String achievementStreakBody(int count) {
    return 'Analyze on 3 different days in a week ($count/3).';
  }

  @override
  String get settingsTitle => 'Settings';

  @override
  String get settingsAppearance => 'Appearance';

  @override
  String get settingsThemeSystem => 'System';

  @override
  String get settingsThemeLight => 'Light';

  @override
  String get settingsThemeDark => 'Dark';

  @override
  String get settingsLanguage => 'Language';

  @override
  String get settingsVoice => 'Sound';

  @override
  String get settingsVoiceTitle => 'Voice guidance';

  @override
  String get settingsVoiceBody =>
      'Reads the recording countdown and your result aloud.';

  @override
  String get settingsAccount => 'Account';

  @override
  String get settingsSignOut => 'Sign out';

  @override
  String get settingsSignOutBody => 'You\'ll be signed out on this device.';

  @override
  String get settingsSignOutAll => 'Sign out of all devices';

  @override
  String get settingsSignOutAllBody =>
      'You\'ll be signed out on every device where your account is open.';

  @override
  String get settingsDeleteTitle => 'Delete account';

  @override
  String get settingsDeleteBody =>
      'Your account, all uploaded videos and analysis results will be permanently deleted. This can\'t be undone.';

  @override
  String get settingsDeleteAction => 'Delete permanently';

  @override
  String get settingsDeleted => 'Your account and all its data were deleted.';

  @override
  String get settingsLegal => 'Legal';

  @override
  String settingsVersion(String version) {
    return 'AIT version $version';
  }

  @override
  String get legalKvkkTitle => 'KVKK Privacy Notice';

  @override
  String legalLastUpdated(String date) {
    return 'Last updated: $date';
  }
}
