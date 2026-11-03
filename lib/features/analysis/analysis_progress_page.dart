import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_tts/flutter_tts.dart';

import '../../app.dart';
import '../../core/app_exception.dart';
import '../../core/state/analysis_history_store.dart';
import '../../core/state/app_settings_store.dart';
import '../../core/theme/app_theme.dart';
import '../../data/api_service.dart';
import '../../data/exercise_catalog.dart';
import '../../l10n/form_issues.dart';
import '../../models/analysis_result_model.dart';
import '../../widgets/app_card.dart';
import '../../widgets/common.dart';
import '../result/result_page.dart';

/// Uploads the video, follows the server-side analysis and opens the result.
class AnalysisProgressPage extends StatefulWidget {
  final ExerciseId exercise;
  final Uint8List videoBytes;
  final String fileName;

  const AnalysisProgressPage({
    super.key,
    required this.exercise,
    required this.videoBytes,
    required this.fileName,
  });

  @override
  State<AnalysisProgressPage> createState() => _AnalysisProgressPageState();
}

class _AnalysisProgressPageState extends State<AnalysisProgressPage> {
  AnalysisStage _stage = AnalysisStage.uploading;
  AppException? _error;

  @override
  void initState() {
    super.initState();
    _run();
  }

  Future<void> _run() async {
    setState(() {
      _stage = AnalysisStage.uploading;
      _error = null;
    });
    try {
      final id = await ApiService.uploadVideo(
        videoBytes: widget.videoBytes,
        fileName: widget.fileName,
        exercise: widget.exercise,
      );
      if (!mounted) return;
      setState(() => _stage = AnalysisStage.queued);

      final result = await ApiService.waitForResult(
        id,
        onStage: (stage) {
          if (mounted && stage != _stage) setState(() => _stage = stage);
        },
      );
      AnalysisHistoryStore.addResult(result);
      if (!mounted) return;
      _announce(result);
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => ResultPage(result: result)),
      );
    } on AppException catch (error) {
      if (mounted) {
        setState(() {
          _error = error;
          _stage = AnalysisStage.failed;
        });
      }
    }
  }

  /// Reads the real result aloud when voice feedback is on.
  Future<void> _announce(AnalysisResult result) async {
    final settings = AppSettingsStore.settings.value;
    if (!settings.voiceFeedbackEnabled) return;
    final l10n = context.l10n;
    final topIssue = result.issueCodes.isEmpty
        ? l10n.issueNoneTitle
        : formIssue(l10n, result.issueCodes.first).title;
    try {
      final tts = FlutterTts();
      await tts.setLanguage(settings.ttsLanguage);
      await tts.speak(
        result.isScored
            ? l10n.voiceResultSummary(
                result.score,
                result.repetitionCount,
                topIssue,
              )
            : l10n.resultNotScoredBody,
      );
    } catch (_) {
      // Voice is optional.
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final failed = _stage == AnalysisStage.failed;
    final steps = [
      (AnalysisStage.uploading, l10n.progressUploading),
      (AnalysisStage.queued, l10n.progressQueued),
      (AnalysisStage.processing, l10n.progressProcessing),
    ];
    final currentIndex = steps.indexWhere((s) => s.$1 == _stage);

    return Scaffold(
      appBar: AppBar(title: Text(l10n.progressTitle)),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(Gap.page),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 480),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  AppCard(
                    child: Row(
                      children: [
                        IconBadge(icon: widget.exercise.icon, size: 48),
                        const SizedBox(width: Gap.md + 2),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                widget.exercise.title(l10n),
                                style: context.text.titleMedium,
                              ),
                              const SizedBox(height: 2),
                              Text(
                                l10n.progressVideoSize(
                                  (widget.videoBytes.lengthInBytes /
                                          (1024 * 1024))
                                      .toStringAsFixed(1),
                                ),
                                style: context.text.bodySmall,
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: Gap.xl),
                  if (failed)
                    _FailureView(
                      message: _error?.message(l10n) ?? l10n.errorUnknown,
                      onRetry: _run,
                    )
                  else ...[
                    for (var i = 0; i < steps.length; i++)
                      _StepRow(
                        label: steps[i].$2,
                        state: i < currentIndex
                            ? _StepState.done
                            : i == currentIndex
                            ? _StepState.active
                            : _StepState.pending,
                      ),
                    const SizedBox(height: Gap.xl),
                    Text(
                      l10n.progressLeaveHint,
                      textAlign: TextAlign.center,
                      style: context.text.bodySmall,
                    ),
                  ],
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

enum _StepState { done, active, pending }

class _StepRow extends StatelessWidget {
  final String label;
  final _StepState state;

  const _StepRow({required this.label, required this.state});

  @override
  Widget build(BuildContext context) {
    final tokens = context.tokens;
    final Widget leading = switch (state) {
      _StepState.done => Icon(
        Icons.check_circle_rounded,
        color: tokens.success,
      ),
      _StepState.active => const SizedBox.square(
        dimension: 22,
        child: CircularProgressIndicator(strokeWidth: 2.4),
      ),
      _StepState.pending => Icon(
        Icons.radio_button_unchecked_rounded,
        color: tokens.textTertiary,
      ),
    };

    return Semantics(
      liveRegion: state == _StepState.active,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: Gap.sm + 2),
        child: Row(
          children: [
            SizedBox(width: 28, child: Center(child: leading)),
            const SizedBox(width: Gap.md),
            Expanded(
              child: Text(
                label,
                style: context.text.bodyLarge?.copyWith(
                  color: state == _StepState.pending
                      ? tokens.textTertiary
                      : null,
                  fontWeight: state == _StepState.active
                      ? FontWeight.w600
                      : null,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _FailureView extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;

  const _FailureView({required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Icon(
          Icons.error_outline_rounded,
          size: 48,
          color: context.tokens.danger,
        ),
        const SizedBox(height: Gap.lg),
        Text(
          l10n.progressFailedTitle,
          textAlign: TextAlign.center,
          style: context.text.titleLarge,
        ),
        const SizedBox(height: Gap.sm),
        Text(
          message,
          textAlign: TextAlign.center,
          style: context.text.bodyMedium?.copyWith(
            color: context.tokens.textSecondary,
          ),
        ),
        const SizedBox(height: Gap.xl),
        FilledButton(onPressed: onRetry, child: Text(l10n.commonRetry)),
        const SizedBox(height: Gap.sm),
        OutlinedButton(
          onPressed: () => Navigator.of(context).pop(),
          child: Text(l10n.commonBack),
        ),
      ],
    );
  }
}
