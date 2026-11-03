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
            if (body.currentWeight != null) _BmiCard(body: body),
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
      builder: (context, results, _) {
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
          actionLabel: l10n.progressMyDetails,
          onAction: () => _editDetails(context, body),
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

String sexName(AppLocalizations l10n, Sex sex) => switch (sex) {
  Sex.female => l10n.sexFemale,
  Sex.male => l10n.sexMale,
};

/// BMI with WHO category and scale, plus a sex- and age-specific body-fat
/// estimate when the user has entered those details.
class _BmiCard extends StatelessWidget {
  final BodyProgress body;

  const _BmiCard({required this.body});

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final tokens = context.tokens;
    final bmi = body.bmi;
    final now = DateTime.now();
    final age = body.ageAt(now);
    final sex = body.sex;
    final fat = body.bodyFatPercent(now);
    final range = body.healthyWeightRange;

    Widget personalize(String message) => Row(
      children: [
        IconBadge(
          icon: Icons.person_search_rounded,
          color: context.colors.secondary,
          size: 36,
        ),
        const SizedBox(width: Gap.md),
        Expanded(child: Text(message, style: context.text.bodySmall)),
        TextButton(
          key: const Key('bmi_personalize'),
          onPressed: () => _editDetails(context, body),
          child: Text(l10n.progressMyDetails),
        ),
      ],
    );

    if (bmi == null) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          SectionHeader(title: l10n.bmiTitle),
          AppCard(child: personalize(l10n.bmiNeedHeight)),
        ],
      );
    }

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
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                children: [
                  Text(
                    bmi.toStringAsFixed(1),
                    style: context.text.headlineMedium,
                  ),
                  const SizedBox(width: Gap.md),
                  Pill(label: label, color: color),
                  const Spacer(),
                  if (sex != null)
                    Pill(
                      label: sexName(l10n, sex),
                      icon: sex == Sex.female
                          ? Icons.female_rounded
                          : Icons.male_rounded,
                      color: context.colors.secondary,
                    ),
                ],
              ),
              const SizedBox(height: Gap.md),
              _BmiScale(bmi: bmi),
              if (range != null) ...[
                const SizedBox(height: Gap.md),
                Text(
                  l10n.bmiHealthyRange(_kg(range.$1), _kg(range.$2)),
                  style: context.text.bodyMedium,
                ),
              ],
              const SizedBox(height: Gap.lg),
              const Divider(),
              const SizedBox(height: Gap.lg),
              if (fat != null && sex != null)
                _BodyFatRow(percent: fat, sex: sex)
              else if (sex != null && age != null && age < 18)
                Text(l10n.bmiAdultsOnly, style: context.text.bodySmall)
              else
                personalize(l10n.bmiPersonalizeBody),
              const SizedBox(height: Gap.md),
              Text(l10n.bmiMethodNote, style: context.text.bodySmall),
            ],
          ),
        ),
      ],
    );
  }
}

/// Horizontal BMI scale (15-35) with the four WHO bands and a marker.
class _BmiScale extends StatelessWidget {
  final double bmi;

  const _BmiScale({required this.bmi});

  static const double _min = 15, _max = 35;

