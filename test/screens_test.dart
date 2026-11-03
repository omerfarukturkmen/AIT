import 'package:flutter/material.dart';
import 'package:flutter_application_1/core/state/analysis_history_store.dart';
import 'package:flutter_application_1/core/state/app_settings_store.dart';
import 'package:flutter_application_1/core/state/auth_store.dart';
import 'package:flutter_application_1/core/state/body_progress_store.dart';
import 'package:flutter_application_1/core/state/navigation_store.dart';
import 'package:flutter_application_1/data/exercise_catalog.dart';
import 'package:flutter_application_1/features/exercise_detail/exercise_detail_page.dart';
import 'package:flutter_application_1/features/legal/legal_page.dart';
import 'package:flutter_application_1/features/navigation/main_navigation_page.dart';
import 'package:flutter_application_1/features/onboarding/onboarding_page.dart';
import 'package:flutter_application_1/features/result/result_page.dart';
import 'package:flutter_application_1/features/settings/settings_page.dart';
import 'package:flutter_application_1/l10n/form_issues.dart';
import 'package:flutter_application_1/models/analysis_result_model.dart';
import 'package:flutter_application_1/widgets/common.dart';
import 'package:flutter_application_1/models/body_progress_model.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'helpers.dart';

const _sizes = {
  'phone': Size(360, 780),
  'tablet': Size(820, 1180),
  'desktop': Size(1440, 900),
};

