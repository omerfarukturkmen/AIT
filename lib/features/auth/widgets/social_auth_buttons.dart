import 'package:flutter/material.dart';

import '../../../core/services/auth_service.dart';
import 'auth_palette.dart';

/// Google and Apple buttons styled after each brand's sign-in guidelines:
/// Google uses the four-color "G" on a neutral surface; Apple uses a solid
/// black (light mode) or white (dark mode) button with the Apple logo.
class SocialAuthButtons extends StatelessWidget {
  final bool isSignUp;
  final bool enabled;
  final ValueChanged<SocialAuthProvider> onPressed;

  const SocialAuthButtons({
    super.key,
    required this.isSignUp,
    required this.onPressed,
    this.enabled = true,
  });

  @override
  Widget build(BuildContext context) {
    final palette = AuthPalette.of(context);
    final action = isSignUp ? 'kayıt ol' : 'devam et';

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _SocialButton(
          label: 'Google ile $action',
          logo: const GoogleLogo(size: 18),
          background: palette.isDark ? const Color(0xFF131314) : Colors.white,
          foreground: palette.isDark
              ? const Color(0xFFE3E3E3)
              : const Color(0xFF1F1F1F),
          border: palette.isDark
              ? const Color(0xFF8E918F)
              : const Color(0xFF747775),
          onPressed: enabled
              ? () => onPressed(SocialAuthProvider.google)
              : null,
        ),
        const SizedBox(height: 12),
        _SocialButton(
          label: 'Apple ile $action',
          logo: Icon(
            Icons.apple,
            size: 21,
            color: palette.isDark ? Colors.black : Colors.white,
          ),
          background: palette.isDark ? Colors.white : Colors.black,
          foreground: palette.isDark ? Colors.black : Colors.white,
          border: palette.isDark ? Colors.white : Colors.black,
          onPressed: enabled ? () => onPressed(SocialAuthProvider.apple) : null,
        ),
      ],
    );
  }
}

class _SocialButton extends StatelessWidget {
  final String label;
  final Widget logo;
  final Color background;
  final Color foreground;
  final Color border;
  final VoidCallback? onPressed;

  const _SocialButton({
    required this.label,
    required this.logo,
    required this.background,
    required this.foreground,
    required this.border,
    required this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    return OutlinedButton(
      onPressed: onPressed,
      style: ButtonStyle(
        minimumSize: const WidgetStatePropertyAll(Size.fromHeight(48)),
        padding: const WidgetStatePropertyAll(
          EdgeInsets.symmetric(horizontal: 16),
        ),
        backgroundColor: WidgetStatePropertyAll(background),
        foregroundColor: WidgetStatePropertyAll(foreground),
        overlayColor: WidgetStateProperty.resolveWith(
          (states) => states.contains(WidgetState.pressed)
              ? foreground.withValues(alpha: 0.12)
              : foreground.withValues(alpha: 0.06),
        ),
        side: WidgetStateProperty.resolveWith(
          (states) => BorderSide(
            color: states.contains(WidgetState.focused)
                ? const Color(0xFF7C3AED)
                : border,
            width: states.contains(WidgetState.focused) ? 2 : 1,
          ),
        ),
        shape: WidgetStatePropertyAll(
          RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        ),
        textStyle: const WidgetStatePropertyAll(
          TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
        ),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          SizedBox(width: 22, child: Center(child: logo)),
          const SizedBox(width: 12),
          Flexible(child: Text(label, overflow: TextOverflow.ellipsis)),
        ],
      ),
    );
  }
}

/// Google's standard four-color "G" mark, drawn from the paths of the
/// official sign-in button SVG (48x48 viewBox).
class GoogleLogo extends StatelessWidget {
  final double size;

  const GoogleLogo({super.key, this.size = 18});

  @override
  Widget build(BuildContext context) {
    return SizedBox.square(
      dimension: size,
      child: const CustomPaint(painter: _GoogleLogoPainter()),
    );
  }
}

class _GoogleLogoPainter extends CustomPainter {
  const _GoogleLogoPainter();

  @override
  void paint(Canvas canvas, Size size) {
    canvas.scale(size.width / 48, size.height / 48);

    final red = Path()
      ..moveTo(24, 9.5)
      ..cubicTo(27.54, 9.5, 30.71, 10.72, 33.21, 13.1)
      ..lineTo(40.06, 6.25)
      ..cubicTo(35.9, 2.38, 30.47, 0, 24, 0)
      ..cubicTo(14.62, 0, 6.51, 5.38, 2.56, 13.22)
      ..lineTo(10.54, 19.41)
      ..cubicTo(12.43, 13.72, 17.74, 9.5, 24, 9.5)
      ..close();
    final blue = Path()
      ..moveTo(46.98, 24.55)
      ..cubicTo(46.98, 22.98, 46.83, 21.46, 46.6, 20)
      ..lineTo(24, 20)
      ..lineTo(24, 29.02)
      ..lineTo(36.94, 29.02)
      ..cubicTo(36.36, 31.98, 34.68, 34.5, 32.16, 36.2)
      ..lineTo(39.89, 42.2)
      ..cubicTo(44.4, 38.02, 46.98, 31.84, 46.98, 24.55)
      ..close();
    final yellow = Path()
      ..moveTo(10.53, 28.59)
      ..cubicTo(10.05, 27.14, 9.77, 25.6, 9.77, 24)
      ..cubicTo(9.77, 22.4, 10.04, 20.86, 10.53, 19.41)
      ..lineTo(2.55, 13.22)
      ..cubicTo(0.92, 16.46, 0, 20.12, 0, 24)
      ..cubicTo(0, 27.88, 0.92, 31.54, 2.56, 34.78)
      ..lineTo(10.53, 28.59)
      ..close();
    final green = Path()
      ..moveTo(24, 48)
      ..cubicTo(30.48, 48, 35.93, 45.87, 39.89, 42.19)
      ..lineTo(32.16, 36.19)
      ..cubicTo(30.01, 37.64, 27.24, 38.49, 24, 38.49)
      ..cubicTo(17.74, 38.49, 12.43, 34.27, 10.53, 28.58)
      ..lineTo(2.55, 34.77)
      ..cubicTo(6.51, 42.62, 14.62, 48, 24, 48)
      ..close();

    final paint = Paint()..isAntiAlias = true;
    canvas.drawPath(red, paint..color = const Color(0xFFEA4335));
    canvas.drawPath(blue, paint..color = const Color(0xFF4285F4));
    canvas.drawPath(yellow, paint..color = const Color(0xFFFBBC05));
    canvas.drawPath(green, paint..color = const Color(0xFF34A853));
  }

  @override
  bool shouldRepaint(covariant _GoogleLogoPainter oldDelegate) => false;
}
