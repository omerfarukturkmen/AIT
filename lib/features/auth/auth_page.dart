import 'package:flutter/material.dart';

import '../../app.dart';
import '../../core/app_exception.dart';
import '../../core/services/social_sign_in.dart';
import '../../core/state/auth_store.dart';
import '../../core/state/app_settings_store.dart';
import '../../core/theme/app_theme.dart';
import '../../models/auth_session_model.dart';
import '../../widgets/app_card.dart';
import '../../widgets/common.dart';
import '../navigation/main_navigation_page.dart';
import 'login_form.dart';
import 'register_form.dart';

enum AuthMode { login, register }

class AuthPage extends StatefulWidget {
  final AuthMode initialMode;

  /// Screen opened after a successful sign-in; defaults to the main app.
  final WidgetBuilder? homeBuilder;

  const AuthPage({
    super.key,
    this.initialMode = AuthMode.login,
    this.homeBuilder,
  });

  @override
  State<AuthPage> createState() => _AuthPageState();
}

class _AuthPageState extends State<AuthPage> {
  static const double _wideBreakpoint = 920;

  late AuthMode _mode = widget.initialMode;
  bool _socialInProgress = false;

  void _switchTo(AuthMode mode) => setState(() => _mode = mode);

  void _onAuthenticated(AuthSession session, String message) {
    final messenger = ScaffoldMessenger.of(context);
    Navigator.of(context).pushAndRemoveUntil(
      MaterialPageRoute(
        builder: widget.homeBuilder ?? (_) => const MainNavigationPage(),
      ),
      (_) => false,
    );
    messenger.showSnackBar(SnackBar(content: Text(message)));
  }

