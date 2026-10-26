import 'package:flutter/foundation.dart';

import '../../data/exercise_catalog.dart';
import 'user_storage.dart';

class FavoriteExercisesStore {
  static const _storageName = 'favorites';

  static final ValueNotifier<Set<ExerciseId>> favorites = ValueNotifier({});

  static bool isFavorite(ExerciseId exercise) =>
      favorites.value.contains(exercise);

  static Future<void> toggle(ExerciseId exercise) async {
    final next = Set<ExerciseId>.from(favorites.value);
    if (!next.remove(exercise)) next.add(exercise);
    favorites.value = next;
    await UserStorage.writeJson(_storageName, next.map((e) => e.name).toList());
  }

  static Future<void> load() async {
    final stored = await UserStorage.readJson(_storageName);
    favorites.value = {
      if (stored is List)
        for (final name in stored.whereType<String>()) ?exerciseFromName(name),
    };
  }

  static void clear() => favorites.value = {};
}
