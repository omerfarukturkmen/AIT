import 'dart:async';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:video_player/video_player.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/services/analysis_service.dart';
import '../../../core/state/analysis_history_store.dart';
import '../../../data/exercise_details_data.dart';
import '../../../data/fake_data.dart';
import '../../../widgets/glass_card.dart';
import '../../../widgets/premium_background.dart';
import '../../../widgets/premium_button.dart';
import '../camera/live_analysis_page.dart';
import '../exercise_detail/exercise_detail_page.dart';
import '../result/result_page.dart';
import '../../../core/state/favorite_exercises_store.dart';
import '../../../core/state/selected_exercise_store.dart';
class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final ImagePicker _picker = ImagePicker();

  VideoPlayerController? _videoController;
  String? selectedVideoPath;
  bool isAnalyzing = false;
  String selectedExercise = 'Squat';
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
      selectedVideoPath = video.path;
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
        builder: (_) => LiveAnalysisPage(
          exerciseName: selectedExercise,
        ),
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
    if (selectedVideoPath == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Lütfen önce analiz etmek için bir video yükle.',
          ),
        ),
      );
      return;
    }

    setState(() {
      isAnalyzing = true;
    });

    try {
      final result = await AnalysisService().analyzeVideo(
        videoFile: File(selectedVideoPath!),
        exerciseName: selectedExercise,
      );

      AnalysisHistoryStore.addResult(result);

      if (!mounted) return;

      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => ResultPage(result: result),
        ),
      );
    } catch (_) {
      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Analiz sırasında bir hata oluştu.'),
        ),
      );
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
  SelectedExerciseStore.selectedExercise.removeListener(_syncSelectedExercise);
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
                      const SizedBox(height: 20),
                      const _SectionHeader(
                        title: 'Video Ön İzleme',
                        subtitle:
                            'Video analizi için hareketin net göründüğünden emin ol.',
                      ),
                      const SizedBox(height: 10),
                      GlassCard(
                        child: hasVideo
                            ? ClipRRect(
                                borderRadius: BorderRadius.circular(18),
                                child: AspectRatio(
                                  aspectRatio:
                                      _videoController!.value.aspectRatio,
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
                              )
                            : const _VideoPlaceholder(),
                      ),
                      const SizedBox(height: 18),
                      PremiumButton(
                        icon: Icons.analytics_rounded,
                        text: hasVideo
                            ? 'Yüklenen Videoyu Analiz Et'
                            : 'Önce Video Yükle',
                        onPressed: analyzeVideo,
                      ),
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
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
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
                        fontSize: 25,
                        fontWeight: FontWeight.w900,
                        letterSpacing: -0.6,
                      ),
                    ),
                    SizedBox(height: 6),
                    Text(
                      'Canlı kamera veya video üzerinden egzersiz formunu analiz et.',
                      style: TextStyle(
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
          const SizedBox(height: 18),
          Row(
            children: const [
              _HeroMetric(
                title: 'Live Mode',
                value: 'Camera',
                icon: Icons.videocam_rounded,
              ),
              SizedBox(width: 10),
              _HeroMetric(
                title: 'Upload Mode',
                value: 'Video',
                icon: Icons.movie_creation_rounded,
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _HeroMetric extends StatelessWidget {
  final String title;
  final String value;
  final IconData icon;

  const _HeroMetric({
    required this.title,
    required this.value,
    required this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(13),
        decoration: BoxDecoration(
          color: AppColors.purpleGlow.withValues(alpha: 0.12),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: AppColors.purpleGlow.withValues(alpha: 0.24),
          ),
        ),
        child: Row(
          children: [
            Icon(
              icon,
              color: AppColors.purpleGlow,
              size: 21,
            ),
            const SizedBox(width: 8),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    value,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      fontWeight: FontWeight.w900,
                      fontSize: 13,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    title,
                    style: const TextStyle(
                      color: AppColors.textSoft,
                      fontSize: 11,
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
                icon: const Icon(
                  Icons.info_outline_rounded,
                  size: 18,
                ),
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
            style: const TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            description,
            maxLines: 3,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(
              color: AppColors.textSoft,
              height: 1.5,
            ),
          ),
        ],
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  final String title;
  final String subtitle;

  const _SectionHeader({
    required this.title,
    required this.subtitle,
  });

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
                style: const TextStyle(
                  color: AppColors.textSoft,
                  fontSize: 12,
                ),
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
              Icon(
                icon,
                size: 25,
                color: Colors.white,
              ),
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
            Icon(
              icon,
              color: AppColors.purpleGlow,
              size: 32,
            ),
            const SizedBox(height: 12),
            Text(
              title,
              style: const TextStyle(
                fontWeight: FontWeight.w900,
                fontSize: 16,
              ),
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

  const _StatusBadge({
    required this.text,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: 11,
        vertical: 7,
      ),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.14),
        borderRadius: BorderRadius.circular(99),
        border: Border.all(
          color: color.withValues(alpha: 0.30),
        ),
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

class _VideoPlaceholder extends StatelessWidget {
  const _VideoPlaceholder();

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 220,
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            height: 76,
            width: 76,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: AppColors.purpleGlow.withValues(alpha: 0.14),
              border: Border.all(
                color: AppColors.purpleGlow.withValues(alpha: 0.26),
              ),
            ),
            child: const Icon(
              Icons.video_library_rounded,
              size: 38,
              color: AppColors.textSoft,
            ),
          ),
          const SizedBox(height: 16),
          const Text(
            'Henüz video seçilmedi',
            style: TextStyle(
              fontWeight: FontWeight.w900,
              fontSize: 17,
            ),
          ),
          const SizedBox(height: 7),
          const Text(
            'Galeriden video yükleyerek yapay zeka analizini başlatabilirsin.',
            textAlign: TextAlign.center,
            style: TextStyle(
              color: AppColors.textSoft,
              fontSize: 13,
              height: 1.4,
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
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w900,
            ),
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

  const _TipRow({
    required this.text,
  });

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
          Expanded(
            child: Text(text),
          ),
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
      title: 'Video hazırlanıyor...',
      description: 'Yüklenen video analiz için işleniyor.',
      icon: Icons.video_file_rounded,
    ),
    _AnalysisStep(
      title: 'Hareket noktaları çıkarılıyor...',
      description: 'Vücut pozisyonu ve eklem hizaları inceleniyor.',
      icon: Icons.accessibility_new_rounded,
    ),
    _AnalysisStep(
      title: 'Form skoru hesaplanıyor...',
      description: 'Hareket açısı, tekrar sayısı ve duruş kalitesi değerlendiriliyor.',
      icon: Icons.analytics_rounded,
    ),
    _AnalysisStep(
      title: 'AI geri bildirimi oluşturuluyor...',
      description: 'Tespit edilen hatalar ve öneriler hazırlanıyor.',
      icon: Icons.psychology_rounded,
    ),
    _AnalysisStep(
      title: 'Rapor hazırlanıyor...',
      description: 'Analiz sonucu kullanıcıya anlaşılır şekilde sunuluyor.',
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
                                color: AppColors.purpleGlow.withValues(alpha: 0.35),
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
                text: 'AI Analysis Running',
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

  const _FavoriteExercisesCard({
    required this.onExerciseSelected,
  });

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
                  Icon(
                    Icons.favorite_rounded,
                    color: Colors.redAccent,
                  ),
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