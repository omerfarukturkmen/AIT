import 'package:camera/camera.dart';
import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';
import '../../../data/api_service.dart';
import '../../../main.dart';
import '../../../widgets/glass_card.dart';
import '../../../widgets/premium_background.dart';
import '../../../widgets/premium_button.dart';
import '../result/result_page.dart';

class CameraRecordPage extends StatefulWidget {
  final String exerciseName;

  const CameraRecordPage({super.key, required this.exerciseName});

  @override
  State<CameraRecordPage> createState() => _CameraRecordPageState();
}

class _CameraRecordPageState extends State<CameraRecordPage> {
  CameraController? _cameraController;

  bool isRecording = false;
  bool isCameraReady = false;
  bool hasCameraError = false;
  bool isAnalyzing = false;

  @override
  void initState() {
    super.initState();
    setupCamera();
  }

  Future<void> setupCamera() async {
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
      ResolutionPreset.high,
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

  Future<void> startRecording() async {
    if (isAnalyzing) return;

    if (_cameraController == null || !_cameraController!.value.isInitialized) {
      return;
    }

    try {
      await _cameraController!.startVideoRecording();

      if (!mounted) return;

      setState(() {
        isRecording = true;
      });
    } catch (_) {
      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Video kaydı başlatılamadı.')),
      );
    }
  }

  Future<void> stopRecordingAndAnalyze() async {
    if (_cameraController == null || !isRecording || isAnalyzing) return;

    try {
      final XFile video = await _cameraController!.stopVideoRecording();

      if (!mounted) return;

      setState(() {
        isRecording = false;
        isAnalyzing = true;
      });

      final videoBytes = await video.readAsBytes();
      final videoName = video.name.isNotEmpty
          ? video.name
          : 'exercise_video.mp4';

      final result = await ApiService.uploadVideoBytes(
        videoBytes: videoBytes,
        fileName: videoName,
        exerciseName: widget.exerciseName,
      );

      if (!mounted) return;

      setState(() {
        isAnalyzing = false;
      });

      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (_) => ResultPage(result: result)),
      );
    } catch (e) {
      if (!mounted) return;

      setState(() {
        isRecording = false;
        isAnalyzing = false;
      });

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            e is ApiException
                ? e.message
                : 'Video analiz edilemedi. Lütfen tekrar dene.',
          ),
        ),
      );
    }
  }

  void handleMainButtonPressed() {
    if (isAnalyzing) return;

    if (isRecording) {
      stopRecordingAndAnalyze();
    } else {
      startRecording();
    }
  }

  @override
  void dispose() {
    _cameraController?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: PremiumBackground(
        child: SafeArea(
          child: Column(
            children: [
              Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    IconButton(
                      onPressed: isAnalyzing
                          ? null
                          : () {
                              Navigator.pop(context);
                            },
                      icon: const Icon(Icons.arrow_back_rounded),
                    ),
                    const Expanded(
                      child: Text(
                        'Video Kaydı',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                    ),
                    const SizedBox(width: 48),
                  ],
                ),
              ),
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: GlassCard(
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(22),
                      child: _buildCameraContent(),
                    ),
                  ),
                ),
              ),
              if (isAnalyzing)
                const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 16),
                  child: GlassCard(
                    child: Column(
                      children: [
                        CircularProgressIndicator(color: AppColors.purpleGlow),
                        SizedBox(height: 14),
                        Text(
                          'Video backend tarafına gönderiliyor ve analiz ediliyor...',
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            color: AppColors.textSoft,
                            height: 1.4,
                            fontSize: 14,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              Padding(
                padding: const EdgeInsets.all(16),
                child: PremiumButton(
                  icon: isAnalyzing
                      ? Icons.hourglass_top_rounded
                      : isRecording
                      ? Icons.stop_rounded
                      : Icons.fiber_manual_record_rounded,
                  text: isAnalyzing
                      ? 'Analiz Ediliyor...'
                      : isRecording
                      ? 'Kaydı Durdur ve Analiz Et'
                      : 'Kaydı Başlat',
                  onPressed: handleMainButtonPressed,
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
