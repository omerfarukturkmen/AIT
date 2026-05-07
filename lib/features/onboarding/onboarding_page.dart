import 'package:flutter/material.dart';

import '../../core/constants/app_colors.dart';
import '../../core/state/onboarding_store.dart';
import '../../widgets/glass_card.dart';
import '../../widgets/premium_background.dart';
import '../../widgets/premium_button.dart';
import '../navigation/main_navigation_page.dart';

class OnboardingPage extends StatefulWidget {
  const OnboardingPage({super.key});

  @override
  State<OnboardingPage> createState() => _OnboardingPageState();
}

class _OnboardingPageState extends State<OnboardingPage> {
  final PageController _pageController = PageController();
  int currentIndex = 0;

  final List<_OnboardingItem> items = const [
    _OnboardingItem(
      icon: Icons.videocam_rounded,
      title: 'Canlı Kamera Analizi',
      description:
          'Kamera karşısında hareketlerini canlı olarak takip et. Uygulama form skorunu, tekrar sayısını ve anlık geri bildirimleri gösterir.',
      badge: 'Live AI Feedback',
    ),
    _OnboardingItem(
      icon: Icons.video_library_rounded,
      title: 'Video Yükleyerek Analiz',
      description:
          'Daha önce çektiğin egzersiz videolarını yükle. Yapay zeka destekli analiz sonucunda skor, hata ve önerileri rapor olarak gör.',
      badge: 'Upload Video Analysis',
    ),
    _OnboardingItem(
      icon: Icons.volume_up_rounded,
      title: 'Sesli Geri Bildirim',
      description:
          'Egzersiz sırasında ekrana bakmadan kulaklık üzerinden uyarı al. Dil, sesli geri bildirim ve uyarı sıklığını ayarlardan yönet.',
      badge: 'Voice Coaching',
    ),
  ];

  bool get isLastPage => currentIndex == items.length - 1;

  Future<void> finishOnboarding() async {
    await OnboardingStore.markAsSeen();

    if (!mounted) return;

    Navigator.pushReplacement(
      context,
      MaterialPageRoute(builder: (_) => const MainNavigationPage()),
    );
  }

  void nextPage() {
    if (isLastPage) {
      finishOnboarding();
      return;
    }

    _pageController.nextPage(
      duration: const Duration(milliseconds: 350),
      curve: Curves.easeOutCubic,
    );
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: PremiumBackground(
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 18, 16, 24),
            child: Column(
              children: [
                Row(
                  children: [
                    const Expanded(
                      child: Text(
                        'AIT Fitness Trainer',
                        style: TextStyle(
                          fontSize: 22,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                    ),
                    TextButton(
                      onPressed: finishOnboarding,
                      style: TextButton.styleFrom(
                        foregroundColor: AppColors.textSoft,
                      ),
                      child: const Text('Geç'),
                    ),
                  ],
                ),
                const SizedBox(height: 18),
                Expanded(
                  child: PageView.builder(
                    controller: _pageController,
                    itemCount: items.length,
                    onPageChanged: (index) {
                      setState(() {
                        currentIndex = index;
                      });
                    },
                    itemBuilder: (context, index) {
                      final item = items[index];

                      return _OnboardingCard(item: item);
                    },
                  ),
                ),
                const SizedBox(height: 20),
                _DotsIndicator(count: items.length, currentIndex: currentIndex),
                const SizedBox(height: 22),
                PremiumButton(
                  icon: isLastPage
                      ? Icons.check_circle_rounded
                      : Icons.arrow_forward_rounded,
                  text: isLastPage ? 'Başla' : 'Devam Et',
                  onPressed: nextPage,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _OnboardingCard extends StatelessWidget {
  final _OnboardingItem item;

  const _OnboardingCard({required this.item});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: GlassCard(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            _FeatureBadge(text: item.badge),
            const SizedBox(height: 28),
            Container(
              height: 116,
              width: 116,
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
                    blurRadius: 38,
                    offset: const Offset(0, 16),
                  ),
                ],
              ),
              child: Icon(item.icon, color: Colors.white, size: 56),
            ),
            const SizedBox(height: 30),
            Text(
              item.title,
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: 27,
                fontWeight: FontWeight.w900,
                letterSpacing: -0.7,
              ),
            ),
            const SizedBox(height: 14),
            Text(
              item.description,
              textAlign: TextAlign.center,
              style: const TextStyle(
                color: AppColors.textSoft,
                height: 1.55,
                fontSize: 14,
              ),
            ),
            const SizedBox(height: 28),
            const _ApiReadyBox(),
          ],
        ),
      ),
    );
  }
}

class _DotsIndicator extends StatelessWidget {
  final int count;
  final int currentIndex;

  const _DotsIndicator({required this.count, required this.currentIndex});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: List.generate(count, (index) {
        final isActive = index == currentIndex;

        return AnimatedContainer(
          duration: const Duration(milliseconds: 250),
          margin: const EdgeInsets.symmetric(horizontal: 4),
          height: 9,
          width: isActive ? 28 : 9,
          decoration: BoxDecoration(
            color: isActive
                ? AppColors.purpleGlow
                : Colors.white.withValues(alpha: 0.22),
            borderRadius: BorderRadius.circular(99),
          ),
        );
      }),
    );
  }
}

class _FeatureBadge extends StatelessWidget {
  final String text;

  const _FeatureBadge({required this.text});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 8),
      decoration: BoxDecoration(
        color: AppColors.purpleGlow.withValues(alpha: 0.14),
        borderRadius: BorderRadius.circular(99),
        border: Border.all(color: AppColors.purpleGlow.withValues(alpha: 0.30)),
      ),
      child: Text(
        text,
        style: const TextStyle(
          color: AppColors.purpleGlow,
          fontWeight: FontWeight.w900,
          fontSize: 12,
        ),
      ),
    );
  }
}

class _ApiReadyBox extends StatelessWidget {
  const _ApiReadyBox();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.045),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: Colors.white.withValues(alpha: 0.09)),
      ),
      child: const Row(
        children: [
          Icon(Icons.cloud_done_rounded, color: AppColors.purpleGlow),
          SizedBox(width: 10),
          Expanded(
            child: Text(
              'Frontend demo service ile çalışır. Backend API hazır olduğunda aynı ekranlar gerçek analiz verileriyle kullanılabilir.',
              style: TextStyle(
                color: AppColors.textSoft,
                height: 1.4,
                fontSize: 12,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _OnboardingItem {
  final IconData icon;
  final String title;
  final String description;
  final String badge;

  const _OnboardingItem({
    required this.icon,
    required this.title,
    required this.description,
    required this.badge,
  });
}
