import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../app.dart';
import '../../core/state/navigation_store.dart';
import '../../core/theme/app_theme.dart';
import '../../data/exercise_catalog.dart';
import '../../l10n/analysis_messages.dart';
import '../../l10n/app_localizations.dart';
import '../../l10n/form_issues.dart';
import '../../models/analysis_result_model.dart';
import '../../widgets/app_card.dart';
import '../../widgets/common.dart';
import '../../widgets/page_scaffold.dart';

String scoreLabel(AppLocalizations l10n, int score) {
  if (score >= 90) return l10n.scoreExcellent;
  if (score >= 75) return l10n.scoreGood;
  if (score >= 50) return l10n.scoreFair;
  return l10n.scoreNeedsWork;
}

class ResultPage extends StatelessWidget {
  final AnalysisResult result;

  const ResultPage({super.key, required this.result});

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final locale = Localizations.localeOf(context).toLanguageTag();
    final date = DateFormat.yMMMd(locale).add_Hm().format(result.createdAt);
    final issues = result.issueCodes
        .map((code) => formIssue(l10n, code))
        .toList();
    final warnings = [
      for (final code in result.warningCodes) ?analysisWarningText(l10n, code),
    ];
    final showDepth =
        result.exercise == ExerciseId.squat &&
        (result.averageMinKneeAngle != null ||
            result.kneeRangeOfMotion != null);

