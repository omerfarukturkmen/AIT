import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:intl/intl.dart';

import '../../app.dart';
import '../../core/state/analysis_history_store.dart';
import '../../core/state/body_progress_store.dart';
import '../../core/theme/app_theme.dart';
import '../../l10n/app_localizations.dart';
import '../../models/analysis_result_model.dart';
import '../../models/body_progress_model.dart';
import '../../widgets/app_card.dart';
import '../../widgets/common.dart';
import '../../widgets/page_scaffold.dart';
import '../../widgets/trend_chart.dart';

String measurementName(AppLocalizations l10n, MeasurementType type) =>
    switch (type) {
      MeasurementType.waist => l10n.measureWaist,
      MeasurementType.hip => l10n.measureHip,
      MeasurementType.chest => l10n.measureChest,
      MeasurementType.arm => l10n.measureArm,
      MeasurementType.thigh => l10n.measureThigh,
    };

String _kg(double value) => NumberFormat('0.#').format(value);

class ProgressPage extends StatelessWidget {
  const ProgressPage({super.key});

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    return ValueListenableBuilder<BodyProgress>(
      valueListenable: BodyProgressStore.progress,
      builder: (context, body, _) {
        return PageScaffold(
          title: l10n.progressPageTitle,
          subtitle: l10n.progressPageSubtitle,
          children: [
            const _ScoreTrend(),
            _WeightSection(body: body),
            if (body.bmi != null) _BmiCard(bmi: body.bmi!),
            _MeasurementsSection(body: body),
            const SizedBox(height: Gap.xl),
            Row(
              children: [
                Icon(
                  Icons.lock_outline_rounded,
                  size: 16,
                  color: context.tokens.textTertiary,
                ),
                const SizedBox(width: Gap.sm),
                Expanded(
                  child: Text(
                    l10n.progressLocalNote,
                    style: context.text.bodySmall,
                  ),
                ),
              ],
            ),
          ],
        );
      },
    );
  }
}

class _ScoreTrend extends StatelessWidget {
  const _ScoreTrend();

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    return ValueListenableBuilder<List<AnalysisResult>>(
      valueListenable: AnalysisHistoryStore.results,
      builder: (context, all, _) {
        final results = all.where((r) => r.isScored).toList();
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            SectionHeader(title: l10n.progressScoreTitle),
            if (results.length < 2)
              EmptyState(
                icon: Icons.show_chart_rounded,
                title: l10n.progressScoreEmptyTitle,
                message: l10n.progressScoreEmptyBody,
              )
            else
              AppCard(
                padding: const EdgeInsets.fromLTRB(
                  Gap.sm,
                  Gap.lg,
                  Gap.lg,
                  Gap.sm,
                ),
                child: TrendChart(
                  points: [
                    for (final r in results)
                      TrendPoint(r.createdAt, r.score.toDouble()),
                  ],
                  minY: 0,
                  maxY: 100,
                  format: (v) => '${v.round()}',
                  semanticsLabel: l10n.progressScoreTitle,
                ),
              ),
          ],
        );
      },
    );
  }
}

class _WeightSection extends StatelessWidget {
  final BodyProgress body;

