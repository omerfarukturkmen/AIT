import 'package:flutter/foundation.dart';

import '../../models/analysis_result_model.dart';

class AnalysisHistoryStore {
  static final ValueNotifier<List<AnalysisResult>> results =
      ValueNotifier<List<AnalysisResult>>(<AnalysisResult>[]);

  static void addResult(AnalysisResult result) {
    results.value = [result, ...results.value];
  }

  static void clearHistory() {
    results.value = [];
  }

  static int get totalAnalyses => results.value.length;

  static int get averageScore {
    if (results.value.isEmpty) return 0;

    final total = results.value.fold<int>(
      0,
      (sum, result) => sum + result.score,
    );

    return (total / results.value.length).round();
  }

  static int get bestScore {
    if (results.value.isEmpty) return 0;

    return results.value
        .map((result) => result.score)
        .reduce((current, next) => current > next ? current : next);
  }

  static AnalysisResult? get latestResult {
    if (results.value.isEmpty) return null;
    return results.value.first;
  }
}
