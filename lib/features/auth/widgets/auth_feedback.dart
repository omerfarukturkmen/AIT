import 'package:flutter/material.dart';

import 'auth_palette.dart';

enum AuthMessageType { error, info }

/// Inline message shown above the submit button (e.g. wrong password,
/// server unreachable). Announced to screen readers when it appears.
class AuthMessageBanner extends StatelessWidget {
  final String message;
  final AuthMessageType type;

  const AuthMessageBanner({
    super.key,
    required this.message,
    this.type = AuthMessageType.error,
  });

  @override
  Widget build(BuildContext context) {
    final palette = AuthPalette.of(context);
    final color = type == AuthMessageType.error ? palette.error : palette.focus;

    return Semantics(
      liveRegion: true,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        decoration: BoxDecoration(
          color: color.withValues(alpha: palette.isDark ? 0.12 : 0.08),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: color.withValues(alpha: 0.35)),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(
              type == AuthMessageType.error
                  ? Icons.error_outline_rounded
                  : Icons.info_outline_rounded,
              size: 20,
              color: color,
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Text(
                message,
                style: TextStyle(
                  color: palette.text,
                  fontSize: 13.5,
                  height: 1.4,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class AuthOrDivider extends StatelessWidget {
  const AuthOrDivider({super.key});

  @override
  Widget build(BuildContext context) {
    final palette = AuthPalette.of(context);

    return Row(
      children: [
        Expanded(child: Divider(color: palette.divider, thickness: 1)),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 14),
          child: Text(
            'veya',
            style: TextStyle(
              color: palette.textMuted,
              fontSize: 13,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
        Expanded(child: Divider(color: palette.divider, thickness: 1)),
      ],
    );
  }
}

/// Inline text button used for "Kayıt Ol", "Şifremi unuttum" etc.
class AuthLinkButton extends StatelessWidget {
  final String label;
  final VoidCallback? onPressed;

  const AuthLinkButton({super.key, required this.label, this.onPressed});

  @override
  Widget build(BuildContext context) {
    final palette = AuthPalette.of(context);

    return TextButton(
      onPressed: onPressed,
      style: TextButton.styleFrom(
        foregroundColor: palette.link,
        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 8),
        minimumSize: const Size(0, 40),
        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
        textStyle: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700),
      ),
      child: Text(label),
    );
  }
}

class AuthSwitchPrompt extends StatelessWidget {
  final String question;
  final String action;
  final VoidCallback? onPressed;

  const AuthSwitchPrompt({
    super.key,
    required this.question,
    required this.action,
    required this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    final palette = AuthPalette.of(context);

    return Wrap(
      alignment: WrapAlignment.center,
      crossAxisAlignment: WrapCrossAlignment.center,
      children: [
        Text(
          question,
          style: TextStyle(color: palette.textMuted, fontSize: 14),
        ),
        AuthLinkButton(label: action, onPressed: onPressed),
      ],
    );
  }
}