  const _WeightSection({required this.body});

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final current = body.currentWeight;
    final change = body.weightChange;
    final progress = body.goalProgress;
    final dateFormat = DateFormat.yMMMd(
      Localizations.localeOf(context).toLanguageTag(),
    );

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        SectionHeader(
          title: l10n.progressWeightTitle,
          actionLabel: l10n.progressGoalAndHeight,
          onAction: () => _editProfile(context, body),
        ),
        if (current == null)
          EmptyState(
            icon: Icons.monitor_weight_outlined,
            title: l10n.progressWeightEmptyTitle,
            message: l10n.progressWeightEmptyBody,
            actionLabel: l10n.progressAddWeight,
            onAction: () => _addWeight(context),
          )
        else ...[
          AppCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Row(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(_kg(current), style: context.text.displaySmall),
                    const SizedBox(width: Gap.xs),
                    Padding(
                      padding: const EdgeInsets.only(bottom: 6),
                      child: Text('kg', style: context.text.titleMedium),
                    ),
                    const Spacer(),
                    if (change != null && body.weights.length > 1)
                      Pill(
                        label: '${change > 0 ? '+' : ''}${_kg(change)} kg',
                        icon: change <= 0
                            ? Icons.south_east_rounded
                            : Icons.north_east_rounded,
                      ),
                  ],
                ),
                if (progress != null) ...[
                  const SizedBox(height: Gap.lg),
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          l10n.progressGoal(_kg(body.targetWeightKg!)),
                          style: context.text.bodySmall,
                        ),
                      ),
                      Text(
                        NumberFormat.percentPattern(
                          Localizations.localeOf(context).toLanguageTag(),
                        ).format(progress),
                        style: context.text.labelLarge,
                      ),
                    ],
                  ),
                  const SizedBox(height: Gap.sm),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(4),
                    child: LinearProgressIndicator(
                      value: progress,
                      minHeight: 8,
                    ),
                  ),
                ],
                if (body.weights.length > 1) ...[
                  const SizedBox(height: Gap.xl),
                  TrendChart(
                    points: [
                      for (final w in body.weights) TrendPoint(w.date, w.kg),
                    ],
                    format: (v) => _kg(v),
                    semanticsLabel: l10n.progressWeightTitle,
                    height: 180,
                  ),
                ],
              ],
            ),
          ),
          const SizedBox(height: Gap.md),
          AppCard(
            padding: EdgeInsets.zero,
            child: Column(
              children: [
                for (final entry in body.weights.reversed.take(5))
                  ListTile(
                    dense: true,
                    title: Text(
                      '${_kg(entry.kg)} kg',
                      style: context.text.bodyMedium,
                    ),
                    subtitle: Text(dateFormat.format(entry.date)),
                    trailing: IconButton(
                      tooltip: l10n.commonDelete,
                      icon: const Icon(Icons.delete_outline_rounded, size: 20),
                      onPressed: () => BodyProgressStore.removeWeight(entry),
                    ),
                  ),
                const Divider(),
                TextButton.icon(
                  onPressed: () => _addWeight(context),
                  icon: const Icon(Icons.add_rounded),
                  label: Text(l10n.progressAddWeight),
                ),
              ],
            ),
          ),
        ],
      ],
    );
  }
}

class _BmiCard extends StatelessWidget {
  final double bmi;

  const _BmiCard({required this.bmi});

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final tokens = context.tokens;
    final (label, color) = bmi < 18.5
        ? (l10n.bmiUnder, tokens.warning)
        : bmi < 25
        ? (l10n.bmiNormal, tokens.success)
        : bmi < 30
        ? (l10n.bmiOver, tokens.warning)
        : (l10n.bmiObese, tokens.danger);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        SectionHeader(title: l10n.bmiTitle),
        AppCard(
          child: Row(
            children: [
              Text(bmi.toStringAsFixed(1), style: context.text.headlineMedium),
              const SizedBox(width: Gap.md),
              Pill(label: label, color: color),
              const Spacer(),
              Flexible(
                child: Text(
                  l10n.bmiNote,
                  textAlign: TextAlign.end,
                  style: context.text.bodySmall,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _MeasurementsSection extends StatelessWidget {
  final BodyProgress body;

  const _MeasurementsSection({required this.body});

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final summary = body.measurementSummary;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        SectionHeader(
          title: l10n.progressMeasurementsTitle,
          actionLabel: summary.isEmpty ? null : l10n.commonAdd,
          onAction: () => _addMeasurement(context),
        ),
        if (summary.isEmpty)
          EmptyState(
            icon: Icons.straighten_rounded,
            title: l10n.progressMeasurementsEmptyTitle,
            message: l10n.progressMeasurementsEmptyBody,
            actionLabel: l10n.progressAddMeasurement,
            onAction: () => _addMeasurement(context),
          )
        else
          AppCard(
            padding: EdgeInsets.zero,
            child: Column(
              children: [
                for (final entry in summary.entries)
                  ListTile(
                    title: Text(measurementName(l10n, entry.key)),
                    subtitle: entry.value.$1 == entry.value.$2
                        ? null
                        : Text(
                            l10n.progressMeasurementFrom(_kg(entry.value.$1)),
                          ),
                    trailing: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          '${_kg(entry.value.$2)} cm',
                          style: context.text.titleSmall,
                        ),
                        if (entry.value.$1 != entry.value.$2) ...[
                          const SizedBox(width: Gap.sm),
                          Pill(
                            label:
                                '${entry.value.$2 > entry.value.$1 ? '+' : ''}${_kg(entry.value.$2 - entry.value.$1)}',
                          ),
                        ],
                      ],
                    ),
                  ),
              ],
            ),
          ),
      ],
    );
  }
}

