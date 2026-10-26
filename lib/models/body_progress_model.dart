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

  /// Sorted oldest first.
  final List<WeightEntry> weights;
  final List<MeasurementEntry> measurements;

  const BodyProgress({
    this.heightCm,
    this.targetWeightKg,
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
    List<WeightEntry>? weights,
    List<MeasurementEntry>? measurements,
  }) {
    return BodyProgress(
      heightCm: heightCm ?? this.heightCm,
      targetWeightKg: targetWeightKg ?? this.targetWeightKg,
      weights: weights ?? this.weights,
      measurements: measurements ?? this.measurements,
    );
  }

  Map<String, Object?> toJson() => {
    'heightCm': heightCm,
    'targetWeightKg': targetWeightKg,
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
      weights: weights,
      measurements: [
        if (json['measurements'] is List)
          for (final item in json['measurements'] as List)
            ?MeasurementEntry.fromJson(item),
      ],
    );
  }
}
