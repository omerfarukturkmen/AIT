import 'package:flutter/material.dart';

import '../../core/constants/app_colors.dart';
import '../../core/services/auth_service.dart';
import '../../models/auth_session_model.dart';
import '../../widgets/glass_card.dart';
import '../../widgets/premium_background.dart';
import '../navigation/main_navigation_page.dart';
import 'login_form.dart';
import 'register_form.dart';
import 'widgets/auth_palette.dart';

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

  void _switchTo(AuthMode mode) => setState(() => _mode = mode);

  void _onAuthenticated(AuthSession session, String message) {
    final messenger = ScaffoldMessenger.of(context);
    Navigator.of(context).pushAndRemoveUntil(
      MaterialPageRoute(
        builder: widget.homeBuilder ?? (_) => const MainNavigationPage(),
      ),
      (_) => false,
    );
    messenger.showSnackBar(
      SnackBar(
        content: Row(
          children: [
            const Icon(Icons.check_circle_rounded, color: AppColors.neonGreen),
            const SizedBox(width: 10),
            Expanded(child: Text(message)),
          ],
        ),
      ),
    );
  }

  Future<void> _onSocialPressed(SocialAuthProvider provider) async {
    final messenger = ScaffoldMessenger.of(context);
    try {
      final session = await AuthService.signInWithProvider(provider);
      if (!mounted) return;
      _onAuthenticated(session, 'Hoş geldin, ${session.user.firstName}!');
    } on AuthException catch (error) {
      messenger
        ..hideCurrentSnackBar()
        ..showSnackBar(
          SnackBar(
            content: Row(
              children: [
                const Icon(
                  Icons.info_outline_rounded,
                  color: AppColors.electricBlue,
                ),
                const SizedBox(width: 10),
                Expanded(child: Text(error.message)),
              ],
            ),
          ),
        );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: PremiumBackground(
        child: SafeArea(
          child: LayoutBuilder(
            builder: (context, constraints) {
              final isWide = constraints.maxWidth >= _wideBreakpoint;
              final card = _buildFormCard(context, compact: !isWide);

              return SingleChildScrollView(
                keyboardDismissBehavior:
                    ScrollViewKeyboardDismissBehavior.onDrag,
                padding: EdgeInsets.symmetric(
                  horizontal: isWide ? 48 : 16,
                  vertical: isWide ? 40 : 20,
                ),
                child: ConstrainedBox(
                  constraints: BoxConstraints(
                    minHeight: constraints.maxHeight - (isWide ? 80 : 40),
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
                                const SizedBox(height: 20),
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
      ),
    );
  }

  Widget _buildFormCard(BuildContext context, {required bool compact}) {
    final palette = AuthPalette.of(context);
    final isLogin = _mode == AuthMode.login;

    return GlassCard(
      enableHover: false,
      radius: 24,
      padding: EdgeInsets.fromLTRB(
        compact ? 20 : 32,
        compact ? 26 : 34,
        compact ? 20 : 32,
        compact ? 14 : 20,
      ),
      child: AnimatedSize(
        duration: const Duration(milliseconds: 260),
        curve: Curves.easeOutCubic,
        alignment: Alignment.topCenter,
        child: AnimatedSwitcher(
          duration: const Duration(milliseconds: 240),
          switchInCurve: Curves.easeOutCubic,
          switchOutCurve: Curves.easeInCubic,
          transitionBuilder: (child, animation) => FadeTransition(
            opacity: animation,
            child: SlideTransition(
              position: Tween(
                begin: const Offset(0, 0.02),
                end: Offset.zero,
              ).animate(animation),
              child: child,
            ),
          ),
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
                  isLogin ? 'Tekrar hoş geldin' : 'Hesabını oluştur',
                  style: TextStyle(
                    color: palette.text,
                    fontSize: compact ? 24 : 28,
                    fontWeight: FontWeight.w800,
                    letterSpacing: -0.4,
                  ),
                ),
              ),
              const SizedBox(height: 8),
              Text(
                isLogin
                    ? 'Antrenmanlarına kaldığın yerden devam etmek için '
                          'hesabına giriş yap.'
                    : 'Form analizlerini kaydet, ilerlemeni her cihazdan '
                          'takip et.',
                style: TextStyle(
                  color: palette.textMuted,
                  fontSize: 14.5,
                  height: 1.45,
                ),
              ),
              const SizedBox(height: 28),
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

class _BrandMark extends StatelessWidget {
  final double size;

  const _BrandMark({required this.size});

  @override
  Widget build(BuildContext context) {
    return ExcludeSemantics(
      child: Container(
        height: size,
        width: size,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(size * 0.3),
          gradient: const LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [AppColors.primary, Color(0xFF3B82F6)],
          ),
          boxShadow: [
            BoxShadow(
              color: AppColors.primary.withValues(alpha: 0.3),
              blurRadius: size * 0.4,
              offset: Offset(0, size * 0.15),
            ),
          ],
        ),
        child: Icon(
          Icons.fitness_center_rounded,
          color: Colors.white,
          size: size * 0.5,
        ),
      ),
    );
  }
}

class _CompactBrand extends StatelessWidget {
  const _CompactBrand();

  @override
  Widget build(BuildContext context) {
    final palette = AuthPalette.of(context);

    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        const _BrandMark(size: 40),
        const SizedBox(width: 12),
        Text(
          'AIT Fitness',
          style: TextStyle(
            color: palette.text,
            fontSize: 20,
            fontWeight: FontWeight.w800,
            letterSpacing: -0.2,
          ),
        ),
      ],
    );
  }
}

class _BrandPanel extends StatelessWidget {
  const _BrandPanel();

  @override
  Widget build(BuildContext context) {
    final palette = AuthPalette.of(context);

    const features = [
      (
        Icons.videocam_outlined,
        'Canlı form analizi',
        'Kamera karşısında anlık skor ve tekrar takibi.',
      ),
      (
        Icons.insights_rounded,
        'Detaylı video raporları',
        'Yüklediğin videolardan hata ve öneri raporu.',
      ),
      (
        Icons.record_voice_over_outlined,
        'Sesli koçluk',
        'Ekrana bakmadan anlık sesli geri bildirim.',
      ),
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        Row(
          children: [
            const _BrandMark(size: 48),
            const SizedBox(width: 14),
            Text(
              'AIT Fitness',
              style: TextStyle(
                color: palette.text,
                fontSize: 22,
                fontWeight: FontWeight.w800,
              ),
            ),
          ],
        ),
        const SizedBox(height: 40),
        Text(
          'Formunu yapay zekâ ile\nmükemmelleştir.',
          style: TextStyle(
            color: palette.text,
            fontSize: 40,
            height: 1.15,
            fontWeight: FontWeight.w800,
            letterSpacing: -1,
          ),
        ),
        const SizedBox(height: 16),
        Text(
          'Her tekrarda daha doğru hareket et; ilerlemeni tek bir yerden '
          'takip et.',
          style: TextStyle(color: palette.textMuted, fontSize: 16, height: 1.5),
        ),
        const SizedBox(height: 36),
        for (final (icon, title, description) in features)
          Padding(
            padding: const EdgeInsets.only(bottom: 20),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  height: 40,
                  width: 40,
                  decoration: BoxDecoration(
                    color: AppColors.primary.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Icon(icon, color: palette.focus, size: 21),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        style: TextStyle(
                          color: palette.text,
                          fontSize: 15,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const SizedBox(height: 3),
                      Text(
                        description,
                        style: TextStyle(
                          color: palette.textMuted,
                          fontSize: 14,
                          height: 1.4,
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
