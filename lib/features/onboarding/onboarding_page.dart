import 'package:flutter/material.dart';

import '../../app.dart';
import '../../core/state/app_settings_store.dart';
import '../../core/state/auth_store.dart';
import '../../core/state/onboarding_store.dart';
import '../../core/theme/app_theme.dart';
import '../../widgets/common.dart';
import '../auth/auth_page.dart';
import '../navigation/main_navigation_page.dart';

class OnboardingPage extends StatefulWidget {
  const OnboardingPage({super.key});

  @override
  State<OnboardingPage> createState() => _OnboardingPageState();
}

class _OnboardingPageState extends State<OnboardingPage> {
  final _controller = PageController();
  int _index = 0;

  static const _pageCount = 3;

  bool get _isLast => _index == _pageCount - 1;

  Future<void> _finish() async {
    await OnboardingStore.markAsSeen();
    if (!mounted) return;
    Navigator.of(context).pushReplacement(
      MaterialPageRoute(
        builder: (_) => AuthStore.isSignedIn
            ? const MainNavigationPage()
            : const AuthPage(),
      ),
    );
  }

  void _next() {
    if (_isLast) {
      _finish();
      return;
    }
    _controller.nextPage(
      duration: const Duration(milliseconds: 320),
      curve: Curves.easeOutCubic,
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final pages = [
      (
        Icons.videocam_rounded,
        l10n.onboardingCaptureTitle,
        l10n.onboardingCaptureBody,
      ),
      (
        Icons.insights_rounded,
        l10n.onboardingAnalyzeTitle,
        l10n.onboardingAnalyzeBody,
      ),
      (
        Icons.trending_up_rounded,
        l10n.onboardingProgressTitle,
        l10n.onboardingProgressBody,
      ),
    ];

    return Scaffold(
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 520),
            child: Padding(
              padding: const EdgeInsets.fromLTRB(
                Gap.page,
                Gap.md,
                Gap.page,
                Gap.xl,
              ),
              child: Column(
                children: [
                  Row(
                    children: [
                      const BrandMark(size: 36),
                      const SizedBox(width: Gap.md),
                      // Shrinks instead of overflowing on narrow screens or large text.
                      const Expanded(
                        child: Align(
                          alignment: AlignmentDirectional.centerStart,
                          child: FittedBox(
                            fit: BoxFit.scaleDown,
                            child: Wordmark(size: 22),
                          ),
                        ),
                      ),
                      const _LanguageToggle(),
                      TextButton(
                        onPressed: _finish,
                        child: Text(l10n.onboardingSkip),
                      ),
                    ],
                  ),
                  Expanded(
                    child: PageView.builder(
                      controller: _controller,
                      itemCount: _pageCount,
                      onPageChanged: (index) => setState(() => _index = index),
                      itemBuilder: (context, index) {
                        final (icon, title, body) = pages[index];
                        return _OnboardingSlide(
                          icon: icon,
                          title: title,
                          body: body,
                        );
                      },
                    ),
                  ),
                  _PageDots(count: _pageCount, index: _index),
                  const SizedBox(height: Gap.xl),
                  SizedBox(
                    width: double.infinity,
                    child: FilledButton(
                      onPressed: _next,
                      child: Text(
                        _isLast ? l10n.onboardingStart : l10n.commonContinue,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _OnboardingSlide extends StatelessWidget {
  final IconData icon;
  final String title;
  final String body;

  const _OnboardingSlide({
    required this.icon,
    required this.title,
    required this.body,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Container(
          width: 120,
          height: 120,
          decoration: BoxDecoration(
            color: context.colors.primaryContainer,
            borderRadius: BorderRadius.circular(36),
          ),
          child: Icon(icon, size: 56, color: context.colors.onPrimaryContainer),
        ),
        const SizedBox(height: Gap.xxl),
        Text(
          title,
          textAlign: TextAlign.center,
          style: context.text.headlineMedium,
        ),
        const SizedBox(height: Gap.md),
        Text(
          body,
          textAlign: TextAlign.center,
          style: context.text.bodyLarge?.copyWith(
            color: context.tokens.textSecondary,
          ),
        ),
      ],
    );
  }
}

class _PageDots extends StatelessWidget {
  final int count;
  final int index;

  const _PageDots({required this.count, required this.index});

  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: '${index + 1} / $count',
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          for (var i = 0; i < count; i++)
            AnimatedContainer(
              duration: const Duration(milliseconds: 200),
              margin: const EdgeInsets.symmetric(horizontal: 3),
              width: i == index ? 22 : 8,
              height: 8,
              decoration: BoxDecoration(
                color: i == index
                    ? context.colors.primary
                    : context.tokens.border,
                borderRadius: BorderRadius.circular(4),
              ),
            ),
        ],
      ),
    );
  }
}

/// Compact TR / EN switch for screens shown before sign-in.
class _LanguageToggle extends StatelessWidget {
  const _LanguageToggle();

  @override
  Widget build(BuildContext context) {
    final current = AppSettingsStore.settings.value.languageCode;
    final next = current == 'tr' ? 'en' : 'tr';
    return TextButton(
      onPressed: () => AppSettingsStore.setLanguage(next),
      child: Text(
        next.toUpperCase(),
        semanticsLabel: next == 'tr' ? 'Türkçe' : 'English',
      ),
    );
  }
}