void main() {
  setUp(() {
    SharedPreferences.setMockInitialValues({});
    FlutterSecureStorage.setMockInitialValues({});
    NavigationStore.go(AppTab.home);
    signInForTest();
    AnalysisHistoryStore.results.value = [
      sampleResult(
        id: 3,
        score: 92,
        issues: const [],
        createdAt: DateTime.now(),
      ),
      sampleResult(
        id: 2,
        score: 74,
        exercise: ExerciseId.pushUp,
        issues: const ['elbows_flared'],
      ),
      sampleResult(id: 1, score: 61, createdAt: DateTime(2026, 10, 1)),
    ];
    AnalysisHistoryStore.status.value = HistoryStatus.ready;
    BodyProgressStore.progress.value = BodyProgress(
      heightCm: 168,
      targetWeightKg: 62,
      weights: [
        WeightEntry(date: DateTime(2026, 9, 1), kg: 72),
        WeightEntry(date: DateTime(2026, 10, 1), kg: 69.5),
      ],
      measurements: [
        MeasurementEntry(
          date: DateTime(2026, 9, 1),
          type: MeasurementType.waist,
          cm: 82,
        ),
        MeasurementEntry(
          date: DateTime(2026, 10, 1),
          type: MeasurementType.waist,
          cm: 78,
        ),
      ],
    );
  });

  tearDown(() {
    AuthStore.session.value = null;
    AnalysisHistoryStore.clearHistory();
    BodyProgressStore.clear();
  });

  for (final MapEntry(key: name, value: size) in _sizes.entries) {
    for (final (locale, theme) in [
      (const Locale('tr'), ThemeMode.light),
      (const Locale('en'), ThemeMode.dark),
    ]) {
      testWidgets(
        'all tabs render on $name (${locale.languageCode}, ${theme.name})',
        (tester) async {
          setScreenSize(tester, size);
          final l10n = locale.languageCode == 'tr' ? trL10n : enL10n;
          await tester.pumpWidget(
            wrapApp(
              const MainNavigationPage(),
              locale: locale,
              themeMode: theme,
            ),
          );
          await tester.pumpAndSettle();

          expect(find.text(l10n.homeGreeting('Ayşe')), findsOneWidget);
          expect(find.text(l10n.homeNewAnalysis), findsOneWidget);
          expect(tester.takeException(), isNull);

          for (final tab in AppTab.values.skip(1)) {
            NavigationStore.go(tab);
            await tester.pumpAndSettle();
            expect(tester.takeException(), isNull, reason: '$tab');
          }

          NavigationStore.go(AppTab.history);
          await tester.pumpAndSettle();
          expect(find.text(l10n.historyCount(3)), findsOneWidget);

          NavigationStore.go(AppTab.profile);
          await tester.pumpAndSettle();
          expect(find.text('Ayşe Yılmaz'), findsOneWidget);
        },
      );
    }
  }

  testWidgets('wide screens use a navigation rail, phones a bottom bar', (
    tester,
  ) async {
    setScreenSize(tester, _sizes['desktop']!);
    await tester.pumpWidget(wrapApp(const MainNavigationPage()));
    await tester.pumpAndSettle();
    expect(find.byType(NavigationRail), findsOneWidget);

    setScreenSize(tester, _sizes['phone']!);
    await tester.pumpAndSettle();
    expect(find.byType(NavigationBar), findsOneWidget);
  });

  testWidgets('unverified users see the verification banner', (tester) async {
    signInForTest(emailVerified: false);
    setScreenSize(tester, _sizes['phone']!);
    await tester.pumpWidget(wrapApp(const MainNavigationPage()));
    await tester.pumpAndSettle();
    expect(find.text(trL10n.homeVerifyEmail), findsOneWidget);
  });

  testWidgets('empty history shows a helpful empty state', (tester) async {
    AnalysisHistoryStore.results.value = [];
    setScreenSize(tester, _sizes['phone']!);
    await tester.pumpWidget(wrapApp(const MainNavigationPage()));
    await tester.pumpAndSettle();
    expect(find.text(trL10n.homeEmptyTitle), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('result page shows the real date, issues and how to fix them', (
    tester,
  ) async {
    setScreenSize(tester, _sizes['phone']!);
    final result = sampleResult(
      issues: const ['insufficient_depth', 'too_fast'],
    );
    await tester.pumpWidget(wrapApp(ResultPage(result: result)));
    await tester.pumpAndSettle();

    final depth = formIssue(trL10n, 'insufficient_depth');
    expect(find.text(depth.title), findsOneWidget);
    expect(find.text(depth.fix), findsOneWidget);
    expect(find.textContaining('20 Eki 2026'), findsOneWidget);
    expect(find.text(trL10n.resultSummaryIssues(2)), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('a clean result says there were no issues', (tester) async {
    setScreenSize(tester, _sizes['phone']!);
    await tester.pumpWidget(
      wrapApp(
        ResultPage(result: sampleResult(issues: const [])),
        locale: const Locale('en'),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text(enL10n.issueNoneTitle), findsOneWidget);
  });

  testWidgets('a video without a finished rep says it was not scored', (
    tester,
  ) async {
    setScreenSize(tester, _sizes['phone']!);
    final result = AnalysisResult.fromPayload(
      resultPayload(score: 0, reps: 0, errors: ['no_completed_reps']),
    );
    await tester.pumpWidget(
      wrapApp(ResultPage(result: result), locale: const Locale('en')),
    );
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('result_not_scored')), findsOneWidget);
    expect(find.byType(ScoreRing), findsNothing);
    expect(find.text(enL10n.issueNoReps), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets("recording warnings are shown in the user's language", (
    tester,
  ) async {
    setScreenSize(tester, _sizes['phone']!);
    final result = AnalysisResult.fromPayload(
      resultPayload(warningCodes: ['low_frame_rate', 'unknown_code']),
    );
    await tester.pumpWidget(
      wrapApp(ResultPage(result: result), locale: const Locale('en')),
    );
    await tester.pumpAndSettle();
    expect(find.text(enL10n.warningTitle), findsOneWidget);
    expect(find.text(enL10n.warningLowFrameRate), findsOneWidget);
    expect(find.text('unknown_code'), findsNothing);
  });

  testWidgets('unsupported exercises say "coming soon" and offer no analysis', (
    tester,
  ) async {
    setScreenSize(tester, _sizes['phone']!);
    await tester.pumpWidget(
      wrapApp(const ExerciseDetailPage(exercise: ExerciseId.plank)),
    );
    await tester.pumpAndSettle();
    expect(find.text(trL10n.detailComingSoonBody), findsOneWidget);
    expect(find.text(trL10n.homeRecordVideo), findsNothing);
  });

  testWidgets('settings change language and theme', (tester) async {
    setScreenSize(tester, _sizes['phone']!);
    await tester.pumpWidget(wrapApp(const SettingsPage()));
    await tester.pumpAndSettle();

    await tester.tap(find.text('English'));
    await tester.pumpAndSettle();
    expect(AppSettingsStore.settings.value.languageCode, 'en');

    await tester.tap(find.text(trL10n.settingsThemeDark));
    await tester.pumpAndSettle();
    expect(AppSettingsStore.settings.value.themeMode, ThemeMode.dark);
    expect(tester.takeException(), isNull);
  });

  for (final document in LegalDocument.values) {
    testWidgets('legal page ${document.name} has text in both languages', (
      tester,
    ) async {
      for (final locale in const [Locale('tr'), Locale('en')]) {
        await tester.pumpWidget(
          wrapApp(LegalPage(document: document), locale: locale),
        );
        await tester.pumpAndSettle();
        expect(document.sections(locale.languageCode).length, greaterThan(3));
        expect(tester.takeException(), isNull);
      }
    });
  }

  testWidgets('onboarding pages render on a small phone', (tester) async {
    setScreenSize(tester, const Size(320, 640));
    await tester.pumpWidget(wrapApp(const OnboardingPage()));
    await tester.pumpAndSettle();
    expect(find.text(trL10n.onboardingCaptureTitle), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
