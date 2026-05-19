import 'package:camera/camera.dart';
import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';
import '../../../main.dart';
import '../../../widgets/glass_card.dart';
import '../../../widgets/premium_background.dart';
import '../../../widgets/premium_button.dart';

class CameraRecordPage extends StatefulWidget {
  const CameraRecordPage({super.key});

  @override
  State<CameraRecordPage> createState() => _CameraRecordPageState();
}

class _CameraRecordPageState extends State<CameraRecordPage> {
  CameraController? _cameraController;
  bool isRecording = false;
  bool isCameraReady = false;
  bool hasCameraError = false;

  @override
  void initState() {
    super.initState();
    setupCamera();
  }

  Future<void> setupCamera() async {
    if (appCameras.isEmpty) {
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
    if (_cameraController == null || !_cameraController!.value.isInitialized) {
      return;
    }

    try {
      await _cameraController!.startVideoRecording();

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

  Future<void> stopRecording() async {
    if (_cameraController == null || !isRecording) return;

    try {
      final XFile video = await _cameraController!.stopVideoRecording();

      setState(() {
        isRecording = false;
      });

      if (!mounted) return;

      Navigator.pop(context, video);
    } catch (_) {
      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Video kaydı durdurulamadı.')),
      );
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
                      onPressed: () => Navigator.pop(context),
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
              Padding(
                padding: const EdgeInsets.all(16),
                child: PremiumButton(
                  icon: isRecording
                      ? Icons.stop_rounded
                      : Icons.fiber_manual_record_rounded,
                  text: isRecording ? 'Kaydı Durdur' : 'Kaydı Başlat',
                  onPressed: isRecording ? stopRecording : startRecording,
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
