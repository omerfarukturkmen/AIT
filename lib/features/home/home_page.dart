import 'dart:async';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:video_player/video_player.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/state/analysis_history_store.dart';
import '../../../core/state/favorite_exercises_store.dart';
import '../../../core/state/selected_exercise_store.dart';
import '../../../data/api_service.dart';
import '../../../data/exercise_details_data.dart';
import '../../../data/fake_data.dart';
import '../../../models/analysis_result_model.dart';
import '../../../widgets/glass_card.dart';
import '../../../widgets/premium_background.dart';
import '../../../widgets/premium_button.dart';
import '../camera/live_analysis_page.dart';
import '../exercise_detail/exercise_detail_page.dart';
import '../result/result_page.dart';

enum VideoAnalysisStatus { idle, selected, pending, completed, failed }

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final ImagePicker _picker = ImagePicker();

  VideoPlayerController? _videoController;
  XFile? selectedVideo;
  bool isAnalyzing = false;
  String selectedExercise = 'Squat';

  VideoAnalysisStatus videoAnalysisStatus = VideoAnalysisStatus.idle;
  String? videoAnalysisErrorMessage;

  @override
  void initState() {
    super.initState();
    selectedExercise = SelectedExerciseStore.selectedExercise.value;
    SelectedExerciseStore.selectedExercise.addListener(_syncSelectedExercise);
  }

  void _syncSelectedExercise() {
    if (!mounted) return;

    setState(() {
      selectedExercise = SelectedExerciseStore.selectedExercise.value;
    });
  }

  void selectExercise(String exerciseName) {
    SelectedExerciseStore.setExercise(exerciseName);
  }

  Future<void> _prepareVideo(XFile video) async {
    await _videoController?.dispose();

    if (kIsWeb) {
      _videoController = VideoPlayerController.networkUrl(
        Uri.parse(video.path),
      );
    } else {
      _videoController = VideoPlayerController.file(File(video.path));
    }

    await _videoController!.initialize();

    setState(() {
      selectedVideo = video;
      videoAnalysisStatus = VideoAnalysisStatus.selected;
      videoAnalysisErrorMessage = null;
    });

    await _videoController!.play();
  }

  Future<void> uploadVideo() async {
    final XFile? video = await _picker.pickVideo(source: ImageSource.gallery);

    if (video != null) {
      await _prepareVideo(video);
    }
  }

  Future<void> openLiveCamera() async {
    await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => LiveAnalysisPage(exerciseName: selectedExercise),
      ),
    );
  }

  void toggleVideoPlay() {
    if (_videoController == null) return;

    setState(() {
      if (_videoController!.value.isPlaying) {
        _videoController!.pause();
      } else {
        _videoController!.play();
      }
    });
  }

  Future<void> analyzeVideo() async {
    if (selectedVideo == null) {
      setState(() {
        videoAnalysisStatus = VideoAnalysisStatus.idle;
        videoAnalysisErrorMessage =
            'Lütfen önce analiz etmek için bir video yükle.';
      });

      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(videoAnalysisErrorMessage!)));
      return;
    }

    setState(() {
      isAnalyzing = true;
      videoAnalysisStatus = VideoAnalysisStatus.pending;
      videoAnalysisErrorMessage = null;
    });

    try {
      final videoBytes = await selectedVideo!.readAsBytes();
      final videoName = selectedVideo!.name.isNotEmpty
          ? selectedVideo!.name
          : 'uploaded_video.mp4';

      final dynamic backendResult = await ApiService.uploadVideoBytes(
        videoBytes: videoBytes,
        fileName: videoName,
        userId: 1,
        exerciseName: selectedExercise,
      );

      final int accuracy = backendResult.accuracy is int
          ? backendResult.accuracy
          : int.tryParse(backendResult.accuracy.toString()) ?? 0;

      final int totalFrames = backendResult.totalFrames is int
          ? backendResult.totalFrames
          : int.tryParse(backendResult.totalFrames.toString()) ?? 0;

      final double averageMotion = backendResult.averageMotion is double
          ? backendResult.averageMotion
          : double.tryParse(backendResult.averageMotion.toString()) ?? 0.0;

      final String exerciseName =
          backendResult.exercise?.toString() ?? selectedExercise;

      final String feedback =
          backendResult.feedback?.toString() ??
          'Analiz sonucu backend tarafından başarıyla oluşturuldu.';

      final result = AnalysisResult(
        exerciseName: exerciseName,
        score: accuracy,
        repetitionCount: totalFrames,
        confidence: accuracy.toDouble(),
        duration: '$totalFrames frame',
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
        videoAnalysisStatus = VideoAnalysisStatus.completed;
        videoAnalysisErrorMessage = null;
      });

      Navigator.push(
        context,
        MaterialPageRoute(builder: (_) => ResultPage(result: result)),
      );
    } catch (e) {
      if (!mounted) return;

      setState(() {
        videoAnalysisStatus = VideoAnalysisStatus.failed;
        videoAnalysisErrorMessage =
            'Video analiz edilirken bir sorun oluştu. Backend açık mı ve video dosyası uygun formatta mı kontrol et.';
      });

      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(videoAnalysisErrorMessage!)));
    } finally {
      if (mounted) {
        setState(() {
          isAnalyzing = false;
        });
      }
    }
  }

  @override
  void dispose() {
    SelectedExerciseStore.selectedExercise.removeListener(
      _syncSelectedExercise,
    );
    _videoController?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final bool hasVideo =
        _videoController != null && _videoController!.value.isInitialized;

    final exerciseDetail = getExerciseDetailByName(selectedExercise);

    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        title: const Text(
          'AIT Fitness',
          style: TextStyle(fontWeight: FontWeight.w900),
        ),
      ),
      body: PremiumBackground(
        child: isAnalyzing
            ? const _LoadingView()
            : SafeArea(
                child: SingleChildScrollView(
                  padding: const EdgeInsets.fromLTRB(16, 18, 16, 24),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      const _PremiumHeroCard(),
                      const SizedBox(height: 18),
                      _SelectedExerciseCard(
                        exerciseName: selectedExercise,
                        description: exerciseDetail.description,
                        onDetailPressed: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => ExerciseDetailPage(
                                exerciseName: selectedExercise,
                              ),
                            ),
                          );
                        },
                      ),
                      const SizedBox(height: 18),

                      _FavoriteExercisesCard(
                        onExerciseSelected: (exerciseName) {
                          setState(() {
                            selectedExercise = exerciseName;
                          });
                          SelectedExerciseStore.setExercise(exerciseName);
                        },
                      ),
                      const SizedBox(height: 18),
                      const _SectionHeader(
                        title: 'Hareket Seç',
                        subtitle: 'Analiz etmek istediğin egzersizi seç.',
                      ),
                      const SizedBox(height: 10),
                      SizedBox(
                        height: 90,
                        child: ListView.builder(
                          scrollDirection: Axis.horizontal,
                          itemCount: exercises.length,
                          itemBuilder: (context, index) {
                            final exercise = exercises[index];
                            final isSelected =
                                selectedExercise == exercise.name;

                            return Padding(
                              padding: const EdgeInsets.only(right: 12),
                              child: _ExerciseTile(
                                exerciseName: exercise.name,
                                icon: exercise.icon,
                                isSelected: isSelected,
                                onTap: () {
                                  selectExercise(exercise.name);
                                },
                                onLongPress: () {
                                  Navigator.push(
                                    context,
                                    MaterialPageRoute(
                                      builder: (_) => ExerciseDetailPage(
                                        exerciseName: exercise.name,
                                      ),
                                    ),
                                  );
                                },
                              ),
                            );
                          },
                        ),
                      ),
                      const SizedBox(height: 20),
                      const _SectionHeader(
                        title: 'Analiz Modu',
                        subtitle:
                            'Canlı analiz yap veya daha önce çekilmiş bir videoyu yükle.',
                      ),
                      const SizedBox(height: 10),
                      Row(
                        children: [
                          Expanded(
                            child: _ModeCard(
                              icon: Icons.video_library_rounded,
                              title: 'Video Yükle',
                              subtitle: 'Galeriden video seç ve analiz ettir',
                              onTap: uploadVideo,
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: _ModeCard(
                              icon: Icons.videocam_rounded,
                              title: 'Canlı Kamera',
                              subtitle: 'Anlık sesli ve yazılı feedback al',
                              onTap: openLiveCamera,
                            ),
                          ),
                        ],
                      ),
                      if (hasVideo) ...[
                        const SizedBox(height: 20),
                        const _SectionHeader(
                          title: 'Video Ön İzleme',
                          subtitle:
                              'Video analizi için hareketin net göründüğünden emin ol.',
                        ),
                        const SizedBox(height: 10),
                        GlassCard(
                          child: ClipRRect(
                            borderRadius: BorderRadius.circular(18),
                            child: AspectRatio(
                              aspectRatio: _videoController!.value.aspectRatio,
                              child: GestureDetector(
                                onTap: toggleVideoPlay,
                                child: Stack(
                                  alignment: Alignment.center,
                                  children: [
                                    VideoPlayer(_videoController!),
                                    Positioned(
                                      top: 12,
                                      left: 12,
                                      child: _StatusBadge(
                                        text: 'Video Ready',
                                        color: Colors.greenAccent,
                                      ),
                                    ),
                                    Positioned(
                                      top: 12,
                                      right: 12,
                                      child: _StatusBadge(
                                        text: selectedExercise,
                                        color: AppColors.purpleGlow,
                                      ),
                                    ),
                                    if (!_videoController!.value.isPlaying)
                                      Container(
                                        decoration: BoxDecoration(
                                          color: Colors.black.withValues(
                                            alpha: 0.35,
                                          ),
                                          shape: BoxShape.circle,
                                          border: Border.all(
                                            color: Colors.white.withValues(
                                              alpha: 0.25,
                                            ),
                                          ),
                                        ),
                                        padding: const EdgeInsets.all(18),
                                        child: const Icon(
                                          Icons.play_arrow_rounded,
                                          size: 48,
                                          color: Colors.white,
                                        ),
                                      ),
                                  ],
                                ),
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(height: 14),
                        _VideoAnalysisStatusCard(
                          status: videoAnalysisStatus,
                          errorMessage: videoAnalysisErrorMessage,
                          exerciseName: selectedExercise,
                        ),
                        const SizedBox(height: 14),
                        PremiumButton(
                          icon: Icons.analytics_rounded,
                          text: 'Yüklenen Videoyu Backend ile Analiz Et',
                          onPressed: analyzeVideo,
                        ),
                      ],
                      if (!hasVideo &&
                          videoAnalysisStatus ==
                              VideoAnalysisStatus.failed) ...[
                        const SizedBox(height: 18),
                        _VideoAnalysisStatusCard(
                          status: videoAnalysisStatus,
                          errorMessage: videoAnalysisErrorMessage,
                          exerciseName: selectedExercise,
                        ),
                      ],
                      const SizedBox(height: 18),
                      const _TipsCard(),
                    ],
                  ),
                ),
              ),
      ),
    );
  }
}

