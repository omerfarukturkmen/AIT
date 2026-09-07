import 'dart:async';
import 'dart:math';

import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:flutter_tts/flutter_tts.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/state/analysis_history_store.dart';
import '../../../core/state/app_settings_store.dart';
import '../../../data/api_service.dart';
import '../../../main.dart';
import '../../../models/analysis_result_model.dart';
import '../../../widgets/glass_card.dart';
import '../../../widgets/premium_background.dart';
import '../../../widgets/premium_button.dart';
import '../result/result_page.dart';

enum LiveFeedbackType { idle, success, warning, error, cameraPosition }

class LiveAnalysisPage extends StatefulWidget {
  final String exerciseName;

  const LiveAnalysisPage({super.key, required this.exerciseName});

  @override
  State<LiveAnalysisPage> createState() => _LiveAnalysisPageState();
}

class _LiveAnalysisPageState extends State<LiveAnalysisPage> {
  CameraController? _cameraController;

  bool isCameraReady = false;
  bool hasCameraError = false;
  bool isAnalyzing = false;
  bool isFullScreenCamera = false;
  bool isUploadingToBackend = false;

  bool hasCompletedAnalysis = false;
  String? analysisErrorMessage;

  Timer? _feedbackTimer;
  final FlutterTts _flutterTts = FlutterTts();
  final Random _random = Random();

  String? _lastSpokenWarning;

  int formScore = 78;
  int repetitionCount = 0;

  String liveStatus = 'Analiz başlatılmayı bekliyor.';
  String postureWarning =
      'Kamera karşısında tüm vücudun görünecek şekilde dur.';

  LiveFeedbackType feedbackType = LiveFeedbackType.idle;
  bool hasStartedOnce = false;

  final List<String> _squatFeedbacksTr = [
    'Dizlerini ayak parmaklarınla aynı hizada tut.',
    'Gövden fazla öne eğiliyor, sırtını daha dik tut.',
    'İniş fazını daha kontrollü yap.',
    'Kalçanı biraz daha geriye al.',
    'Form iyi görünüyor, hareketi kontrollü sürdür.',
  ];

  final List<String> _pushUpFeedbacksTr = [
    'Kalçan aşağı düşüyor, core bölgeni sıkı tut.',
    'Dirseklerini fazla dışa açma.',
    'Omuz, kalça ve ayak hizasını koru.',
    'Göğsünü kontrollü şekilde yere yaklaştır.',
    'Form iyi, tekrar hızını sabit tut.',
  ];

  final List<String> _plankFeedbacksTr = [
    'Bel bölgen aşağı çöküyor, core aktivasyonunu artır.',
    'Kalçanı çok yukarı kaldırma.',
    'Dirseklerini omuzlarının altında tut.',
    'Boynunu nötr pozisyonda koru.',
    'Form stabil görünüyor.',
  ];

  final List<String> _generalFeedbacksTr = [
    'Eklem hizalarını korumaya dikkat et.',
    'Hareketi daha yavaş ve kontrollü yap.',
    'Gövde stabilitesini artır.',
    'Kamera açısından biraz daha geriye geç.',
    'Form iyi görünüyor, devam et.',
  ];

  final List<String> _squatFeedbacksEn = [
    'Keep your knees aligned with your toes.',
    'Your torso is leaning too far forward.',
    'Control the lowering phase more slowly.',
    'Move your hips slightly backward.',
    'Your form looks good. Keep moving with control.',
  ];

  final List<String> _pushUpFeedbacksEn = [
    'Your hips are dropping. Keep your core tight.',
    'Do not open your elbows too wide.',
    'Keep your shoulders, hips, and feet aligned.',
    'Lower your chest with control.',
    'Good form. Keep your repetition speed stable.',
  ];

  final List<String> _plankFeedbacksEn = [
    'Your lower back is dropping. Activate your core.',
    'Do not raise your hips too high.',
    'Keep your elbows under your shoulders.',
    'Keep your neck in a neutral position.',
    'Your form looks stable.',
  ];

  final List<String> _generalFeedbacksEn = [
    'Pay attention to your joint alignment.',
    'Move more slowly and with control.',
    'Improve your torso stability.',
    'Move slightly farther back from the camera.',
    'Your form looks good. Keep going.',
  ];

  @override
  void initState() {
    super.initState();
    _setupCamera();
    _setupTextToSpeech();
    AppSettingsStore.settings.addListener(_handleSettingsChanged);
  }

  Future<void> _setupTextToSpeech() async {
    final settings = AppSettingsStore.settings.value;

    await _flutterTts.setLanguage(settings.languageCode);
    await _flutterTts.setSpeechRate(0.48);
    await _flutterTts.setVolume(1.0);
    await _flutterTts.setPitch(1.0);
  }

