import 'package:flutter/material.dart';

import '../../app.dart';
import '../../core/state/auth_store.dart';
import '../../core/state/onboarding_store.dart';
import '../../core/theme/app_theme.dart';
import '../../widgets/common.dart';
import '../auth/auth_page.dart';
import '../navigation/main_navigation_page.dart';
import '../onboarding/onboarding_page.dart';

/// Restores the session, then routes to onboarding, sign-in or the app.
class SplashPage extends StatefulWidget {
  const SplashPage({super.key});

  @override
  State<SplashPage> createState() => _SplashPageState();
}

class _SplashPageState extends State<SplashPage> {
  @override
  void initState() {
    super.initState();
    _route();
  }

  Future<void> _route() async {
    final results = await Future.wait([
      OnboardingStore.hasSeenOnboarding(),
      AuthStore.restore().then((_) => AuthStore.isSignedIn),
      // Keep the brand visible briefly instead of flashing.
      Future<bool>.delayed(const Duration(milliseconds: 600), () => true),
    ]);
    if (!mounted) return;

    final Widget next = !results[0]
        ? const OnboardingPage()
        : results[1]
        ? const MainNavigationPage()
        : const AuthPage();
    Navigator.of(context).pushReplacement(
      PageRouteBuilder(
        pageBuilder: (_, _, _) => next,
        transitionsBuilder: (_, animation, _, child) =>
            FadeTransition(opacity: animation, child: child),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const BrandMark(size: 72),
            const SizedBox(height: Gap.lg),
            const Wordmark(size: 34),
            const SizedBox(height: Gap.xs),
            Text(
              context.l10n.appTagline,
              style: context.text.bodyMedium?.copyWith(
                color: context.tokens.textSecondary,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
