import 'package:flutter/foundation.dart';

import 'user_storage.dart';

/// Days of the current week the user marked as done. Stored per user and
/// per week, so a new week starts empty.
class WorkoutProgramStore {
  static const _storageName = 'program.completed';

  /// Entries look like "2026-10-26:1" (week start date : ISO weekday).
  static final ValueNotifier<Set<String>> _completed = ValueNotifier({});

  static ValueListenable<Set<String>> get completed => _completed;

  static DateTime _weekStart(DateTime now) {
    final day = DateTime(now.year, now.month, now.day);
    return day.subtract(Duration(days: day.weekday - 1));
  }

  static String _entry(int weekday, [DateTime? now]) {
    final start = _weekStart(now ?? DateTime.now());
    final date =
        '${start.year}-${start.month.toString().padLeft(2, '0')}-${start.day.toString().padLeft(2, '0')}';
    return '$date:$weekday';
  }

  static bool isCompleted(int weekday) =>
      _completed.value.contains(_entry(weekday));

  static int completedThisWeek() {
    final prefix = _entry(1).split(':').first;
    return _completed.value.where((e) => e.startsWith(prefix)).length;
  }

  static Future<void> toggle(int weekday) async {
    final entry = _entry(weekday);
    final next = Set<String>.from(_completed.value);
    if (!next.remove(entry)) next.add(entry);
    _completed.value = next;
    await UserStorage.writeJson(_storageName, next.toList());
  }

  static Future<void> load() async {
    final stored = await UserStorage.readJson(_storageName);
    _completed.value = stored is List ? stored.whereType<String>().toSet() : {};
  }

  static void clear() => _completed.value = {};
}
