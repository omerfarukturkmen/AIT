import 'package:flutter/foundation.dart';

import '../../models/body_progress_model.dart';
import 'user_storage.dart';

/// Body measurements the user enters; stored on the device per user.
class BodyProgressStore {
  static const _storageName = 'body';

  static final ValueNotifier<BodyProgress> progress = ValueNotifier(
    BodyProgress.empty,
  );

  static Future<void> load() async {
    progress.value = BodyProgress.fromJson(
      await UserStorage.readJson(_storageName),
    );
  }

  static Future<void> _save(BodyProgress next) async {
    progress.value = next;
    await UserStorage.writeJson(_storageName, next.toJson());
  }

  static Future<void> addWeight(double kg, {DateTime? date}) {
    final entry = WeightEntry(date: date ?? DateTime.now(), kg: kg);
    final weights = [...progress.value.weights, entry]
      ..sort((a, b) => a.date.compareTo(b.date));
    return _save(progress.value.copyWith(weights: weights));
  }

  static Future<void> removeWeight(WeightEntry entry) {
    return _save(
      progress.value.copyWith(
        weights: progress.value.weights.where((w) => w != entry).toList(),
      ),
    );
  }

  static Future<void> addMeasurement(MeasurementType type, double cm) {
    final entry = MeasurementEntry(date: DateTime.now(), type: type, cm: cm);
    return _save(
      progress.value.copyWith(
        measurements: [...progress.value.measurements, entry],
      ),
    );
  }

  static Future<void> setProfile({
    double? heightCm,
    double? targetWeightKg,
    Sex? sex,
    int? birthYear,
  }) {
    return _save(
      progress.value.copyWith(
        heightCm: heightCm,
        targetWeightKg: targetWeightKg,
        sex: sex,
        birthYear: birthYear,
      ),
    );
  }

  static void clear() => progress.value = BodyProgress.empty;
}