  @override
  Widget build(BuildContext context) {
    final tokens = context.tokens;
    final bands = [
      (18.5 - _min, tokens.warning),
      (25 - 18.5, tokens.success),
      (30 - 25.0, tokens.warning),
      (_max - 30, tokens.danger),
    ];
    final position = ((bmi - _min) / (_max - _min)).clamp(0.0, 1.0);

    return ExcludeSemantics(
      child: SizedBox(
        height: 18,
        child: LayoutBuilder(
          builder: (context, constraints) => Stack(
            children: [
              Positioned.fill(
                top: 6,
                bottom: 6,
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    for (final (i, (width, color)) in bands.indexed) ...[
                      if (i > 0) const SizedBox(width: 2),
                      Expanded(
                        flex: (width * 10).round(),
                        child: DecoratedBox(
                          decoration: BoxDecoration(
                            color: color.withValues(alpha: 0.55),
                            borderRadius: BorderRadius.circular(3),
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              Positioned(
                left: position * (constraints.maxWidth - 6),
                top: 0,
                bottom: 0,
                child: Container(
                  width: 6,
                  decoration: BoxDecoration(
                    color: context.colors.onSurface,
                    borderRadius: BorderRadius.circular(3),
                    border: Border.all(color: context.colors.surface),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _BodyFatRow extends StatelessWidget {
  final double percent;
  final Sex sex;

  const _BodyFatRow({required this.percent, required this.sex});

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final tokens = context.tokens;
    final (label, color) = switch (bodyFatBand(percent, sex)) {
      BodyFatBand.essential => (l10n.bodyFatEssential, tokens.warning),
      BodyFatBand.athletic => (l10n.bodyFatAthletic, tokens.success),
      BodyFatBand.fitness => (l10n.bodyFatFitness, tokens.success),
      BodyFatBand.average => (l10n.bodyFatAverage, tokens.info),
      BodyFatBand.high => (l10n.bodyFatHigh, tokens.danger),
    };
    final percentText = NumberFormat.decimalPercentPattern(
      locale: Localizations.localeOf(context).toLanguageTag(),
      decimalDigits: 1,
    ).format(percent / 100);

    return Row(
      children: [
        IconBadge(icon: Icons.water_drop_outlined, color: color),
        const SizedBox(width: Gap.md),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(l10n.bmiBodyFat, style: context.text.labelMedium),
              Text(percentText, style: context.text.titleLarge),
            ],
          ),
        ),
        Column(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Pill(label: label, color: color),
            const SizedBox(height: 4),
            Text(
              l10n.bmiBodyFatFor(sexName(l10n, sex)),
              style: context.text.bodySmall,
            ),
          ],
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

Future<void> _editDetails(BuildContext context, BodyProgress body) async {
  final saved = await showModalBottomSheet<bool>(
    context: context,
    isScrollControlled: true,
    builder: (_) => _DetailsSheet(body: body),
  );
  if (saved == true && context.mounted) {
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(context.l10n.detailsSaved)));
  }
}

/// Sex, birth year, height and target weight in one form.
class _DetailsSheet extends StatefulWidget {
  final BodyProgress body;

  const _DetailsSheet({required this.body});

  @override
  State<_DetailsSheet> createState() => _DetailsSheetState();
}

class _DetailsSheetState extends State<_DetailsSheet> {
  final _formKey = GlobalKey<FormState>();
  late Sex? _sex = widget.body.sex;
  late final _birthYear = TextEditingController(
    text: widget.body.birthYear?.toString() ?? '',
  );
  late final _height = TextEditingController(
    text: widget.body.heightCm == null ? '' : _kg(widget.body.heightCm!),
  );
  late final _target = TextEditingController(
    text: widget.body.targetWeightKg == null
        ? ''
        : _kg(widget.body.targetWeightKg!),
  );

  @override
  void dispose() {
    _birthYear.dispose();
    _height.dispose();
    _target.dispose();
    super.dispose();
  }

  static double? _parse(String text) =>
      double.tryParse(text.trim().replaceAll(',', '.'));

  String? Function(String?) _range(double min, double max, String unit) {
    return (value) {
      if (value == null || value.trim().isEmpty) return null;
      final number = _parse(value);
      if (number == null || number < min || number > max) {
        return context.l10n.progressRangeError(_kg(min), _kg(max), unit);
      }
      return null;
    };
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    await BodyProgressStore.setProfile(
      sex: _sex,
      birthYear: int.tryParse(_birthYear.text.trim()),
      heightCm: _parse(_height.text),
      targetWeightKg: _parse(_target.text),
    );
    if (mounted) Navigator.of(context).pop(true);
  }

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final thisYear = DateTime.now().year;
    final decimal = [FilteringTextInputFormatter.allow(RegExp(r'[0-9.,]'))];

    return Padding(
      padding: EdgeInsets.only(
        left: Gap.page,
        right: Gap.page,
        bottom: MediaQuery.viewInsetsOf(context).bottom + Gap.xl,
      ),
      child: Form(
        key: _formKey,
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(l10n.detailsTitle, style: context.text.titleLarge),
              const SizedBox(height: Gap.xs),
              Text(l10n.detailsBody, style: context.text.bodySmall),
              const SizedBox(height: Gap.xl),
              Text(l10n.sexLabel, style: context.text.labelLarge),
              const SizedBox(height: Gap.sm),
              SegmentedButton<Sex>(
                key: const Key('details_sex'),
                showSelectedIcon: false,
                emptySelectionAllowed: true,
                segments: [
                  ButtonSegment(
                    value: Sex.female,
                    label: Text(l10n.sexFemale),
                    icon: const Icon(Icons.female_rounded),
                  ),
                  ButtonSegment(
                    value: Sex.male,
                    label: Text(l10n.sexMale),
                    icon: const Icon(Icons.male_rounded),
                  ),
                ],
                selected: {?_sex},
                onSelectionChanged: (value) =>
                    setState(() => _sex = value.firstOrNull),
              ),
              const SizedBox(height: Gap.lg),
              TextFormField(
                key: const Key('details_birth_year'),
                controller: _birthYear,
                keyboardType: TextInputType.number,
                inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                decoration: InputDecoration(labelText: l10n.birthYearLabel),
                validator: (value) {
                  if (value == null || value.trim().isEmpty) return null;
                  final year = int.tryParse(value.trim());
                  final (min, max) = (thisYear - 100, thisYear - 10);
                  if (year == null || year < min || year > max) {
                    return l10n.progressRangeError('$min', '$max', '');
                  }
                  return null;
                },
              ),
              const SizedBox(height: Gap.lg),
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: TextFormField(
                      key: const Key('details_height'),
                      controller: _height,
                      keyboardType: const TextInputType.numberWithOptions(
                        decimal: true,
                      ),
                      inputFormatters: decimal,
                      decoration: InputDecoration(
                        labelText: l10n.progressHeight,
                        suffixText: 'cm',
                      ),
                      validator: _range(80, 250, 'cm'),
                    ),
                  ),
                  const SizedBox(width: Gap.md),
                  Expanded(
                    child: TextFormField(
                      key: const Key('details_target'),
                      controller: _target,
                      keyboardType: const TextInputType.numberWithOptions(
                        decimal: true,
                      ),
                      inputFormatters: decimal,
                      decoration: InputDecoration(
                        labelText: l10n.progressTargetWeight,
                        suffixText: 'kg',
                      ),
                      validator: _range(20, 400, 'kg'),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: Gap.xl),
              FilledButton(
                key: const Key('details_save'),
                onPressed: _save,
                child: Text(l10n.commonSave),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
