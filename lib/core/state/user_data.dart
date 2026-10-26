import 'analysis_history_store.dart';
import 'body_progress_store.dart';
import 'favorite_exercises_store.dart';
import 'user_storage.dart';
import 'workout_program_store.dart';

/// Loads and clears everything that belongs to the signed-in user.
class UserData {
  static Future<void> loadForCurrentUser() async {
    await Future.wait([
      FavoriteExercisesStore.load(),
      WorkoutProgramStore.load(),
      BodyProgressStore.load(),
    ]);
    // History comes from the server; don't block app start on it.
    AnalysisHistoryStore.refresh();
  }

  /// Forget in-memory data (sign-out). Stored data stays for next sign-in.
  static void clearInMemory() {
    AnalysisHistoryStore.clearHistory();
    FavoriteExercisesStore.clear();
    WorkoutProgramStore.clear();
    BodyProgressStore.clear();
  }

  /// Account deletion: also remove what is stored on this device.
  static Future<void> deleteForCurrentUser() async {
    await UserStorage.clearCurrentUser();
    clearInMemory();
  }
}
