import 'package:flutter/foundation.dart';

class FavoriteExercisesStore {
  static final ValueNotifier<Set<String>> favorites =
      ValueNotifier<Set<String>>({});

  static bool isFavorite(String exerciseName) {
    return favorites.value.contains(exerciseName);
  }

  static void toggleFavorite(String exerciseName) {
    final updatedFavorites = Set<String>.from(favorites.value);

    if (updatedFavorites.contains(exerciseName)) {
      updatedFavorites.remove(exerciseName);
    } else {
      updatedFavorites.add(exerciseName);
    }

    favorites.value = updatedFavorites;
  }

  static void removeFavorite(String exerciseName) {
    final updatedFavorites = Set<String>.from(favorites.value);
    updatedFavorites.remove(exerciseName);
    favorites.value = updatedFavorites;
  }

  static void clearFavorites() {
    favorites.value = {};
  }
}