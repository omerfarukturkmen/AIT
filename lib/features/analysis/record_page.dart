import 'dart:async';

import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:flutter_tts/flutter_tts.dart';

import '../../app.dart';
import '../../core/state/app_settings_store.dart';
import '../../core/theme/app_theme.dart';
import '../../data/exercise_catalog.dart';
import 'analysis_progress_page.dart';

enum _RecordState { preparing, ready, countdown, recording, error }

/// Records the exercise with the camera, then hands the video to
/// [AnalysisProgressPage]. Nothing is analyzed while recording: the AI runs
/// on the server after upload, so no live score is shown.
class RecordPage extends StatefulWidget {
  final ExerciseId exercise;

  const RecordPage({super.key, required this.exercise});

  @override
  State<RecordPage> createState() => _RecordPageState();
}

class _RecordPageState extends State<RecordPage> {
  static const maxDuration = Duration(seconds: 60);

  final FlutterTts _tts = FlutterTts();
  List<CameraDescription> _cameras = const [];
  CameraController? _controller;
  _RecordState _state = _RecordState.preparing;
  int _countdown = 3;
  Duration _elapsed = Duration.zero;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _initCameras();
  }

  Future<void> _initCameras() async {
    try {
      _cameras = await availableCameras();
    } catch (_) {
      _cameras = const [];
    }
    if (_cameras.isEmpty) {
      if (mounted) setState(() => _state = _RecordState.error);
      return;
    }
    // Filming yourself: prefer the front camera.
    final front = _cameras.where(
      (c) => c.lensDirection == CameraLensDirection.front,
    );
    await _useCamera(front.isNotEmpty ? front.first : _cameras.first);
  }

  Future<void> _useCamera(CameraDescription camera) async {
    final previous = _controller;
    setState(() {
      _controller = null;
      _state = _RecordState.preparing;
    });
    await previous?.dispose();

    final controller = CameraController(
      camera,
      ResolutionPreset.high,
      enableAudio: false,
    );
    try {
      await controller.initialize();
      if (!mounted) {
        await controller.dispose();
        return;
      }
      setState(() {
        _controller = controller;
        _state = _RecordState.ready;
      });
    } catch (_) {
      await controller.dispose();
      if (mounted) setState(() => _state = _RecordState.error);
    }
  }

  void _switchCamera() {
    final current = _controller?.description;
    if (current == null || _cameras.length < 2) return;
    final next = _cameras[(_cameras.indexOf(current) + 1) % _cameras.length];
    _useCamera(next);
  }

  Future<void> _speak(String text) async {
    final settings = AppSettingsStore.settings.value;
    if (!settings.voiceFeedbackEnabled) return;
    try {
      await _tts.setLanguage(settings.ttsLanguage);
      await _tts.speak(text);
    } catch (_) {
      // Voice is optional; recording works without it.
    }
  }

  void _startCountdown() {
    setState(() {
      _state = _RecordState.countdown;
      _countdown = 3;
    });
    _speak('3');
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (_countdown <= 1) {
        timer.cancel();
        _startRecording();
        return;
      }
      setState(() => _countdown--);
      _speak('$_countdown');
    });
  }

  Future<void> _startRecording() async {
    final controller = _controller;
    if (controller == null) return;
    final l10n = context.l10n;
    try {
      await controller.startVideoRecording();
    } catch (_) {
      if (mounted) setState(() => _state = _RecordState.error);
      return;
    }
    _speak(l10n.recordGo);
    setState(() {
      _state = _RecordState.recording;
      _elapsed = Duration.zero;
    });
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      setState(() => _elapsed += const Duration(seconds: 1));
      if (_elapsed >= maxDuration) _stopRecording();
    });
  }

  Future<void> _stopRecording() async {
    _timer?.cancel();
    final controller = _controller;
    if (controller == null || !controller.value.isRecordingVideo) return;
    try {
      final file = await controller.stopVideoRecording();
      final bytes = await file.readAsBytes();
      if (!mounted) return;
      final name = file.name.isNotEmpty ? file.name : 'recording.mp4';
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(
          builder: (_) => AnalysisProgressPage(
            exercise: widget.exercise,
            videoBytes: bytes,
            fileName: name.contains('.') ? name : '$name.mp4',
          ),
        ),
      );
    } catch (_) {
      if (mounted) setState(() => _state = _RecordState.error);
    }
  }

  void _cancelCountdown() {
    _timer?.cancel();
    _tts.stop();
    setState(() => _state = _RecordState.ready);
  }

  @override
  void dispose() {
    _timer?.cancel();
    _tts.stop();
    _controller?.dispose();
    super.dispose();
  }

  String _format(Duration d) =>
      '${d.inMinutes.toString().padLeft(2, '0')}:${(d.inSeconds % 60).toString().padLeft(2, '0')}';

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final controller = _controller;

    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        foregroundColor: Colors.white,
        title: Text(l10n.recordTitle(widget.exercise.title(l10n))),
        actions: [
          if (_cameras.length > 1 && _state == _RecordState.ready)
            IconButton(
              onPressed: _switchCamera,
              tooltip: l10n.recordSwitchCamera,
              icon: const Icon(Icons.cameraswitch_rounded),
            ),
        ],
      ),
      body: SafeArea(
        top: false,
        child: _state == _RecordState.error
            ? _CameraError(onRetry: _initCameras)
            : Column(
                children: [
                  Expanded(
                    child: Stack(
                      fit: StackFit.expand,
                      children: [
                        if (controller != null &&
                            controller.value.isInitialized)
                          Center(
                            child: AspectRatio(
                              aspectRatio: 1 / controller.value.aspectRatio,
                              child: CameraPreview(controller),
                            ),
                          )
                        else
                          const Center(
                            child: CircularProgressIndicator(
                              color: Colors.white,
                            ),
                          ),
                        const IgnorePointer(child: _FramingGuide()),
                        if (_state == _RecordState.countdown)
                          Center(
                            child: Text(
                              '$_countdown',
                              style: context.text.displaySmall?.copyWith(
                                fontSize: 120,
                                color: Colors.white,
                              ),
                            ),
                          ),
                        if (_state == _RecordState.recording)
                          Positioned(
                            top: Gap.lg,
                            left: 0,
                            right: 0,
                            child: Center(
                              child: _RecordingBadge(
                                label:
                                    '${_format(_elapsed)} / ${_format(maxDuration)}',
                              ),
                            ),
                          ),
                      ],
                    ),
                  ),
                  _ControlBar(
                    state: _state,
                    hint: switch (_state) {
                      _RecordState.recording => l10n.recordRecordingHint,
                      _RecordState.countdown => l10n.recordGetReady,
                      _ => l10n.recordFramingHint,
                    },
                    onStart: _startCountdown,
                    onStop: _stopRecording,
                    onCancelCountdown: _cancelCountdown,
                  ),
                ],
              ),
      ),
    );
  }
}

