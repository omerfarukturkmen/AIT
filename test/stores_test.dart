import 'package:flutter_application_1/core/state/auth_store.dart';
import 'package:flutter_application_1/core/state/body_progress_store.dart';
import 'package:flutter_application_1/core/state/favorite_exercises_store.dart';
import 'package:flutter_application_1/core/state/workout_program_store.dart';
import 'package:flutter_application_1/data/exercise_catalog.dart';
import 'package:flutter_application_1/features/profile/achievements.dart';
import 'package:flutter_application_1/models/auth_session_model.dart';
import 'package:flutter_application_1/models/body_progress_model.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'helpers.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
    signInForTest();
  });
  tearDown(() => AuthStore.session.value = null);

  test(
    'body data persists per user and is not shared between accounts',
    () async {
      await BodyProgressStore.addWeight(72, date: DateTime(2026, 9, 1));
      await BodyProgressStore.addWeight(70, date: DateTime(2026, 10, 1));
      await BodyProgressStore.setProfile(heightCm: 170, targetWeightKg: 66);

      BodyProgressStore.clear();
      await BodyProgressStore.load();
      expect(BodyProgressStore.progress.value.currentWeight, 70);

      AuthStore.session.value = const AuthSession(
        accessToken: 't2',
        user: AuthUser(id: 99, email: 'b@example.com', fullName: 'Başka Kişi'),
      );
      await BodyProgressStore.load();
      expect(BodyProgressStore.progress.value.hasData, isFalse);
    },
  );

  test('body progress math', () {
    final body = BodyProgress(
      heightCm: 170,
      targetWeightKg: 66,
      weights: [
        WeightEntry(date: DateTime(2026, 9, 1), kg: 72),
        WeightEntry(date: DateTime(2026, 10, 1), kg: 69),
      ],
    );
    expect(body.weightChange, -3);
    expect(body.goalProgress, closeTo(0.5, 0.001));
    expect(body.bmi, closeTo(23.9, 0.05));
    expect(BodyProgress.empty.bmi, isNull);
    expect(BodyProgress.empty.goalProgress, isNull);
  });

  test('favorites persist', () async {
    await FavoriteExercisesStore.toggle(ExerciseId.squat);
    FavoriteExercisesStore.clear();
    await FavoriteExercisesStore.load();
    expect(FavoriteExercisesStore.favorites.value, {ExerciseId.squat});
  });

  test('program completion is stored for the current week only', () async {
    await WorkoutProgramStore.toggle(DateTime.monday);
    expect(WorkoutProgramStore.isCompleted(DateTime.monday), isTrue);
    expect(WorkoutProgramStore.completedThisWeek(), 1);

    WorkoutProgramStore.clear();
    await WorkoutProgramStore.load();
    expect(WorkoutProgramStore.isCompleted(DateTime.monday), isTrue);

    await WorkoutProgramStore.toggle(DateTime.monday);
    expect(WorkoutProgramStore.completedThisWeek(), 0);
  });

  test('achievements come from real results', () {
    expect(achievementsFor(trL10n, []).where((a) => a.unlocked), isEmpty);

    final now = DateTime(2026, 10, 26, 12);
    final results = [
      sampleResult(id: 1, score: 93, issues: const [], createdAt: now),
      sampleResult(
        id: 2,
        exercise: ExerciseId.pushUp,
        createdAt: now.subtract(const Duration(days: 1)),
      ),
      sampleResult(id: 3, createdAt: now.subtract(const Duration(days: 3))),
    ];
    final unlocked = achievementsFor(
      trL10n,
      results,
      now: now,
    ).where((a) => a.unlocked).map((a) => a.title).toSet();

    expect(unlocked, {
      trL10n.achievementFirstTitle,
      trL10n.achievementNinetyTitle,
      trL10n.achievementCleanTitle,
      trL10n.achievementBothTitle,
      trL10n.achievementStreakTitle,
    });
  });
}
