import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/state/onboarding_store.dart';
import '../../../widgets/premium_background.dart';
import '../navigation/main_navigation_page.dart';
import '../onboarding/onboarding_page.dart';

class SplashPage extends StatefulWidget {
  const SplashPage({super.key});

  @override
  State<SplashPage> createState() => _SplashPageState();
}

class _SplashPageState extends State<SplashPage> {
  @override
  void initState() {
    super.initState();
    _navigateNext();
  }

  Future<void> _navigateNext() async {
    await Future.delayed(const Duration(seconds: 2));

    final hasSeenOnboarding = await OnboardingStore.hasSeenOnboarding();

    if (!mounted) return;

    Navigator.pushReplacement(
      context,
      MaterialPageRoute(
        builder: (_) => hasSeenOnboarding
            ? const MainNavigationPage()
            : const OnboardingPage(),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: PremiumBackground(
        child: Center(
          child: TweenAnimationBuilder<double>(
            tween: Tween(begin: 0.6, end: 1),
            duration: const Duration(milliseconds: 900),
            curve: Curves.easeOutBack,
            builder: (context, value, child) {
              return Opacity(
                opacity: value.clamp(0.0, 1.0),
                child: Transform.scale(scale: value, child: child),
              );
            },
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  height: 110,
                  width: 110,
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
                        color: AppColors.purpleGlow.withValues(alpha: 0.4),
                        blurRadius: 40,
                        spreadRadius: 5,
                      ),
                    ],
                  ),
                  child: const Icon(
                    Icons.fitness_center_rounded,
                    size: 50,
                    color: Colors.white,
                  ),
                ),
                const SizedBox(height: 24),
                const Text(
                  'AIT Fitness',
                  style: TextStyle(fontSize: 26, fontWeight: FontWeight.w900),
                ),
                const SizedBox(height: 8),
                const Text(
                  'AI destekli form analizi',
                  style: TextStyle(color: AppColors.textSoft),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