/// Body outline showing where to stand.
class _FramingGuide extends StatelessWidget {
  const _FramingGuide();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: FractionallySizedBox(
        widthFactor: 0.6,
        heightFactor: 0.86,
        child: DecoratedBox(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(Radii.lg),
            border: Border.all(
              color: Colors.white.withValues(alpha: 0.55),
              width: 2,
            ),
          ),
        ),
      ),
    );
  }
}

class _RecordingBadge extends StatelessWidget {
  final String label;

  const _RecordingBadge({required this.label});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: Gap.md,
        vertical: Gap.xs + 2,
      ),
      decoration: BoxDecoration(
        color: Colors.black.withValues(alpha: 0.6),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(
            Icons.fiber_manual_record_rounded,
            color: Color(0xFFEF4444),
            size: 14,
          ),
          const SizedBox(width: Gap.xs + 2),
          Text(
            label,
            style: context.text.labelLarge?.copyWith(
              color: Colors.white,
              fontFeatures: const [FontFeature.tabularFigures()],
            ),
          ),
        ],
      ),
    );
  }
}

class _ControlBar extends StatelessWidget {
  final _RecordState state;
  final String hint;
  final VoidCallback onStart;
  final VoidCallback onStop;
  final VoidCallback onCancelCountdown;

  const _ControlBar({
    required this.state,
    required this.hint,
    required this.onStart,
    required this.onStop,
    required this.onCancelCountdown,
  });

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final recording = state == _RecordState.recording;
    final counting = state == _RecordState.countdown;

    return Padding(
      padding: const EdgeInsets.fromLTRB(Gap.page, Gap.lg, Gap.page, Gap.lg),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            hint,
            textAlign: TextAlign.center,
            style: context.text.bodyMedium?.copyWith(color: Colors.white70),
          ),
          const SizedBox(height: Gap.lg),
          Semantics(
            button: true,
            label: recording
                ? l10n.recordStop
                : counting
                ? l10n.commonCancel
                : l10n.recordStart,
            excludeSemantics: true,
            child: GestureDetector(
              onTap: state == _RecordState.ready
                  ? onStart
                  : recording
                  ? onStop
                  : counting
                  ? onCancelCountdown
                  : null,
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                width: 76,
                height: 76,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(color: Colors.white, width: 4),
                ),
                child: Center(
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 200),
                    width: recording ? 28 : 58,
                    height: recording ? 28 : 58,
                    decoration: BoxDecoration(
                      color: state == _RecordState.preparing
                          ? Colors.white24
                          : const Color(0xFFEF4444),
                      borderRadius: BorderRadius.circular(recording ? 6 : 29),
                    ),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _CameraError extends StatelessWidget {
  final VoidCallback onRetry;

  const _CameraError({required this.onRetry});

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(Gap.xl),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(
              Icons.videocam_off_rounded,
              color: Colors.white70,
              size: 48,
            ),
            const SizedBox(height: Gap.lg),
            Text(
              l10n.recordCameraError,
              textAlign: TextAlign.center,
              style: context.text.bodyLarge?.copyWith(color: Colors.white),
            ),
            const SizedBox(height: Gap.lg),
            FilledButton.tonal(
              onPressed: onRetry,
              child: Text(l10n.commonRetry),
            ),
          ],
        ),
      ),
    );
  }
}