    return Scaffold(
      appBar: AppBar(title: Text(result.exercise.title(l10n))),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(
            Gap.page,
            Gap.sm,
            Gap.page,
            Gap.xxl,
          ),
          children: [
            Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(
                  maxWidth: PageScaffold.maxContentWidth,
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Text(date, style: context.text.bodySmall),
                    const SizedBox(height: Gap.md),
                    _ScoreCard(result: result),
                    const SizedBox(height: Gap.md),
                    Row(
                      children: [
                        Expanded(
                          child: StatTile(
                            label: l10n.resultReps,
                            value: result.invalidReps > 0
                                ? '${result.validReps}/${result.repetitionCount}'
                                : '${result.repetitionCount}',
                            icon: Icons.repeat_rounded,
                          ),
                        ),
                        const SizedBox(width: Gap.md),
                        Expanded(
                          child: StatTile(
                            label: l10n.resultDuration,
                            value: l10n.unitSeconds(
                              result.durationSeconds.round(),
                            ),
                            icon: Icons.timer_outlined,
                          ),
                        ),
                        const SizedBox(width: Gap.md),
                        Expanded(
                          child: StatTile(
                            label: l10n.resultConfidence,
                            value: NumberFormat.percentPattern(
                              locale,
                            ).format(result.confidencePercent / 100),
                            icon: Icons.visibility_outlined,
                          ),
                        ),
                      ],
                    ),
                    if (result.invalidReps > 0) ...[
                      const SizedBox(height: Gap.sm),
                      Text(
                        l10n.resultValidRepsNote(
                          result.validReps,
                          result.repetitionCount,
                        ),
                        style: context.text.bodySmall,
                      ),
                    ],
                    if (warnings.isNotEmpty) ...[
                      SectionHeader(title: l10n.warningTitle),
                      _WarningsCard(warnings: warnings),
                    ],
                    if (showDepth) ...[
                      SectionHeader(title: l10n.resultDepthTitle),
                      AppCard(
                        child: Column(
                          children: [
                            if (result.averageMinKneeAngle != null)
                              _MetricRow(
                                label: l10n.resultAvgKneeAngle,
                                value:
                                    '${result.averageMinKneeAngle!.round()}°',
                                help: l10n.resultAvgKneeAngleHelp,
                              ),
                            if (result.averageMinKneeAngle != null &&
                                result.kneeRangeOfMotion != null)
                              const Divider(height: Gap.xl),
                            if (result.kneeRangeOfMotion != null)
                              _MetricRow(
                                label: l10n.resultRangeOfMotion,
                                value: '${result.kneeRangeOfMotion!.round()}°',
                                help: l10n.resultRangeOfMotionHelp,
                              ),
                          ],
                        ),
                      ),
                    ],
                    SectionHeader(title: l10n.resultIssuesTitle),
                    if (issues.isEmpty)
                      AppCard(
                        child: Row(
                          children: [
                            IconBadge(
                              icon: Icons.check_rounded,
                              color: context.tokens.success,
                            ),
                            const SizedBox(width: Gap.md),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    l10n.issueNoneTitle,
                                    style: context.text.titleSmall,
                                  ),
                                  const SizedBox(height: 2),
                                  Text(
                                    l10n.issueNoneMessage,
                                    style: context.text.bodySmall,
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      )
                    else
                      for (final issue in issues) ...[
                        _IssueCard(issue: issue),
                        const SizedBox(height: Gap.sm),
                      ],
                    SectionHeader(title: l10n.resultTipsTitle),
                    AppCard(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          for (final tip in result.exercise.tips(l10n))
                            Padding(
                              padding: const EdgeInsets.symmetric(
                                vertical: Gap.xs,
                              ),
                              child: Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Icon(
                                    Icons.check_rounded,
                                    size: 18,
                                    color: context.colors.primary,
                                  ),
                                  const SizedBox(width: Gap.sm),
                                  Expanded(
                                    child: Text(
                                      tip,
                                      style: context.text.bodyMedium,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                        ],
                      ),
                    ),
                    const SizedBox(height: Gap.xl),
                    FilledButton.icon(
                      onPressed: () {
                        NavigationStore.go(AppTab.home);
                        Navigator.of(
                          context,
                        ).popUntil((route) => route.isFirst);
                      },
                      icon: const Icon(Icons.add_rounded),
                      label: Text(l10n.resultNewAnalysis),
                    ),
                    const SizedBox(height: Gap.lg),
                    Text(
                      l10n.resultDisclaimer,
                      textAlign: TextAlign.center,
                      style: context.text.bodySmall?.copyWith(
                        color: context.tokens.textTertiary,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ScoreCard extends StatelessWidget {
  final AnalysisResult result;

  const _ScoreCard({required this.result});

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    if (!result.isScored) {
      return AppCard(
        key: const Key('result_not_scored'),
        padding: const EdgeInsets.all(Gap.xl),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            IconBadge(
              icon: Icons.do_not_disturb_on_outlined,
              color: context.tokens.textSecondary,
              size: 52,
            ),
            const SizedBox(width: Gap.lg),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(l10n.resultNotScored, style: context.text.titleLarge),
                  const SizedBox(height: Gap.sm),
                  Text(
                    l10n.resultNotScoredBody,
                    style: context.text.bodyMedium?.copyWith(
                      color: context.tokens.textSecondary,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      );
    }
    final color = context.tokens.scoreColor(result.score);
    return AppCard(
      padding: const EdgeInsets.all(Gap.xl),
      child: Row(
        children: [
          ScoreRing(
            score: result.score,
            size: 112,
            caption: l10n.resultScoreCaption,
          ),
          const SizedBox(width: Gap.xl),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Pill(label: scoreLabel(l10n, result.score), color: color),
                const SizedBox(height: Gap.md),
                Text(
                  result.issueCodes.isEmpty
                      ? l10n.resultSummaryClean
                      : l10n.resultSummaryIssues(result.issueCodes.length),
                  style: context.text.bodyMedium?.copyWith(
                    color: context.tokens.textSecondary,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// Notes on recording quality; the result is still shown.
class _WarningsCard extends StatelessWidget {
  final List<String> warnings;

  const _WarningsCard({required this.warnings});

  @override
  Widget build(BuildContext context) {
    return AppCard(
      key: const Key('result_warnings'),
      child: Column(
        children: [
          for (final (i, warning) in warnings.indexed) ...[
            if (i > 0) const Divider(height: Gap.xl),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                IconBadge(
                  icon: Icons.videocam_outlined,
                  color: context.tokens.info,
                  size: 36,
                ),
                const SizedBox(width: Gap.md),
                Expanded(child: Text(warning, style: context.text.bodyMedium)),
              ],
            ),
          ],
        ],
      ),
    );
  }
}

class _IssueCard extends StatelessWidget {
  final FormIssue issue;

  const _IssueCard({required this.issue});

  @override
  Widget build(BuildContext context) {
    return AppCard(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          IconBadge(
            icon: Icons.priority_high_rounded,
            color: context.tokens.warning,
          ),
          const SizedBox(width: Gap.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(issue.title, style: context.text.titleSmall),
                const SizedBox(height: Gap.xs),
                Text(
                  issue.fix,
                  style: context.text.bodyMedium?.copyWith(
                    color: context.tokens.textSecondary,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _MetricRow extends StatelessWidget {
  final String label;
  final String value;
  final String help;

  const _MetricRow({
    required this.label,
    required this.value,
    required this.help,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label, style: context.text.titleSmall),
              const SizedBox(height: 2),
              Text(help, style: context.text.bodySmall),
            ],
          ),
        ),
        const SizedBox(width: Gap.md),
        Text(value, style: context.text.headlineSmall),
      ],
    );
  }
}