  Future<void> _onSocialPressed(SocialProvider provider) async {
    if (_socialInProgress) return;
    final l10n = context.l10n;
    final messenger = ScaffoldMessenger.of(context);
    final providerName = provider == SocialProvider.google ? 'Google' : 'Apple';

    if (!SocialSignIn.isAvailable(provider)) {
      messenger
        ..hideCurrentSnackBar()
        ..showSnackBar(
          SnackBar(content: Text(l10n.authSocialNotConfigured(providerName))),
        );
      return;
    }

    setState(() => _socialInProgress = true);
    try {
      final session = await SocialSignIn.signIn(provider);
      if (session == null || !mounted) return; // cancelled
      await AuthStore.save(session, remember: true);
      if (!mounted) return;
      _onAuthenticated(session, l10n.authWelcomeBack(session.user.firstName));
    } on AppException catch (error) {
      messenger
        ..hideCurrentSnackBar()
        ..showSnackBar(SnackBar(content: Text(error.message(l10n))));
    } finally {
      if (mounted) setState(() => _socialInProgress = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) {
            final isWide = constraints.maxWidth >= _wideBreakpoint;
            final card = _buildFormCard(context, compact: !isWide);

            return SingleChildScrollView(
              keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
              padding: EdgeInsets.symmetric(
                horizontal: isWide ? 48 : Gap.lg,
                vertical: isWide ? 40 : Gap.lg,
              ),
              child: ConstrainedBox(
                constraints: BoxConstraints(
                  minHeight: constraints.maxHeight - (isWide ? 80 : 32),
                ),
                child: Center(
                  child: isWide
                      ? ConstrainedBox(
                          constraints: const BoxConstraints(maxWidth: 1080),
                          child: Row(
                            children: [
                              const Expanded(child: _BrandPanel()),
                              const SizedBox(width: 56),
                              SizedBox(width: 460, child: card),
                            ],
                          ),
                        )
                      : ConstrainedBox(
                          constraints: const BoxConstraints(maxWidth: 460),
                          child: Column(
                            children: [
                              const _CompactBrand(),
                              const SizedBox(height: Gap.lg),
                              card,
                            ],
                          ),
                        ),
                ),
              ),
            );
          },
        ),
      ),
    );
  }

  Widget _buildFormCard(BuildContext context, {required bool compact}) {
    final l10n = context.l10n;
    final isLogin = _mode == AuthMode.login;

    return AppCard(
      padding: EdgeInsets.fromLTRB(
        compact ? Gap.lg + 4 : 32,
        compact ? Gap.xl : 34,
        compact ? Gap.lg + 4 : 32,
        compact ? Gap.md : Gap.lg,
      ),
      child: AnimatedSize(
        duration: const Duration(milliseconds: 240),
        curve: Curves.easeOutCubic,
        alignment: Alignment.topCenter,
        child: AnimatedSwitcher(
          duration: const Duration(milliseconds: 220),
          transitionBuilder: (child, animation) =>
              FadeTransition(opacity: animation, child: child),
          layoutBuilder: (current, previous) => Stack(
            alignment: Alignment.topCenter,
            children: [...previous, ?current],
          ),
          child: Column(
            key: ValueKey(_mode),
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Semantics(
                header: true,
                child: Text(
                  isLogin ? l10n.authLoginTitle : l10n.authRegisterTitle,
                  style: compact
                      ? context.text.headlineSmall
                      : context.text.headlineMedium,
                ),
              ),
              const SizedBox(height: Gap.sm),
              Text(
                isLogin ? l10n.authLoginSubtitle : l10n.authRegisterSubtitle,
                style: context.text.bodyMedium?.copyWith(
                  color: context.tokens.textSecondary,
                ),
              ),
              const SizedBox(height: Gap.xl),
              if (isLogin)
                LoginForm(
                  onAuthenticated: _onAuthenticated,
                  onSocialPressed: _onSocialPressed,
                  onSwitchToRegister: () => _switchTo(AuthMode.register),
                )
              else
                RegisterForm(
                  onAuthenticated: _onAuthenticated,
                  onSocialPressed: _onSocialPressed,
                  onSwitchToLogin: () => _switchTo(AuthMode.login),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

class _CompactBrand extends StatelessWidget {
  const _CompactBrand();

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        const BrandMark(size: 36),
        const SizedBox(width: Gap.md),
        Text(context.l10n.appName, style: context.text.titleLarge),
        const Spacer(),
        const _LanguageButton(),
      ],
    );
  }
}

class _LanguageButton extends StatelessWidget {
  const _LanguageButton();

  @override
  Widget build(BuildContext context) {
    final next = AppSettingsStore.settings.value.languageCode == 'tr'
        ? 'en'
        : 'tr';
    return TextButton.icon(
      onPressed: () => AppSettingsStore.setLanguage(next),
      icon: const Icon(Icons.language_rounded, size: 18),
      label: Text(next.toUpperCase()),
    );
  }
}

class _BrandPanel extends StatelessWidget {
  const _BrandPanel();

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final features = [
      (
        Icons.videocam_outlined,
        l10n.authFeatureCaptureTitle,
        l10n.authFeatureCaptureBody,
      ),
      (
        Icons.insights_rounded,
        l10n.authFeatureFeedbackTitle,
        l10n.authFeatureFeedbackBody,
      ),
      (
        Icons.trending_up_rounded,
        l10n.authFeatureProgressTitle,
        l10n.authFeatureProgressBody,
      ),
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        Row(
          children: [
            const BrandMark(size: 44),
            const SizedBox(width: Gap.md + 2),
            Text(l10n.appName, style: context.text.headlineSmall),
            const Spacer(),
            const _LanguageButton(),
          ],
        ),
        const SizedBox(height: 40),
        Text(
          l10n.authHeroTitle,
          style: context.text.displaySmall?.copyWith(fontSize: 40),
        ),
        const SizedBox(height: Gap.lg),
        Text(
          l10n.authHeroBody,
          style: context.text.bodyLarge?.copyWith(
            color: context.tokens.textSecondary,
          ),
        ),
        const SizedBox(height: 36),
        for (final (icon, title, body) in features)
          Padding(
            padding: const EdgeInsets.only(bottom: Gap.lg + 4),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                IconBadge(icon: icon),
                const SizedBox(width: Gap.md + 2),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(title, style: context.text.titleSmall),
                      const SizedBox(height: 2),
                      Text(
                        body,
                        style: context.text.bodyMedium?.copyWith(
                          color: context.tokens.textSecondary,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
      ],
    );
  }
}
