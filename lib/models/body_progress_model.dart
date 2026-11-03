/// Biological sex, used only for sex-specific body-composition estimates.
enum Sex { female, male }

/// Body-fat bands (American Council on Exercise).
enum BodyFatBand { essential, athletic, fitness, average, high }

/// Body measurement types the user can track (all in cm).
enum MeasurementType { waist, hip, chest, arm, thigh }

class WeightEntry {
  final DateTime date;
  final double kg;

  const WeightEntry({required this.date, required this.kg});

  Map<String, Object> toJson() => {'date': date.toIso8601String(), 'kg': kg};

  static WeightEntry? fromJson(Object? json) {
    if (json is! Map) return null;
    final date = DateTime.tryParse('${json['date']}');
    final kg = json['kg'];
    if (date == null || kg is! num) return null;
    return WeightEntry(date: date, kg: kg.toDouble());
  }
}

class MeasurementEntry {
  final DateTime date;
  final MeasurementType type;
  final double cm;

  const MeasurementEntry({
    required this.date,
    required this.type,
    required this.cm,
  });

  Map<String, Object> toJson() => {
    'date': date.toIso8601String(),
    'type': type.name,
    'cm': cm,
  };

  static MeasurementEntry? fromJson(Object? json) {
    if (json is! Map) return null;
    final date = DateTime.tryParse('${json['date']}');
    final type = MeasurementType.values
        .where((t) => t.name == json['type'])
        .firstOrNull;
    final cm = json['cm'];
    if (date == null || type == null || cm is! num) return null;
    return MeasurementEntry(date: date, type: type, cm: cm.toDouble());
  }
}

/// Everything the user entered about their body; all fields are optional.
class BodyProgress {
  final double? heightCm;
  final double? targetWeightKg;
  final Sex? sex;
  final int? birthYear;

  /// Sorted oldest first.
  final List<WeightEntry> weights;
  final List<MeasurementEntry> measurements;

  const BodyProgress({
    this.heightCm,
    this.targetWeightKg,
    this.sex,
    this.birthYear,
    this.weights = const [],
    this.measurements = const [],
  });

  static const empty = BodyProgress();

  bool get hasData => weights.isNotEmpty || measurements.isNotEmpty;

  double? get startWeight => weights.isEmpty ? null : weights.first.kg;
  double? get currentWeight => weights.isEmpty ? null : weights.last.kg;

  double? get weightChange {
    final start = startWeight;
    final current = currentWeight;
    return start == null || current == null ? null : current - start;
  }

  /// 0..1 progress from the first weigh-in toward the target.
  double? get goalProgress {
    final start = startWeight;
    final current = currentWeight;
    final target = targetWeightKg;
    if (start == null || current == null || target == null) return null;
    final total = target - start;
    if (total.abs() < 0.05) return 1;
    return ((current - start) / total).clamp(0.0, 1.0);
  }

  double? get bmi {
    final height = heightCm;
    final weight = currentWeight;
    if (height == null || height <= 0 || weight == null) return null;
    final meters = height / 100;
    return weight / (meters * meters);
  }

  int? ageAt(DateTime now) {
    final year = birthYear;
    return year == null ? null : now.year - year;
  }

  /// Estimated body-fat percentage from BMI, age and sex (Deurenberg et al.,
  /// 1991). Only meaningful for adults; null when anything is missing.
  double? bodyFatPercent(DateTime now) {
    final bmi = this.bmi;
    final age = ageAt(now);
    final sex = this.sex;
    if (bmi == null || age == null || sex == null || age < 18) return null;
    final male = sex == Sex.male ? 1 : 0;
    return (1.2 * bmi + 0.23 * age - 10.8 * male - 5.4).clamp(2.0, 70.0);
  }

  /// Weight range for a BMI of 18.5-24.9 at the user's height.
  (double min, double max)? get healthyWeightRange {
    final height = heightCm;
    if (height == null || height <= 0) return null;
    final meters2 = (height / 100) * (height / 100);
    return (18.5 * meters2, 24.9 * meters2);
  }

  /// First and latest value for each measurement type that has entries.
  Map<MeasurementType, (double first, double latest)> get measurementSummary {
    final result = <MeasurementType, (double, double)>{};
    for (final type in MeasurementType.values) {
      final entries = measurements.where((m) => m.type == type).toList()
        ..sort((a, b) => a.date.compareTo(b.date));
      if (entries.isNotEmpty) {
        result[type] = (entries.first.cm, entries.last.cm);
      }
    }
    return result;
  }

  BodyProgress copyWith({
    double? heightCm,
    double? targetWeightKg,
    Sex? sex,
    int? birthYear,
    List<WeightEntry>? weights,
    List<MeasurementEntry>? measurements,
  }) {
    return BodyProgress(
      heightCm: heightCm ?? this.heightCm,
      targetWeightKg: targetWeightKg ?? this.targetWeightKg,
      sex: sex ?? this.sex,
      birthYear: birthYear ?? this.birthYear,
      weights: weights ?? this.weights,
      measurements: measurements ?? this.measurements,
    );
  }

  Map<String, Object?> toJson() => {
    'heightCm': heightCm,
    'targetWeightKg': targetWeightKg,
    'sex': sex?.name,
    'birthYear': birthYear,
    'weights': weights.map((w) => w.toJson()).toList(),
    'measurements': measurements.map((m) => m.toJson()).toList(),
  };

  static BodyProgress fromJson(Object? json) {
    if (json is! Map) return empty;
    double? number(Object? value) => value is num ? value.toDouble() : null;
    final weights = [
      if (json['weights'] is List)
        for (final item in json['weights'] as List) ?WeightEntry.fromJson(item),
    ]..sort((a, b) => a.date.compareTo(b.date));
    return BodyProgress(
      heightCm: number(json['heightCm']),
      targetWeightKg: number(json['targetWeightKg']),
      sex: Sex.values.where((s) => s.name == json['sex']).firstOrNull,
      birthYear: json['birthYear'] is int ? json['birthYear'] as int : null,
      weights: weights,
      measurements: [
        if (json['measurements'] is List)
          for (final item in json['measurements'] as List)
            ?MeasurementEntry.fromJson(item),
      ],
    );
  }
}

/// ACE body-fat band for a percentage; the cut-offs differ by sex.
BodyFatBand bodyFatBand(double percent, Sex sex) {
  final limits = sex == Sex.male
      ? const [6.0, 14.0, 18.0, 25.0]
      : const [14.0, 21.0, 25.0, 32.0];
  if (percent < limits[0]) return BodyFatBand.essential;
  if (percent < limits[1]) return BodyFatBand.athletic;
  if (percent < limits[2]) return BodyFatBand.fitness;
  if (percent < limits[3]) return BodyFatBand.average;
  return BodyFatBand.high;
}