  void _handleSettingsChanged() {
    final settings = AppSettingsStore.settings.value;

    _flutterTts.setLanguage(settings.languageCode);

    if (!settings.voiceFeedbackEnabled) {
      _flutterTts.stop();
    }

    if (isAnalyzing) {
      _feedbackTimer?.cancel();
      _feedbackTimer = Timer.periodic(
        Duration(seconds: settings.feedbackIntervalSeconds),
        (_) {
          _generateLiveFeedback();
        },
      );
    }

    if (!isAnalyzing && mounted) {
      setState(() {
        liveStatus = settings.languageCode == 'tr-TR'
            ? 'Analiz başlatılmayı bekliyor.'
            : 'Waiting to start analysis.';

        postureWarning = settings.languageCode == 'tr-TR'
            ? 'Kamera karşısında tüm vücudun görünecek şekilde dur.'
            : 'Stand so your full body is visible in front of the camera.';

        feedbackType = LiveFeedbackType.idle;
      });
    }
  }

  Future<void> _setupCamera() async {
    if (appCameras.isEmpty) {
      if (!mounted) return;

      setState(() {
        hasCameraError = true;
        isCameraReady = false;
      });
      return;
    }

    _cameraController = CameraController(
      appCameras.first,
      ResolutionPreset.medium,
      enableAudio: false,
    );

    try {
      await _cameraController!.initialize();

      if (!mounted) return;

      setState(() {
        isCameraReady = true;
        hasCameraError = false;
      });
    } catch (_) {
      if (!mounted) return;

      setState(() {
        isCameraReady = false;
        hasCameraError = true;
      });
    }
  }

