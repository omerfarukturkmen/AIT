import 'package:flutter/material.dart';
import 'package:flutter_application_1/core/state/auth_store.dart';
import 'package:flutter_application_1/core/theme/app_theme.dart';
import 'package:flutter_application_1/data/exercise_catalog.dart';
import 'package:flutter_application_1/l10n/app_localizations.dart';
import 'package:flutter_application_1/models/analysis_result_model.dart';
import 'package:flutter_application_1/models/auth_session_model.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

final AppLocalizations trL10n = lookupAppLocalizations(const Locale('tr'));
final AppLocalizations enL10n = lookupAppLocalizations(const Locale('en'));

/// Wraps [child] in a MaterialApp with the app's themes and localizations.
Widget wrapApp(
  Widget child, {
  Locale locale = const Locale('tr'),
  ThemeMode themeMode = ThemeMode.light,
}) {
  return MaterialApp(
    theme: AppTheme.light(),
    darkTheme: AppTheme.dark(),
    themeMode: themeMode,
    locale: locale,
    supportedLocales: AppLocalizations.supportedLocales,
    localizationsDelegates: const [
      AppLocalizations.delegate,
      GlobalMaterialLocalizations.delegate,
      GlobalWidgetsLocalizations.delegate,
      GlobalCupertinoLocalizations.delegate,
    ],
    home: child,
  );
}

void setScreenSize(WidgetTester tester, Size size) {
  tester.view.physicalSize = size;
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.reset);
}

const testUser = AuthUser(
  id: 7,
  email: 'ayse@example.com',
  fullName: 'Ayşe Yılmaz',
  emailVerified: true,
);

void signInForTest({bool emailVerified = true}) {
  AuthStore.session.value = AuthSession(
    accessToken: 'test-token',
    user: testUser.copyWith(emailVerified: emailVerified),
  );
}

AnalysisResult sampleResult({
  int id = 1,
  int score = 82,
  ExerciseId exercise = ExerciseId.squat,
  List<String> issues = const ['insufficient_depth'],
  DateTime? createdAt,
}) {
  return AnalysisResult(
    id: id,
    createdAt: createdAt ?? DateTime(2026, 10, 20, 9, 30),
    exercise: exercise,
    score: score,
    repetitionCount: 10,
    validReps: 8,
    invalidReps: 2,
    confidencePercent: 91,
    durationSeconds: 38,
    minKneeAngle: 78,
    averageMinKneeAngle: 84,
    kneeRangeOfMotion: 92,
    issueCodes: issues,
  );
}

/// Completed-analysis payload as returned by GET /analysis/{id}.
Map<String, dynamic> resultPayload({
  int analysisId = 5,
  int score = 90,
  int reps = 2,
  List<String> errors = const [],
  List<String> warningCodes = const [],
  String exerciseType = 'squat',
}) {
  return {
    'status': 'success',
    'score': score,
    'repetition_count': reps,
    'data': {
      'analysis_id': analysisId,
      'exercise_type': exerciseType,
      'exercise_name': 'Squat',
      'score': score,
      'repetition_count': reps,
      'valid_reps': reps,
      'invalid_reps': 0,
      'total_frames': 332,
      'processed_frames': 320,
      'confidence_percent': 88.7,
      'duration_seconds': 11.08,
      'average_min_knee_angle': 78.5,
      'min_knee_angle': 76.0,
      'knee_range_of_motion': 85.0,
      'errors': errors,
      'warning_codes': warningCodes,
      'created_at': '2026-10-26T08:15:00',
      'details': {'total_frames': 332},
    },
  };
}