class _PremiumHeroCard extends StatelessWidget {
  const _PremiumHeroCard();

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Row(
        children: [
          Container(
            height: 58,
            width: 58,
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [
                  Color(0xFF5B4B8A),
                  Color(0xFF3B2A6D),
                  Color(0xFF1F1A3D),
                ],
              ),
              borderRadius: BorderRadius.circular(18),
              boxShadow: [
                BoxShadow(
                  color: AppColors.purpleGlow.withValues(alpha: 0.28),
                  blurRadius: 24,
                  offset: const Offset(0, 10),
                ),
              ],
            ),
            child: const Icon(
              Icons.fitness_center_rounded,
              color: Colors.white,
              size: 32,
            ),
          ),
          const SizedBox(width: 14),
          const Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'AI Fitness Trainer',
                  style: TextStyle(
                    fontSize: 27,
                    fontWeight: FontWeight.w900,
                    letterSpacing: -0.6,
                  ),
                ),
                SizedBox(height: 8),
                Text(
                  'Canlı kamera veya video üzerinden egzersiz formunu analiz et.',
                  style: TextStyle(
                    color: AppColors.textSoft,
                    height: 1.4,
                    fontSize: 14,
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

class _SelectedExerciseCard extends StatelessWidget {
  final String exerciseName;
  final String description;
  final VoidCallback onDetailPressed;

  const _SelectedExerciseCard({
    required this.exerciseName,
    required this.description,
    required this.onDetailPressed,
  });

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const _StatusBadge(
                text: 'Selected Exercise',
                color: AppColors.purpleGlow,
              ),
              const Spacer(),
              TextButton.icon(
                onPressed: onDetailPressed,
                icon: const Icon(Icons.info_outline_rounded, size: 18),
                label: const Text('Detay'),
                style: TextButton.styleFrom(
                  foregroundColor: AppColors.purpleGlow,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            exerciseName,
            style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w900),
          ),
          const SizedBox(height: 8),
          Text(
            description,
            maxLines: 3,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(color: AppColors.textSoft, height: 1.5),
          ),
        ],
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  final String title;
  final String subtitle;

  const _SectionHeader({required this.title, required this.subtitle});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          height: 24,
          width: 4,
          decoration: BoxDecoration(
            color: AppColors.purpleGlow,
            borderRadius: BorderRadius.circular(99),
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w900,
                ),
              ),
              const SizedBox(height: 3),
              Text(
                subtitle,
                style: const TextStyle(color: AppColors.textSoft, fontSize: 12),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _ExerciseTile extends StatelessWidget {
  final String exerciseName;
  final IconData icon;
  final bool isSelected;
  final VoidCallback onTap;
  final VoidCallback onLongPress;

  const _ExerciseTile({
    required this.exerciseName,
    required this.icon,
    required this.isSelected,
    required this.onTap,
    required this.onLongPress,
  });

  @override
  Widget build(BuildContext context) {
    return AnimatedScale(
      scale: isSelected ? 1.04 : 1,
      duration: const Duration(milliseconds: 180),
      child: GestureDetector(
        onTap: onTap,
        onLongPress: onLongPress,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 240),
          width: 135,
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: isSelected
                  ? const [
                      Color(0xFF5B4B8A),
                      Color(0xFF3B2A6D),
                      Color(0xFF1F1A3D),
                    ]
                  : [
                      Colors.white.withValues(alpha: 0.09),
                      Colors.white.withValues(alpha: 0.035),
                    ],
            ),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(
              color: isSelected
                  ? AppColors.purpleGlow.withValues(alpha: 0.70)
                  : Colors.white.withValues(alpha: 0.12),
            ),
            boxShadow: [
              if (isSelected)
                BoxShadow(
                  color: AppColors.purpleGlow.withValues(alpha: 0.22),
                  blurRadius: 22,
                  offset: const Offset(0, 10),
                ),
            ],
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(icon, size: 25, color: Colors.white),
              const Spacer(),
              Text(
                exerciseName,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  fontWeight: FontWeight.w900,
                  fontSize: 13,
                ),
              ),
              const SizedBox(height: 3),
              Text(
                isSelected ? 'Active' : 'Tap to select',
                style: TextStyle(
                  color: Colors.white.withValues(alpha: 0.65),
                  fontSize: 10,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ModeCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  const _ModeCard({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: GlassCard(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, color: AppColors.purpleGlow, size: 32),
            const SizedBox(height: 12),
            Text(
              title,
              style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 16),
            ),
            const SizedBox(height: 5),
            Text(
              subtitle,
              style: const TextStyle(
                color: AppColors.textSoft,
                fontSize: 12,
                height: 1.3,
              ),
            ),
          ],
        ),
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
      padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 7),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.14),
        borderRadius: BorderRadius.circular(99),
        border: Border.all(color: color.withValues(alpha: 0.30)),
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

class _VideoAnalysisStatusCard extends StatelessWidget {
  final VideoAnalysisStatus status;
  final String? errorMessage;
  final String exerciseName;

  const _VideoAnalysisStatusCard({
    required this.status,
    required this.errorMessage,
    required this.exerciseName,
  });

  Color get statusColor {
    switch (status) {
      case VideoAnalysisStatus.idle:
        return AppColors.textSoft;
      case VideoAnalysisStatus.selected:
        return AppColors.purpleGlow;
      case VideoAnalysisStatus.pending:
        return Colors.orangeAccent;
      case VideoAnalysisStatus.completed:
        return Colors.greenAccent;
      case VideoAnalysisStatus.failed:
        return Colors.redAccent;
    }
  }

  IconData get statusIcon {
    switch (status) {
      case VideoAnalysisStatus.idle:
        return Icons.video_library_rounded;
      case VideoAnalysisStatus.selected:
        return Icons.check_circle_outline_rounded;
      case VideoAnalysisStatus.pending:
        return Icons.cloud_sync_rounded;
      case VideoAnalysisStatus.completed:
        return Icons.verified_rounded;
      case VideoAnalysisStatus.failed:
        return Icons.error_rounded;
    }
  }

  String get statusTitle {
    switch (status) {
      case VideoAnalysisStatus.idle:
        return 'Video analizi bekleniyor';
      case VideoAnalysisStatus.selected:
        return 'Video seçildi';
      case VideoAnalysisStatus.pending:
        return 'Backend analizi çalışıyor';
      case VideoAnalysisStatus.completed:
        return 'Analiz tamamlandı';
      case VideoAnalysisStatus.failed:
        return 'Analiz başarısız oldu';
    }
  }

  String get statusDescription {
    switch (status) {
      case VideoAnalysisStatus.idle:
        return 'Analize başlamak için önce galeriden bir video seç.';
      case VideoAnalysisStatus.selected:
        return '$exerciseName hareketi için video hazır. Analizi başlatabilirsin.';
      case VideoAnalysisStatus.pending:
        return 'Video backend tarafına gönderildi. Sonuç hazırlanıyor.';
      case VideoAnalysisStatus.completed:
        return 'Sonuç ekranı açıldı ve analiz geçmişe kaydedildi.';
      case VideoAnalysisStatus.failed:
        return errorMessage ??
            'Video analiz edilirken bir sorun oluştu. Lütfen tekrar dene.';
    }
  }

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            height: 46,
            width: 46,
            decoration: BoxDecoration(
              color: statusColor.withValues(alpha: 0.14),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: statusColor.withValues(alpha: 0.30)),
            ),
            child: Icon(statusIcon, color: statusColor, size: 25),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  statusTitle,
                  style: TextStyle(
                    color: statusColor,
                    fontSize: 16,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  statusDescription,
                  style: const TextStyle(
                    color: AppColors.textSoft,
                    height: 1.4,
                    fontSize: 13,
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

class _TipsCard extends StatelessWidget {
  const _TipsCard();

  @override
  Widget build(BuildContext context) {
    return const GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Daha İyi Analiz İçin',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900),
          ),
          SizedBox(height: 12),
          _TipRow(text: 'Canlı analiz için tüm vücudun kamerada görünsün.'),
          _TipRow(text: 'Video yüklerken hareketin net göründüğünden emin ol.'),
          _TipRow(text: 'Ortam ışığı yeterli olsun.'),
          _TipRow(text: 'Hareketi net ve kontrollü şekilde yap.'),
        ],
      ),
    );
  }
}

