import 'package:flutter/material.dart';

import '../../../app.dart';
import '../../../core/theme/app_theme.dart';

enum AuthMessageType { error, info, success }

/// Inline message above a form's button (e.g. wrong password). Announced to
/// screen readers when it appears.
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
    final tokens = context.tokens;
    final (color, icon) = switch (type) {
      AuthMessageType.error => (tokens.danger, Icons.error_outline_rounded),
      AuthMessageType.info => (tokens.info, Icons.info_outline_rounded),
      AuthMessageType.success => (
        tokens.success,
        Icons.check_circle_outline_rounded,
      ),
    };

    return Semantics(
      liveRegion: true,
      child: Container(
        padding: const EdgeInsets.symmetric(
          horizontal: Gap.md + 2,
          vertical: Gap.md,
        ),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(Radii.md),
          border: Border.all(color: color.withValues(alpha: 0.35)),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, size: 20, color: color),
            const SizedBox(width: Gap.sm + 2),
            Expanded(child: Text(message, style: context.text.bodyMedium)),
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
    return Row(
      children: [
        const Expanded(child: Divider()),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: Gap.md + 2),
          child: Text(context.l10n.authOr, style: context.text.labelMedium),
        ),
        const Expanded(child: Divider()),
      ],
    );
  }
}

/// "Hesabın yok mu? Kayıt ol" style prompt.
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
    return Wrap(
      alignment: WrapAlignment.center,
      crossAxisAlignment: WrapCrossAlignment.center,
      children: [
        Text(
          question,
          style: context.text.bodyMedium?.copyWith(
            color: context.tokens.textSecondary,
          ),
        ),
        TextButton(onPressed: onPressed, child: Text(action)),
      ],
    );
  }
}
