import 'package:flutter/foundation.dart';

import '../../data/api_service.dart';
import '../../models/analysis_result_model.dart';
import '../app_exception.dart';

enum HistoryStatus { idle, loading, ready, error }

/// The signed-in user's analyses. The backend is the source of truth;
/// [refresh] loads them, new results are added locally as they complete.
class AnalysisHistoryStore {
  static final ValueNotifier<List<AnalysisResult>> results = ValueNotifier([]);
  static final ValueNotifier<HistoryStatus> status = ValueNotifier(
    HistoryStatus.idle,
  );
  static AppException? lastError;

  static Future<void> refresh() async {
    status.value = HistoryStatus.loading;
    try {
      results.value = await ApiService.fetchHistory();
      lastError = null;
      status.value = HistoryStatus.ready;
    } on AppException catch (error) {
      lastError = error;
      status.value = HistoryStatus.error;
    } catch (_) {
      // Unexpected response shape: show an error state, never crash.
      lastError = const AppException(ErrorKind.server);
      status.value = HistoryStatus.error;
    }
  }

  static void addResult(AnalysisResult result) {
    results.value = [
      result,
      ...results.value.where((r) => r.id == null || r.id != result.id),
    ];
  }

  static void clearHistory() {
    results.value = [];
    status.value = HistoryStatus.idle;
    lastError = null;
  }

  static int get totalAnalyses => results.value.length;

  /// Analyses with a real score (unscored ones would pull averages to 0).
  static Iterable<AnalysisResult> get _scored =>
      results.value.where((r) => r.isScored);

  static int get averageScore {
    final list = _scored.toList();
    if (list.isEmpty) return 0;
    return (list.fold<int>(0, (sum, r) => sum + r.score) / list.length).round();
  }

  static int get bestScore =>
      _scored.fold<int>(0, (best, r) => r.score > best ? r.score : best);

  static AnalysisResult? get latestResult =>
      results.value.isEmpty ? null : results.value.first;
}
