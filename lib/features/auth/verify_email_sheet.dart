import 'dart:async';

import 'package:flutter/material.dart';

import '../../app.dart';
import '../../core/app_exception.dart';
import '../../core/services/auth_service.dart';
import '../../core/state/auth_store.dart';
import '../../core/theme/app_theme.dart';
import 'auth_validators.dart';
import 'widgets/auth_feedback.dart';
import 'widgets/auth_text_field.dart';

/// Bottom sheet to enter the e-mailed verification code. A code is sent at
/// sign-up; "send again" requests a new one.
class VerifyEmailSheet extends StatefulWidget {
  const VerifyEmailSheet({super.key});

  static Future<void> show(BuildContext context) {
    return showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      builder: (_) => const VerifyEmailSheet(),
    );
  }

  @override
  State<VerifyEmailSheet> createState() => _VerifyEmailSheetState();
}

class _VerifyEmailSheetState extends State<VerifyEmailSheet> {
  final _formKey = GlobalKey<FormState>();
  final _codeController = TextEditingController();
  bool _isLoading = false;
  String? _error;
  String? _info;
  int _resendSeconds = 0;
  Timer? _timer;

  @override
  void dispose() {
    _codeController.dispose();
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _resend() async {
    final session = AuthStore.session.value;
    if (session == null) return;
    final l10n = context.l10n;
    setState(() {
      _error = null;
      _info = null;
      _isLoading = true;
    });
    try {
      await AuthService.requestEmailVerification(session.accessToken);
      if (!mounted) return;
      setState(() => _info = l10n.verifyCodeSent);
      _resendSeconds = 60;
      _timer?.cancel();
      _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
        if (!mounted || _resendSeconds <= 1) {
          timer.cancel();
          if (mounted) setState(() => _resendSeconds = 0);
          return;
        }
        setState(() => _resendSeconds--);
      });
    } on AppException catch (error) {
      if (mounted) setState(() => _error = error.message(l10n));
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _verify() async {
    final session = AuthStore.session.value;
    if (session == null || !_formKey.currentState!.validate()) return;
    final l10n = context.l10n;
    final messenger = ScaffoldMessenger.of(context);
    setState(() {
      _error = null;
      _isLoading = true;
    });
    try {
      await AuthService.confirmEmailVerification(
        session.accessToken,
        _codeController.text,
      );
      await AuthStore.updateUser(session.user.copyWith(emailVerified: true));
      if (!mounted) return;
      Navigator.of(context).pop();
      messenger.showSnackBar(SnackBar(content: Text(l10n.verifySuccess)));
    } on AppException catch (error) {
      if (mounted) setState(() => _error = error.message(l10n));
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final email = AuthStore.session.value?.user.email ?? '';

    return Padding(
      padding: EdgeInsets.fromLTRB(
        Gap.page,
        0,
        Gap.page,
        Gap.xl + MediaQuery.viewInsetsOf(context).bottom,
      ),
      child: Form(
        key: _formKey,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(l10n.verifyTitle, style: context.text.titleLarge),
            const SizedBox(height: Gap.sm),
            Text(
              l10n.verifyBody(email),
              style: context.text.bodyMedium?.copyWith(
                color: context.tokens.textSecondary,
              ),
            ),
            const SizedBox(height: Gap.xl),
            AuthTextField(
              key: const Key('verify_code'),
              controller: _codeController,
              label: l10n.resetCode,
              hint: '123456',
              icon: Icons.pin_outlined,
              keyboardType: TextInputType.number,
              autofillHints: const [AutofillHints.oneTimeCode],
              maxLength: 6,
              textInputAction: TextInputAction.done,
              validator: AuthValidators(l10n).code,
              enabled: !_isLoading,
              onFieldSubmitted: (_) => _verify(),
            ),
            if (_error != null || _info != null) ...[
              const SizedBox(height: Gap.md),
              AuthMessageBanner(
                message: _error ?? _info!,
                type: _error != null
                    ? AuthMessageType.error
                    : AuthMessageType.info,
              ),
            ],
            const SizedBox(height: Gap.lg),
            AuthSubmitButton(
              key: const Key('verify_submit'),
              label: l10n.verifyAction,
              loadingLabel: l10n.commonPleaseWait,
              isLoading: _isLoading,
              onPressed: _verify,
            ),
            const SizedBox(height: Gap.sm),
            TextButton(
              onPressed: _isLoading || _resendSeconds > 0 ? null : _resend,
              child: Text(
                _resendSeconds > 0
                    ? l10n.resetResendIn(_resendSeconds)
                    : l10n.verifyResend,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