class _TipRow extends StatelessWidget {
  final String text;

  const _TipRow({required this.text});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 9),
      child: Row(
        children: [
          const Icon(
            Icons.check_circle_rounded,
            color: AppColors.purpleGlow,
            size: 18,
          ),
          const SizedBox(width: 10),
          Expanded(child: Text(text)),
        ],
      ),
    );
  }
}

class _LoadingView extends StatefulWidget {
  const _LoadingView();

  @override
  State<_LoadingView> createState() => _LoadingViewState();
}

class _LoadingViewState extends State<_LoadingView> {
  Timer? _timer;
  int currentStep = 0;

  final List<_AnalysisStep> steps = const [
    _AnalysisStep(
      title: 'Video backend için hazırlanıyor...',
      description: 'Yüklenen video FastAPI backend tarafına gönderiliyor.',
      icon: Icons.video_file_rounded,
    ),
    _AnalysisStep(
      title: 'Backend analizi çalışıyor...',
      description:
          'Video dosyası backend /upload-video endpointinde işleniyor.',
      icon: Icons.cloud_sync_rounded,
    ),
    _AnalysisStep(
      title: 'Form skoru hesaplanıyor...',
      description: 'Backend hareket yoğunluğu ve analiz metriklerini üretiyor.',
      icon: Icons.analytics_rounded,
    ),
    _AnalysisStep(
      title: 'AI geri bildirimi oluşturuluyor...',
      description: 'Backend sonucundan kullanıcıya özel öneriler hazırlanıyor.',
      icon: Icons.psychology_rounded,
    ),
    _AnalysisStep(
      title: 'Rapor hazırlanıyor...',
      description: 'Analiz sonucu ekrana yönlendiriliyor.',
      icon: Icons.assignment_turned_in_rounded,
    ),
  ];

