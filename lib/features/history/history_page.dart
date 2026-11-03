import 'package:flutter/material.dart';

import '../../app.dart';
import '../../core/state/analysis_history_store.dart';
import '../../core/state/navigation_store.dart';
import '../../core/theme/app_theme.dart';
import '../../data/exercise_catalog.dart';
import '../../models/analysis_result_model.dart';
import '../../widgets/common.dart';
import '../../widgets/page_scaffold.dart';
import '../home/home_page.dart' show AnalysisListTile;

class HistoryPage extends StatefulWidget {
  const HistoryPage({super.key});

  @override
  State<HistoryPage> createState() => _HistoryPageState();
}

class _HistoryPageState extends State<HistoryPage> {
  ExerciseId? _filter;

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final supported = ExerciseId.values.where((e) => e.analysisSupported);

    return ValueListenableBuilder<HistoryStatus>(
      valueListenable: AnalysisHistoryStore.status,
      builder: (context, status, _) {
        return ValueListenableBuilder<List<AnalysisResult>>(
          valueListenable: AnalysisHistoryStore.results,
          builder: (context, results, _) {
            final filtered = _filter == null
                ? results
                : results.where((r) => r.exercise == _filter).toList();

            return PageScaffold(
              title: l10n.historyTitle,
              subtitle: results.isEmpty
                  ? null
                  : l10n.historyCount(results.length),
              onRefresh: AnalysisHistoryStore.refresh,
              children: [
                if (results.isNotEmpty) ...[
                  Wrap(
                    spacing: Gap.sm,
                    children: [
                      ChoiceChip(
                        label: Text(l10n.historyAll),
                        selected: _filter == null,
                        onSelected: (_) => setState(() => _filter = null),
                      ),
                      for (final exercise in supported)
                        ChoiceChip(
                          label: Text(exercise.title(l10n)),
                          selected: _filter == exercise,
                          onSelected: (_) => setState(() => _filter = exercise),
                        ),
                    ],
                  ),
                  const SizedBox(height: Gap.lg),
                ],
                if (status == HistoryStatus.loading && results.isEmpty)
                  const Padding(
                    padding: EdgeInsets.all(Gap.xxl),
                    child: Center(child: CircularProgressIndicator()),
                  )
                else if (status == HistoryStatus.error && results.isEmpty)
                  EmptyState(
                    icon: Icons.cloud_off_rounded,
                    title: l10n.historyErrorTitle,
                    message:
                        AnalysisHistoryStore.lastError?.message(l10n) ??
                        l10n.errorUnknown,
                    actionLabel: l10n.commonRetry,
                    onAction: AnalysisHistoryStore.refresh,
                  )
                else if (results.isEmpty)
                  EmptyState(
                    icon: Icons.history_rounded,
                    title: l10n.homeEmptyTitle,
                    message: l10n.homeEmptyBody,
                    actionLabel: l10n.homeNewAnalysis,
                    onAction: () => NavigationStore.go(AppTab.home),
                  )
                else if (filtered.isEmpty)
                  EmptyState(
                    icon: Icons.filter_alt_off_rounded,
                    title: l10n.historyNoMatch,
                    message: l10n.historyNoMatchBody,
                  )
                else
                  for (final result in filtered) ...[
                    AnalysisListTile(result: result),
                    const SizedBox(height: Gap.sm),
                  ],
              ],
            );
          },
        );
      },
    );
  }
}