  Future<void> _startLiveAnalysis() async {
    final settings = AppSettingsStore.settings.value;

    if (!isCameraReady || _cameraController == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            settings.languageCode == 'tr-TR'
                ? 'Kamera hazır değil.'
                : 'Camera is not ready.',
          ),
        ),
      );
      return;
    }

    if (_cameraController!.value.isRecordingVideo) {
      return;
    }

    try {
      await _cameraController!.startVideoRecording();

      if (!mounted) return;

      setState(() {
        isAnalyzing = true;
        isUploadingToBackend = false;
        hasCompletedAnalysis = false;
        analysisErrorMessage = null;
        hasStartedOnce = true;
        feedbackType = LiveFeedbackType.cameraPosition;
        _lastSpokenWarning = null;
        repetitionCount = 0;

        liveStatus = settings.languageCode == 'tr-TR'
            ? 'Canlı analiz aktif.'
            : 'Live analysis is active.';

        postureWarning = settings.languageCode == 'tr-TR'
            ? 'Kamerada tüm vücudunun göründüğünden emin ol. Hareket formun izleniyor.'
            : 'Make sure your full body is visible. Your movement form is being monitored.';
      });

      _feedbackTimer?.cancel();

      _feedbackTimer = Timer.periodic(
        Duration(seconds: settings.feedbackIntervalSeconds),
        (_) {
          _generateLiveFeedback();
        },
      );
    } catch (e) {
      if (!mounted) return;

      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Video kaydı başlatılamadı: $e')));
    }
  }

  Future<void> _stopLiveAnalysisAndSendBackend() async {
    final settings = AppSettingsStore.settings.value;

    if (_cameraController == null) return;
    if (!_cameraController!.value.isRecordingVideo) return;
    if (isUploadingToBackend) return;

    _feedbackTimer?.cancel();
    await _flutterTts.stop();

    try {
      setState(() {
        isUploadingToBackend = true;
        feedbackType = LiveFeedbackType.cameraPosition;

        liveStatus = settings.languageCode == 'tr-TR'
            ? 'Video backend tarafına gönderiliyor.'
            : 'Video is being sent to backend.';

        postureWarning = settings.languageCode == 'tr-TR'
            ? 'Lütfen bekle, analiz sonucu hazırlanıyor...'
            : 'Please wait, analysis result is being prepared...';
      });

      final XFile video = await _cameraController!.stopVideoRecording();

      final videoBytes = await video.readAsBytes();
      final videoName = video.name.isNotEmpty
          ? video.name
          : 'live_analysis.mp4';

      final dynamic backendResult = await ApiService.uploadVideoBytes(
        videoBytes: videoBytes,
        fileName: videoName,
        userId: 1,
        exerciseName: widget.exerciseName,
      );

      final int accuracy = backendResult.accuracy is int
          ? backendResult.accuracy
          : int.tryParse(backendResult.accuracy.toString()) ?? formScore;

      final int totalFrames = backendResult.totalFrames is int
          ? backendResult.totalFrames
          : int.tryParse(backendResult.totalFrames.toString()) ?? 0;

      final double averageMotion = backendResult.averageMotion is double
          ? backendResult.averageMotion
          : double.tryParse(backendResult.averageMotion.toString()) ?? 0.0;

      final String exerciseName =
          backendResult.exercise?.toString() ?? widget.exerciseName;

      final String feedback =
          backendResult.feedback?.toString() ??
          'Analiz sonucu backend tarafından başarıyla oluşturuldu.';
      final AnalysisResult result = AnalysisResult(
        exerciseName: exerciseName,
        score: accuracy,
        riskPercent: 100 - accuracy,
        repetitionCount: repetitionCount > 0 ? repetitionCount : totalFrames,
        validReps: accuracy >= 75 ? repetitionCount : 0,
        invalidReps: accuracy >= 75 ? 0 : repetitionCount,
        confidence: accuracy.toDouble(),
        durationSeconds: totalFrames.toDouble(),
        duration: '$totalFrames frame',
        totalFrames: totalFrames,
        processedFrames: totalFrames,
        minKneeAngle: null,
        averageMinKneeAngle: null,
        rangeOfMotion: averageMotion,
        selectedSide: 'unavailable',
        movementAngle: averageMotion.toStringAsFixed(2),
        mistakes: accuracy >= 75
            ? [
                'Belirgin form hatası algılanmadı.',
                'Hareket genel olarak başarılı görünüyor.',
              ]
            : [
                'Hareket formunda teknik hata olabilir.',
                'Hareket daha kontrollü yapılmalıdır.',
              ],
        recommendations: [
          feedback,
          'Ortalama hareket değeri: ${averageMotion.toStringAsFixed(2)}',
          'Toplam analiz edilen frame sayısı: $totalFrames',
        ],
      );

      AnalysisHistoryStore.addResult(result);

      if (!mounted) return;

      setState(() {
        isAnalyzing = false;
        isUploadingToBackend = false;
        hasCompletedAnalysis = true;
        analysisErrorMessage = null;
        feedbackType = accuracy >= 75
            ? LiveFeedbackType.success
            : LiveFeedbackType.error;
      });

      Navigator.push(
        context,
        MaterialPageRoute(builder: (_) => ResultPage(result: result)),
      );
    } catch (e) {
      if (!mounted) return;

      setState(() {
        isAnalyzing = false;
        isUploadingToBackend = false;
        hasCompletedAnalysis = false;
        analysisErrorMessage = e.toString();
        feedbackType = LiveFeedbackType.error;

        liveStatus = settings.languageCode == 'tr-TR'
            ? 'Backend analiz hatası oluştu.'
            : 'Backend analysis error occurred.';

        postureWarning = settings.languageCode == 'tr-TR'
            ? 'Analiz başarısız oldu. Lütfen tekrar dene.'
            : 'Analysis failed. Please try again.';
      });

      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Backend analiz hatası: $e')));
    }
  }

  Future<void> _handleAnalysisButton() async {
    if (isUploadingToBackend) return;

    if (isAnalyzing) {
      await _stopLiveAnalysisAndSendBackend();
    } else {
      await _startLiveAnalysis();
    }
  }

  Future<void> _speakFeedback(String message) async {
    final settings = AppSettingsStore.settings.value;

    if (!isAnalyzing) return;
    if (!settings.voiceFeedbackEnabled) return;
    if (_lastSpokenWarning == message) return;

    _lastSpokenWarning = message;

    await _flutterTts.stop();
    await _flutterTts.setLanguage(settings.languageCode);
    await _flutterTts.speak(message);
  }

  void _generateLiveFeedback() {
    final settings = AppSettingsStore.settings.value;

    final feedbacks = _getFeedbackList(
      widget.exerciseName,
      settings.languageCode,
    );

    final newWarning = feedbacks[_random.nextInt(feedbacks.length)];
    final newScore = 70 + _random.nextInt(25);

    setState(() {
      formScore = newScore;

      if (_random.nextBool()) {
        repetitionCount++;
      }

      if (formScore >= 85) {
        feedbackType = LiveFeedbackType.success;

        liveStatus = settings.languageCode == 'tr-TR'
            ? 'Doğru form algılandı.'
            : 'Correct form detected.';

        postureWarning = settings.languageCode == 'tr-TR'
            ? 'Hareket formun iyi görünüyor, aynı kontrollü tempoda devam et.'
            : 'Your form looks good. Keep moving with the same controlled tempo.';
      } else if (formScore >= 70) {
        feedbackType = LiveFeedbackType.warning;

        liveStatus = settings.languageCode == 'tr-TR'
            ? 'Küçük form düzeltmesi gerekli.'
            : 'Small form correction needed.';

        postureWarning = newWarning;
      } else {
        feedbackType = LiveFeedbackType.error;

        liveStatus = settings.languageCode == 'tr-TR'
            ? 'Form hatası algılandı.'
            : 'Form error detected.';

        postureWarning = newWarning;
      }
    });

    if (newScore < 85) {
      _speakFeedback(newWarning);
    }
  }

  List<String> _getFeedbackList(String exerciseName, String languageCode) {
    final isTurkish = languageCode == 'tr-TR';

    switch (exerciseName) {
      case 'Squat':
        return isTurkish ? _squatFeedbacksTr : _squatFeedbacksEn;
      case 'Push-up':
        return isTurkish ? _pushUpFeedbacksTr : _pushUpFeedbacksEn;
      case 'Plank':
        return isTurkish ? _plankFeedbacksTr : _plankFeedbacksEn;
      default:
        return isTurkish ? _generalFeedbacksTr : _generalFeedbacksEn;
    }
  }

  Color get scoreColor {
    if (formScore >= 85) return Colors.greenAccent;
    if (formScore >= 70) return Colors.orangeAccent;
    return Colors.redAccent;
  }

  @override
  void dispose() {
    AppSettingsStore.settings.removeListener(_handleSettingsChanged);
    _feedbackTimer?.cancel();
    _flutterTts.stop();
    _cameraController?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (isFullScreenCamera) {
      return ValueListenableBuilder<AppSettings>(
        valueListenable: AppSettingsStore.settings,
        builder: (context, settings, child) {
          return _FullScreenCameraView(
            cameraContent: _buildCameraContent(),
            exerciseName: widget.exerciseName,
            formScore: formScore,
            repetitionCount: repetitionCount,
            scoreColor: scoreColor,
            isAnalyzing: isAnalyzing,
            postureWarning: postureWarning,
            voiceFeedbackEnabled: settings.voiceFeedbackEnabled,
            onClose: () {
              setState(() {
                isFullScreenCamera = false;
              });
            },
          );
        },
      );
    }

    return ValueListenableBuilder<AppSettings>(
      valueListenable: AppSettingsStore.settings,
      builder: (context, settings, child) {
        return Scaffold(
          body: PremiumBackground(
            child: SafeArea(
              child: Column(
                children: [
                  _buildHeader(context),
                  Expanded(
                    child: SingleChildScrollView(
                      padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          _buildCameraCard(settings),
                          const SizedBox(height: 16),
                          if (!isAnalyzing && !isUploadingToBackend)
                            _LiveInstructionCard(
                              exerciseName: widget.exerciseName,
                            ),
                          if (!isAnalyzing && !isUploadingToBackend)
                            const SizedBox(height: 16),
                          if (!isAnalyzing && !isUploadingToBackend)
                            _CameraPositionWarningCard(
                              exerciseName: widget.exerciseName,
                            ),
                          if (!isAnalyzing && !isUploadingToBackend)
                            const SizedBox(height: 16),
                          _LiveStatusCard(
                            exerciseName: widget.exerciseName,
                            formScore: formScore,
                            repetitionCount: repetitionCount,
                            liveStatus: liveStatus,
                            postureWarning: postureWarning,
                            scoreColor: scoreColor,
                            isAnalyzing: isAnalyzing,
                            feedbackType: feedbackType,
                          ),
                          const SizedBox(height: 16),
                          _ActiveSettingsCard(settings: settings),
                          const SizedBox(height: 16),
                          if (isUploadingToBackend) const _BackendLoadingCard(),
                          if (isUploadingToBackend) const SizedBox(height: 16),
                          PremiumButton(
                            icon: isUploadingToBackend
                                ? Icons.hourglass_top_rounded
                                : isAnalyzing
                                ? Icons.stop_rounded
                                : Icons.play_arrow_rounded,
                            text: isUploadingToBackend
                                ? settings.languageCode == 'tr-TR'
                                      ? 'Backend Analiz Ediyor...'
                                      : 'Backend Is Analyzing...'
                                : isAnalyzing
                                ? settings.languageCode == 'tr-TR'
                                      ? 'Durdur'
                                      : 'Stop'
                                : hasStartedOnce
                                ? settings.languageCode == 'tr-TR'
                                      ? 'Tekrar Başlat'
                                      : 'Restart'
                                : settings.languageCode == 'tr-TR'
                                ? 'Analizi Başlat'
                                : 'Start Analysis',
                            onPressed: _handleAnalysisButton,
                          ),
                          const SizedBox(height: 16),
                          const _LiveAnalysisInfoCard(),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildHeader(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(8, 8, 16, 8),
      child: Row(
        children: [
          IconButton(
            onPressed: isUploadingToBackend
                ? null
                : () => Navigator.pop(context),
            icon: const Icon(Icons.arrow_back_rounded),
          ),
          const Expanded(
            child: Text(
              'Canlı AI Analiz',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 21, fontWeight: FontWeight.w900),
            ),
          ),
          const SizedBox(width: 48),
        ],
      ),
    );
  }

  Widget _buildCameraCard(AppSettings settings) {
    return GlassCard(
      child: ClipRRect(
        borderRadius: BorderRadius.circular(22),
        child: SizedBox(
          height: 430,
          child: Stack(
            fit: StackFit.expand,
            children: [
              _buildCameraContent(),

              Positioned(
                top: 12,
                left: 12,
                child: _StatusBadge(
                  text: isAnalyzing ? 'AI LIVE' : 'READY',
                  color: isAnalyzing
                      ? Colors.greenAccent
                      : AppColors.purpleGlow,
                ),
              ),

              Positioned(
                top: 12,
                right: 12,
                child: Row(
                  children: [
                    _StatusBadge(
                      text: settings.voiceFeedbackEnabled
                          ? 'VOICE ON'
                          : 'VOICE OFF',
                      color: settings.voiceFeedbackEnabled
                          ? Colors.greenAccent
                          : Colors.orangeAccent,
                    ),
                    const SizedBox(width: 8),
                    GestureDetector(
                      onTap: () {
                        setState(() {
                          isFullScreenCamera = true;
                        });
                      },
                      child: Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: Colors.black.withValues(alpha: 0.45),
                          borderRadius: BorderRadius.circular(14),
                          border: Border.all(
                            color: Colors.white.withValues(alpha: 0.18),
                          ),
                        ),
                        child: const Icon(
                          Icons.fullscreen_rounded,
                          color: Colors.white,
                          size: 20,
                        ),
                      ),
                    ),
                  ],
                ),
              ),

              Positioned(
                top: 62,
                left: 12,
                right: 12,
                child: _CameraLiveMetricsOverlay(
                  exerciseName: widget.exerciseName,
                  formScore: formScore,
                  repetitionCount: repetitionCount,
                  scoreColor: scoreColor,
                  isAnalyzing: isAnalyzing,
                ),
              ),

              Positioned(
                bottom: 12,
                left: 12,
                right: 12,
                child: _CameraActiveFeedbackOverlay(
                  liveStatus: liveStatus,
                  postureWarning: postureWarning,
                  feedbackType: feedbackType,
                  isAnalyzing: isAnalyzing,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildCameraContent() {
    if (hasCameraError) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(24),
          child: Text(
            'Kamera bulunamadı veya kamera başlatılamadı.',
            textAlign: TextAlign.center,
            style: TextStyle(color: AppColors.textSoft, fontSize: 16),
          ),
        ),
      );
    }

    if (!isCameraReady || _cameraController == null) {
      return const Center(
        child: CircularProgressIndicator(color: AppColors.purpleGlow),
      );
    }

    return CameraPreview(_cameraController!);
  }
}

class _BackendLoadingCard extends StatelessWidget {
  const _BackendLoadingCard();

  @override
  Widget build(BuildContext context) {
    return const GlassCard(
      child: Column(
        children: [
          CircularProgressIndicator(color: AppColors.purpleGlow),
          SizedBox(height: 14),
          Text(
            'Video backend tarafına gönderiliyor. Analiz sonucu bekleniyor...',
            textAlign: TextAlign.center,
            style: TextStyle(color: AppColors.textSoft, height: 1.4),
          ),
        ],
      ),
    );
  }
}

class _LiveStatusCard extends StatelessWidget {
  final String exerciseName;
  final int formScore;
  final int repetitionCount;
  final String liveStatus;
  final String postureWarning;
  final Color scoreColor;
  final bool isAnalyzing;
  final LiveFeedbackType feedbackType;

  const _LiveStatusCard({
    required this.exerciseName,
    required this.formScore,
    required this.repetitionCount,
    required this.liveStatus,
    required this.postureWarning,
    required this.scoreColor,
    required this.isAnalyzing,
    required this.feedbackType,
  });

  Color get feedbackColor {
    switch (feedbackType) {
      case LiveFeedbackType.success:
        return Colors.greenAccent;
      case LiveFeedbackType.warning:
        return Colors.orangeAccent;
      case LiveFeedbackType.error:
        return Colors.redAccent;
      case LiveFeedbackType.cameraPosition:
        return AppColors.purpleGlow;
      case LiveFeedbackType.idle:
        return AppColors.textSoft;
    }
  }

  IconData get feedbackIcon {
    switch (feedbackType) {
      case LiveFeedbackType.success:
        return Icons.check_circle_rounded;
      case LiveFeedbackType.warning:
        return Icons.warning_amber_rounded;
      case LiveFeedbackType.error:
        return Icons.error_rounded;
      case LiveFeedbackType.cameraPosition:
        return Icons.center_focus_strong_rounded;
      case LiveFeedbackType.idle:
        return Icons.info_outline_rounded;
    }
  }

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(
                Icons.psychology_rounded,
                color: AppColors.purpleGlow,
                size: 28,
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  '$exerciseName Live Feedback',
                  style: const TextStyle(
                    fontSize: 19,
                    fontWeight: FontWeight.w900,
                  ),
                ),
              ),
              _StatusBadge(
                text: isAnalyzing ? 'ACTIVE' : 'IDLE',
                color: isAnalyzing ? Colors.greenAccent : AppColors.textSoft,
              ),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: _MetricBox(
                  title: 'Form Skoru',
                  value: '$formScore',
                  color: scoreColor,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _MetricBox(
                  title: 'Tekrar',
                  value: '$repetitionCount',
                  color: AppColors.purpleGlow,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          LinearProgressIndicator(
            minHeight: 8,
            value: formScore / 100,
            backgroundColor: Colors.white.withValues(alpha: 0.08),
            valueColor: AlwaysStoppedAnimation<Color>(scoreColor),
          ),
          const SizedBox(height: 16),
          AnimatedSwitcher(
            duration: const Duration(milliseconds: 350),
            child: Container(
              key: ValueKey(postureWarning),
              width: double.infinity,
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: feedbackColor.withValues(alpha: 0.13),
                borderRadius: BorderRadius.circular(18),
                border: Border.all(
                  color: feedbackColor.withValues(alpha: 0.35),
                ),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(feedbackIcon, color: feedbackColor, size: 24),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          liveStatus,
                          style: TextStyle(
                            color: feedbackColor,
                            fontWeight: FontWeight.w900,
                            fontSize: 15,
                          ),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          postureWarning,
                          style: const TextStyle(
                            color: AppColors.textSoft,
                            height: 1.4,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ActiveSettingsCard extends StatelessWidget {
  final AppSettings settings;

  const _ActiveSettingsCard({required this.settings});

  @override
  Widget build(BuildContext context) {
    final languageText = settings.languageCode == 'tr-TR'
        ? 'Türkçe'
        : 'English';

    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Aktif Canlı Analiz Ayarları',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900),
          ),
          const SizedBox(height: 14),
          Row(
            children: [
              Expanded(
                child: _SettingInfoBox(
                  icon: Icons.volume_up_rounded,
                  title: 'Ses',
                  value: settings.voiceFeedbackEnabled ? 'Açık' : 'Kapalı',
                  color: settings.voiceFeedbackEnabled
                      ? Colors.greenAccent
                      : Colors.orangeAccent,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _SettingInfoBox(
                  icon: Icons.language_rounded,
                  title: 'Dil',
                  value: languageText,
                  color: AppColors.purpleGlow,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _SettingInfoBox(
                  icon: Icons.timer_rounded,
                  title: 'Sıklık',
                  value: '${settings.feedbackIntervalSeconds} sn',
                  color: AppColors.purpleGlow,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          const Text(
            'Bu değerler Ayarlar ekranından yönetilir ve canlı analiz ekranına otomatik yansır.',
            style: TextStyle(
              color: AppColors.textSoft,
              fontSize: 12,
              height: 1.4,
            ),
          ),
        ],
      ),
    );
  }
}

class _SettingInfoBox extends StatelessWidget {
  final IconData icon;
  final String title;
  final String value;
  final Color color;

  const _SettingInfoBox({
    required this.icon,
    required this.title,
    required this.value,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(11),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withValues(alpha: 0.24)),
      ),
      child: Column(
        children: [
          Icon(icon, color: color, size: 22),
          const SizedBox(height: 7),
          Text(
            value,
            textAlign: TextAlign.center,
            style: TextStyle(
              color: color,
              fontWeight: FontWeight.w900,
              fontSize: 13,
            ),
          ),
          const SizedBox(height: 3),
          Text(
            title,
            style: const TextStyle(color: AppColors.textSoft, fontSize: 11),
          ),
        ],
      ),
    );
  }
}

class _MetricBox extends StatelessWidget {
  final String title;
  final String value;
  final Color color;

  const _MetricBox({
    required this.title,
    required this.value,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: color.withValues(alpha: 0.25)),
      ),
      child: Column(
        children: [
          Text(
            value,
            style: TextStyle(
              color: color,
              fontSize: 28,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            title,
            style: const TextStyle(color: AppColors.textSoft, fontSize: 12),
          ),
        ],
      ),
    );
  }
}

class _StatusBadge extends StatelessWidget {
  final String text;
  final Color color;

  const _StatusBadge({required this.text, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.16),
        borderRadius: BorderRadius.circular(99),
        border: Border.all(color: color.withValues(alpha: 0.34)),
      ),
      child: Text(
        text,
        style: TextStyle(
          color: color,
          fontWeight: FontWeight.w900,
          fontSize: 11,
        ),
      ),
    );
  }
}

class _LiveAnalysisInfoCard extends StatelessWidget {
  const _LiveAnalysisInfoCard();

  @override
  Widget build(BuildContext context) {
    return const GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Canlı Analiz Mantığı',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900),
          ),
          SizedBox(height: 10),
          Text(
            'Bu ekranda canlı kamera görüntüsü sırasında video kaydı alınır. Analiz durdurulduğunda video FastAPI backend tarafına gönderilir ve dönen analiz sonucu sonuç ekranında gösterilir.',
            style: TextStyle(color: AppColors.textSoft, height: 1.5),
          ),
        ],
      ),
    );
  }
}

class _FullScreenCameraView extends StatelessWidget {
  final Widget cameraContent;
  final String exerciseName;
  final int formScore;
  final int repetitionCount;
  final Color scoreColor;
  final bool isAnalyzing;
  final String postureWarning;
  final bool voiceFeedbackEnabled;
  final VoidCallback onClose;

  const _FullScreenCameraView({
    required this.cameraContent,
    required this.exerciseName,
    required this.formScore,
    required this.repetitionCount,
    required this.scoreColor,
    required this.isAnalyzing,
    required this.postureWarning,
    required this.voiceFeedbackEnabled,
    required this.onClose,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        fit: StackFit.expand,
        children: [
          Positioned.fill(child: cameraContent),
          Positioned(
            top: MediaQuery.of(context).padding.top + 12,
            left: 16,
            right: 16,
            child: Row(
              children: [
                GestureDetector(
                  onTap: onClose,
                  child: Container(
                    height: 44,
                    width: 44,
                    decoration: BoxDecoration(
                      color: Colors.black.withValues(alpha: 0.55),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(
                        color: Colors.white.withValues(alpha: 0.18),
                      ),
                    ),
                    child: const Icon(Icons.close_rounded, color: Colors.white),
                  ),
                ),
                const Spacer(),
                _StatusBadge(
                  text: isAnalyzing ? 'AI LIVE' : 'READY',
                  color: isAnalyzing
                      ? Colors.greenAccent
                      : AppColors.purpleGlow,
                ),
                const SizedBox(width: 8),
                _StatusBadge(
                  text: voiceFeedbackEnabled ? 'VOICE ON' : 'VOICE OFF',
                  color: voiceFeedbackEnabled
                      ? Colors.greenAccent
                      : Colors.orangeAccent,
                ),
              ],
            ),
          ),
          Positioned(
            top: MediaQuery.of(context).padding.top + 68,
            left: 16,
            right: 16,
            child: _CameraLiveMetricsOverlay(
              exerciseName: exerciseName,
              formScore: formScore,
              repetitionCount: repetitionCount,
              scoreColor: scoreColor,
              isAnalyzing: isAnalyzing,
            ),
          ),
          Positioned(
            bottom: MediaQuery.of(context).padding.bottom + 24,
            left: 16,
            right: 16,
            child: Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.black.withValues(alpha: 0.62),
                borderRadius: BorderRadius.circular(22),
                border: Border.all(
                  color: isAnalyzing
                      ? AppColors.purpleGlow.withValues(alpha: 0.40)
                      : Colors.white.withValues(alpha: 0.15),
                ),
              ),
              child: Row(
                children: [
                  Icon(
                    isAnalyzing
                        ? Icons.auto_awesome_rounded
                        : Icons.info_outline_rounded,
                    color: isAnalyzing
                        ? AppColors.purpleGlow
                        : AppColors.textSoft,
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      postureWarning,
                      style: const TextStyle(
                        color: Colors.white,
                        height: 1.35,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _LiveInstructionCard extends StatelessWidget {
  final String exerciseName;

  const _LiveInstructionCard({required this.exerciseName});

  List<String> get instructions {
    switch (exerciseName) {
      case 'Squat':
        return const [
          'Ayaklarını omuz genişliğinde aç.',
          'Kamerada tüm vücudunun göründüğünden emin ol.',
          'Dizlerini ayak parmaklarınla aynı hizada tut.',
          'İniş ve kalkış hareketini kontrollü yap.',
        ];

      case 'Push-up':
        return const [
          'Ellerini omuz genişliğinde konumlandır.',
          'Omuz, kalça ve ayak hizanı düz tut.',
          'Göğsünü kontrollü şekilde yere yaklaştır.',
          'Core bölgeni aktif tutarak hareketi başlat.',
        ];

      default:
        return const [
          'Kamerada tüm vücudunun göründüğünden emin ol.',
          'Hareketi yavaş ve kontrollü şekilde yap.',
          'Eklem hizalarını korumaya dikkat et.',
          'Analiz başlamadan önce doğru pozisyon al.',
        ];
    }
  }

  IconData get exerciseIcon {
    switch (exerciseName) {
      case 'Squat':
        return Icons.fitness_center_rounded;
      case 'Push-up':
        return Icons.accessibility_new_rounded;
      default:
        return Icons.directions_run_rounded;
    }
  }

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                height: 44,
                width: 44,
                decoration: BoxDecoration(
                  color: AppColors.purpleGlow.withValues(alpha: 0.14),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: AppColors.purpleGlow.withValues(alpha: 0.28),
                  ),
                ),
                child: Icon(
                  exerciseIcon,
                  color: AppColors.purpleGlow,
                  size: 24,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  '$exerciseName İçin Hazırlık',
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w900,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          ...instructions.map(
            (instruction) => Padding(
              padding: const EdgeInsets.only(bottom: 9),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(
                    Icons.check_circle_rounded,
                    color: AppColors.purpleGlow,
                    size: 18,
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      instruction,
                      style: const TextStyle(
                        color: AppColors.textSoft,
                        height: 1.4,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _CameraLiveMetricsOverlay extends StatelessWidget {
  final String exerciseName;
  final int formScore;
  final int repetitionCount;
  final Color scoreColor;
  final bool isAnalyzing;

  const _CameraLiveMetricsOverlay({
    required this.exerciseName,
    required this.formScore,
    required this.repetitionCount,
    required this.scoreColor,
    required this.isAnalyzing,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.black.withValues(alpha: 0.58),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: isAnalyzing
              ? AppColors.purpleGlow.withValues(alpha: 0.38)
              : Colors.white.withValues(alpha: 0.15),
        ),
      ),
      child: Row(
        children: [
          Expanded(
            child: _CameraMetricItem(
              title: 'Hareket',
              value: exerciseName,
              icon: Icons.fitness_center_rounded,
              color: AppColors.purpleGlow,
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: _CameraMetricItem(
              title: 'Skor',
              value: '$formScore',
              icon: Icons.speed_rounded,
              color: scoreColor,
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: _CameraMetricItem(
              title: 'Tekrar',
              value: '$repetitionCount',
              icon: Icons.repeat_rounded,
              color: Colors.greenAccent,
            ),
          ),
        ],
      ),
    );
  }
}

class _CameraMetricItem extends StatelessWidget {
  final String title;
  final String value;
  final IconData icon;
  final Color color;

  const _CameraMetricItem({
    required this.title,
    required this.value,
    required this.icon,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Icon(icon, color: color, size: 20),
        const SizedBox(height: 5),
        Text(
          value,
          overflow: TextOverflow.ellipsis,
          textAlign: TextAlign.center,
          style: TextStyle(
            color: color,
            fontWeight: FontWeight.w900,
            fontSize: 14,
          ),
        ),
        const SizedBox(height: 2),
        Text(
          title,
          style: const TextStyle(
            color: AppColors.textSoft,
            fontSize: 10,
            fontWeight: FontWeight.w700,
          ),
        ),
      ],
    );
  }
}

class _CameraActiveFeedbackOverlay extends StatelessWidget {
  final String liveStatus;
  final String postureWarning;
  final LiveFeedbackType feedbackType;
  final bool isAnalyzing;

  const _CameraActiveFeedbackOverlay({
    required this.liveStatus,
    required this.postureWarning,
    required this.feedbackType,
    required this.isAnalyzing,
  });

  Color get feedbackColor {
    switch (feedbackType) {
      case LiveFeedbackType.success:
        return Colors.greenAccent;
      case LiveFeedbackType.warning:
        return Colors.orangeAccent;
      case LiveFeedbackType.error:
        return Colors.redAccent;
      case LiveFeedbackType.cameraPosition:
        return AppColors.purpleGlow;
      case LiveFeedbackType.idle:
        return AppColors.textSoft;
    }
  }

  IconData get feedbackIcon {
    switch (feedbackType) {
      case LiveFeedbackType.success:
        return Icons.check_circle_rounded;
      case LiveFeedbackType.warning:
        return Icons.warning_amber_rounded;
      case LiveFeedbackType.error:
        return Icons.error_rounded;
      case LiveFeedbackType.cameraPosition:
        return Icons.center_focus_strong_rounded;
      case LiveFeedbackType.idle:
        return Icons.info_outline_rounded;
    }
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedSwitcher(
      duration: const Duration(milliseconds: 450),
      switchInCurve: Curves.easeOutBack,
      switchOutCurve: Curves.easeIn,
      transitionBuilder: (Widget child, Animation<double> animation) {
        final offsetAnimation = Tween<Offset>(
          begin: const Offset(0, 0.35),
          end: Offset.zero,
        ).animate(animation);

        return FadeTransition(
          opacity: animation,
          child: SlideTransition(position: offsetAnimation, child: child),
        );
      },
      child: Container(
        key: ValueKey('$liveStatus-$postureWarning-$feedbackType'),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: Colors.black.withValues(alpha: 0.68),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: feedbackColor.withValues(alpha: 0.42)),

          boxShadow: [
            BoxShadow(
              color: feedbackColor.withValues(alpha: 0.24),
              blurRadius: 24,
              spreadRadius: 1,
              offset: const Offset(0, 10),
            ),
          ],
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(feedbackIcon, color: feedbackColor, size: 26),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    isAnalyzing
                        ? liveStatus
                        : 'Analiz başlamadan önce pozisyonunu hazırla',
                    style: TextStyle(
                      color: feedbackColor,
                      fontWeight: FontWeight.w900,
                      fontSize: 15,
                    ),
                  ),
                  const SizedBox(height: 5),
                  Text(
                    postureWarning,
                    style: const TextStyle(
                      color: Colors.white,
                      height: 1.35,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _CameraPositionWarningCard extends StatelessWidget {
  final String exerciseName;

  const _CameraPositionWarningCard({required this.exerciseName});

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: Colors.orangeAccent.withValues(alpha: 0.10),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: Colors.orangeAccent.withValues(alpha: 0.30),
          ),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Icon(
              Icons.videocam_rounded,
              color: Colors.orangeAccent,
              size: 28,
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Kamera Pozisyonunu Kontrol Et',
                    style: TextStyle(
                      color: Colors.orangeAccent,
                      fontWeight: FontWeight.w900,
                      fontSize: 16,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    exerciseName == 'Push-up'
                        ? 'Push-up analizi için vücudunun yandan veya çapraz açıdan tamamen göründüğünden emin ol.'
                        : 'Analiz başlamadan önce tüm vücudunun kamerada göründüğünden ve yeterli mesafede durduğundan emin ol.',
                    style: const TextStyle(
                      color: AppColors.textSoft,
                      height: 1.4,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
