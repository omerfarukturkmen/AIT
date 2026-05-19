class WeightEntry {
  final String weekLabel;
  final double weight;

  const WeightEntry({required this.weekLabel, required this.weight});
}

class BodyMeasurement {
  final String title;
  final double startValue;
  final double currentValue;
  final String unit;

  const BodyMeasurement({
    required this.title,
    required this.startValue,
    required this.currentValue,
    required this.unit,
  });

  double get difference => currentValue - startValue;
}

class BodyProgress {
  final double startWeight;
  final double currentWeight;
  final double targetWeight;
  final double heightCm;
  final List<WeightEntry> weeklyWeights;
  final List<BodyMeasurement> measurements;

  const BodyProgress({
    required this.startWeight,
    required this.currentWeight,
    required this.targetWeight,
    required this.heightCm,
    required this.weeklyWeights,
    required this.measurements,
  });

  double get lostWeight => startWeight - currentWeight;

  double get remainingWeight => currentWeight - targetWeight;

  double get progressRatio {
    final totalTarget = startWeight - targetWeight;

    if (totalTarget <= 0) return 0;

    final ratio = lostWeight / totalTarget;

    if (ratio < 0) return 0;
    if (ratio > 1) return 1;

    return ratio;
  }

  double get bmi {
    final heightMeter = heightCm / 100;
    return currentWeight / (heightMeter * heightMeter);
  }

  String get bmiStatus {
    if (bmi < 18.5) return 'Düşük kilo';
    if (bmi < 25) return 'Normal';
    if (bmi < 30) return 'Fazla kilo';
    return 'Obezite riski';
  }
}
