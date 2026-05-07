import 'package:flutter/foundation.dart';

import '../../models/body_progress_model.dart';

class BodyProgressStore {
  static final ValueNotifier<BodyProgress> progress =
      ValueNotifier<BodyProgress>(
        const BodyProgress(
          startWeight: 72.0,
          currentWeight: 67.5,
          targetWeight: 62.0,
          heightCm: 168,
          weeklyWeights: [
            WeightEntry(weekLabel: '1. Hafta', weight: 72.0),
            WeightEntry(weekLabel: '2. Hafta', weight: 71.2),
            WeightEntry(weekLabel: '3. Hafta', weight: 70.4),
            WeightEntry(weekLabel: '4. Hafta', weight: 69.1),
            WeightEntry(weekLabel: '5. Hafta', weight: 68.3),
            WeightEntry(weekLabel: '6. Hafta', weight: 67.5),
          ],
          measurements: [
            BodyMeasurement(
              title: 'Bel',
              startValue: 82,
              currentValue: 76,
              unit: 'cm',
            ),
            BodyMeasurement(
              title: 'Kalça',
              startValue: 102,
              currentValue: 98,
              unit: 'cm',
            ),
            BodyMeasurement(
              title: 'Göğüs',
              startValue: 94,
              currentValue: 91,
              unit: 'cm',
            ),
            BodyMeasurement(
              title: 'Kol',
              startValue: 31,
              currentValue: 30,
              unit: 'cm',
            ),
            BodyMeasurement(
              title: 'Bacak',
              startValue: 58,
              currentValue: 55,
              unit: 'cm',
            ),
          ],
        ),
      );
}