  @override
  void initState() {
    super.initState();

    _timer = Timer.periodic(const Duration(milliseconds: 750), (timer) {
      if (!mounted) return;

      setState(() {
        if (currentStep < steps.length - 1) {
          currentStep++;
        }
      });
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  double get progressValue {
    return (currentStep + 1) / steps.length;
  }

  @override
  Widget build(BuildContext context) {
    final activeStep = steps[currentStep];

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: GlassCard(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TweenAnimationBuilder<double>(
                tween: Tween(begin: 0, end: progressValue),
                duration: const Duration(milliseconds: 500),
                curve: Curves.easeOutCubic,
                builder: (context, value, child) {
                  return SizedBox(
                    height: 118,
                    width: 118,
                    child: Stack(
                      alignment: Alignment.center,
                      children: [
                        CircularProgressIndicator(
                          value: value,
                          strokeWidth: 8,
                          backgroundColor: Colors.white.withValues(alpha: 0.08),
                          color: AppColors.purpleGlow,
                        ),
                        Container(
                          height: 78,
                          width: 78,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            gradient: const LinearGradient(
                              colors: [
                                Color(0xFF5B4B8A),
                                Color(0xFF3B2A6D),
                                Color(0xFF1F1A3D),
                              ],
                            ),
                            boxShadow: [
                              BoxShadow(
                                color: AppColors.purpleGlow.withValues(
                                  alpha: 0.35,
                                ),
                                blurRadius: 28,
                                offset: const Offset(0, 12),
                              ),
                            ],
                          ),
                          child: Icon(
                            activeStep.icon,
                            color: Colors.white,
                            size: 34,
                          ),
                        ),
                      ],
                    ),
                  );
                },
              ),
              const SizedBox(height: 24),
              const _StatusBadge(
                text: 'Backend Analysis Running',
                color: AppColors.purpleGlow,
              ),
              const SizedBox(height: 18),
              AnimatedSwitcher(
                duration: const Duration(milliseconds: 350),
                transitionBuilder: (child, animation) {
                  return FadeTransition(
                    opacity: animation,
                    child: SlideTransition(
                      position: Tween<Offset>(
                        begin: const Offset(0, 0.12),
                        end: Offset.zero,
                      ).animate(animation),
                      child: child,
                    ),
                  );
                },
                child: Column(
                  key: ValueKey(currentStep),
                  children: [
                    Text(
                      activeStep.title,
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      activeStep.description,
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        color: AppColors.textSoft,
                        height: 1.45,
                        fontSize: 13,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 22),
              ClipRRect(
                borderRadius: BorderRadius.circular(99),
                child: LinearProgressIndicator(
                  value: progressValue,
                  minHeight: 9,
                  backgroundColor: Colors.white.withValues(alpha: 0.08),
                  valueColor: const AlwaysStoppedAnimation<Color>(
                    AppColors.purpleGlow,
                  ),
                ),
              ),
              const SizedBox(height: 12),
              Text(
                'Adım ${currentStep + 1} / ${steps.length}',
                style: const TextStyle(
                  color: AppColors.textSoft,
                  fontWeight: FontWeight.w700,
                  fontSize: 12,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _AnalysisStep {
  final String title;
  final String description;
  final IconData icon;

  const _AnalysisStep({
    required this.title,
    required this.description,
    required this.icon,
  });
}

class _FavoriteExercisesCard extends StatelessWidget {
  final ValueChanged<String> onExerciseSelected;

  const _FavoriteExercisesCard({required this.onExerciseSelected});

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<Set<String>>(
      valueListenable: FavoriteExercisesStore.favorites,
      builder: (context, favorites, child) {
        if (favorites.isEmpty) {
          return GlassCard(
            child: Row(
              children: [
                Container(
                  height: 48,
                  width: 48,
                  decoration: BoxDecoration(
                    color: AppColors.purpleGlow.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(
                      color: AppColors.purpleGlow.withValues(alpha: 0.22),
                    ),
                  ),
                  child: const Icon(
                    Icons.favorite_border_rounded,
                    color: AppColors.purpleGlow,
                  ),
                ),
                const SizedBox(width: 12),
                const Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Favori Egzersizler',
                        style: TextStyle(
                          fontSize: 17,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                      SizedBox(height: 4),
                      Text(
                        'Egzersiz detay sayfasından favori ekleyebilirsin.',
                        style: TextStyle(
                          color: AppColors.textSoft,
                          height: 1.4,
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          );
        }

        return GlassCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Row(
                children: [
                  Icon(Icons.favorite_rounded, color: Colors.redAccent),
                  SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      'Favori Egzersizler',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 14),
              Wrap(
                spacing: 10,
                runSpacing: 10,
                children: favorites.map((exerciseName) {
                  return GestureDetector(
                    onTap: () {
                      onExerciseSelected(exerciseName);
                    },
                    onLongPress: () {
                      FavoriteExercisesStore.removeFavorite(exerciseName);

                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(
                          content: Text(
                            '$exerciseName favorilerden çıkarıldı.',
                          ),
                        ),
                      );
                    },
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 14,
                        vertical: 10,
                      ),
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          colors: [
                            Colors.redAccent.withValues(alpha: 0.20),
                            AppColors.purpleGlow.withValues(alpha: 0.08),
                          ],
                        ),
                        borderRadius: BorderRadius.circular(99),
                        border: Border.all(
                          color: Colors.redAccent.withValues(alpha: 0.28),
                        ),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(
                            Icons.favorite_rounded,
                            color: Colors.redAccent,
                            size: 17,
                          ),
                          const SizedBox(width: 7),
                          Text(
                            exerciseName,
                            style: const TextStyle(
                              fontWeight: FontWeight.w800,
                              fontSize: 13,
                            ),
                          ),
                        ],
                      ),
                    ),
                  );
                }).toList(),
              ),
              const SizedBox(height: 10),
              const Text(
                'Favoriye dokunarak egzersizi seçebilirsin. Uzun basarak favorilerden çıkarabilirsin.',
                style: TextStyle(
                  color: AppColors.textSoft,
                  fontSize: 11,
                  height: 1.4,
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}