Future<double?> _askNumber(
  BuildContext context, {
  required String title,
  required String label,
  required String unit,
  required double min,
  required double max,
  double? initial,
}) {
  final controller = TextEditingController(
    text: initial == null ? '' : _kg(initial),
  );
  final formKey = GlobalKey<FormState>();
  final l10n = context.l10n;

  return showDialog<double>(
    context: context,
    builder: (context) {
      void submit() {
        if (formKey.currentState!.validate()) {
          Navigator.of(
            context,
          ).pop(double.parse(controller.text.replaceAll(',', '.')));
        }
      }

      return AlertDialog(
        title: Text(title),
        content: Form(
          key: formKey,
          child: TextFormField(
            controller: controller,
            autofocus: true,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            inputFormatters: [
              FilteringTextInputFormatter.allow(RegExp(r'[0-9.,]')),
            ],
            decoration: InputDecoration(labelText: label, suffixText: unit),
            validator: (value) {
              final number = double.tryParse(
                (value ?? '').replaceAll(',', '.'),
              );
              if (number == null || number < min || number > max) {
                return l10n.progressRangeError(_kg(min), _kg(max), unit);
              }
              return null;
            },
            onFieldSubmitted: (_) => submit(),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: Text(l10n.commonCancel),
          ),
          FilledButton(onPressed: submit, child: Text(l10n.commonSave)),
        ],
      );
    },
  );
}

Future<void> _addWeight(BuildContext context) async {
  final l10n = context.l10n;
  final kg = await _askNumber(
    context,
    title: l10n.progressAddWeight,
    label: l10n.progressWeightTitle,
    unit: 'kg',
    min: 20,
    max: 400,
    initial: BodyProgressStore.progress.value.currentWeight,
  );
  if (kg != null) await BodyProgressStore.addWeight(kg);
}

Future<void> _addMeasurement(BuildContext context) async {
  final l10n = context.l10n;
  final type = await showModalBottomSheet<MeasurementType>(
    context: context,
    builder: (context) => SafeArea(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Padding(
            padding: const EdgeInsets.only(bottom: Gap.sm),
            child: Text(
              l10n.progressAddMeasurement,
              style: context.text.titleMedium,
            ),
          ),
          for (final type in MeasurementType.values)
            ListTile(
              title: Text(measurementName(l10n, type)),
              onTap: () => Navigator.of(context).pop(type),
            ),
        ],
      ),
    ),
  );
  if (type == null || !context.mounted) return;
  final cm = await _askNumber(
    context,
    title: measurementName(l10n, type),
    label: measurementName(l10n, type),
    unit: 'cm',
    min: 10,
    max: 300,
  );
  if (cm != null) await BodyProgressStore.addMeasurement(type, cm);
}

Future<void> _editProfile(BuildContext context, BodyProgress body) async {
  final l10n = context.l10n;
  final height = await _askNumber(
    context,
    title: l10n.progressHeight,
    label: l10n.progressHeight,
    unit: 'cm',
    min: 80,
    max: 250,
    initial: body.heightCm,
  );
  if (!context.mounted) return;
  final target = await _askNumber(
    context,
    title: l10n.progressTargetWeight,
    label: l10n.progressTargetWeight,
    unit: 'kg',
    min: 20,
    max: 400,
    initial: body.targetWeightKg,
  );
  if (height != null || target != null) {
    await BodyProgressStore.setProfile(
      heightCm: height,
      targetWeightKg: target,
    );
  }
}
