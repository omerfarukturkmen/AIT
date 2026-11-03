import 'dart:async';

import 'package:flutter/material.dart';

import '../../app.dart';
import '../../core/app_exception.dart';
import '../../core/services/auth_service.dart';
import '../../core/theme/app_theme.dart';
import 'auth_validators.dart';
import 'register_form.dart' show PasswordRequirements;
import 'widgets/auth_feedback.dart';
import 'widgets/auth_text_field.dart';

/// Two steps: request a 6-digit code by e-mail, then set a new password.
/// Also used for "change password" from settings ([lockEmail]).
class PasswordResetPage extends StatefulWidget {
  final String initialEmail;
  final bool lockEmail;

  const PasswordResetPage({
    super.key,
    this.initialEmail = '',
    this.lockEmail = false,
  });

  @override
  State<PasswordResetPage> createState() => _PasswordResetPageState();
}

class _PasswordResetPageState extends State<PasswordResetPage> {
  final _emailForm = GlobalKey<FormState>();
  final _resetForm = GlobalKey<FormState>();
  late final _emailController = TextEditingController(
    text: widget.initialEmail,
  );
  final _codeController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmController = TextEditingController();

  bool _codeSent = false;
  bool _isLoading = false;
  String? _error;
  int _resendSeconds = 0;
  Timer? _resendTimer;

  @override
  void dispose() {
    _emailController.dispose();
    _codeController.dispose();
    _passwordController.dispose();
    _confirmController.dispose();
    _resendTimer?.cancel();
    super.dispose();
  }

  void _startResendCooldown() {
    _resendTimer?.cancel();
    setState(() => _resendSeconds = 60);
    _resendTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (!mounted || _resendSeconds <= 1) {
        timer.cancel();
        if (mounted) setState(() => _resendSeconds = 0);
        return;
      }
      setState(() => _resendSeconds--);
    });
  }

  Future<void> _requestCode() async {
    if (!_emailForm.currentState!.validate()) return;
    final l10n = context.l10n;
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      await AuthService.requestPasswordReset(_emailController.text);
      if (!mounted) return;
      setState(() => _codeSent = true);
      _startResendCooldown();
    } on AppException catch (error) {
      if (mounted) setState(() => _error = error.message(l10n));
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _confirm() async {
    if (!_resetForm.currentState!.validate()) return;
    final l10n = context.l10n;
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      await AuthService.confirmPasswordReset(
        email: _emailController.text,
        code: _codeController.text,
        newPassword: _passwordController.text,
      );
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(l10n.resetSuccess)));
      Navigator.of(context).pop(true);
    } on AppException catch (error) {
      if (mounted) setState(() => _error = error.message(l10n));
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final validators = AuthValidators(l10n);

    return Scaffold(
      appBar: AppBar(title: Text(l10n.resetTitle)),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(Gap.page),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 440),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Text(
                    _codeSent
                        ? l10n.resetCodeSentBody(_emailController.text.trim())
                        : l10n.resetIntro,
                    style: context.text.bodyLarge?.copyWith(
                      color: context.tokens.textSecondary,
                    ),
                  ),
                  const SizedBox(height: Gap.xl),
                  Form(
                    key: _emailForm,
                    child: AuthTextField(
                      key: const Key('reset_email'),
                      controller: _emailController,
                      label: l10n.authEmail,
                      icon: Icons.mail_outline_rounded,
                      keyboardType: TextInputType.emailAddress,
                      autofillHints: const [AutofillHints.email],
                      maxLength: AuthValidators.maxEmailLength,
                      validator: validators.email,
                      enabled: !_isLoading && !_codeSent && !widget.lockEmail,
                      textInputAction: TextInputAction.done,
                      onFieldSubmitted: (_) => _requestCode(),
                    ),
                  ),
                  if (_codeSent) ...[
                    const SizedBox(height: Gap.lg),
                    Form(
                      key: _resetForm,
                      child: AutofillGroup(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            AuthTextField(
                              key: const Key('reset_code'),
                              controller: _codeController,
                              label: l10n.resetCode,
                              hint: '123456',
                              icon: Icons.pin_outlined,
                              keyboardType: TextInputType.number,
                              autofillHints: const [AutofillHints.oneTimeCode],
                              maxLength: 6,
                              validator: validators.code,
                              enabled: !_isLoading,
                            ),
                            const SizedBox(height: Gap.lg),
                            AuthTextField(
                              key: const Key('reset_password'),
                              controller: _passwordController,
                              label: l10n.resetNewPassword,
                              icon: Icons.lock_outline_rounded,
                              isPassword: true,
                              autofillHints: const [AutofillHints.newPassword],
                              maxLength: AuthValidators.maxPasswordLength,
                              validator: validators.newPassword,
                              enabled: !_isLoading,
                              onChanged: (_) => setState(() {}),
                            ),
                            const SizedBox(height: Gap.sm + 2),
                            PasswordRequirements(
                              password: _passwordController.text,
                            ),
                            const SizedBox(height: Gap.lg),
                            AuthTextField(
                              key: const Key('reset_confirm'),
                              controller: _confirmController,
                              label: l10n.authConfirmPassword,
                              icon: Icons.lock_reset_rounded,
                              isPassword: true,
                              textInputAction: TextInputAction.done,
                              maxLength: AuthValidators.maxPasswordLength,
                              validator: (value) => validators.confirmPassword(
                                value,
                                _passwordController.text,
                              ),
                              enabled: !_isLoading,
                              onFieldSubmitted: (_) => _confirm(),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                  if (_error != null) ...[
                    const SizedBox(height: Gap.lg),
                    AuthMessageBanner(message: _error!),
                  ],
                  const SizedBox(height: Gap.xl),
                  AuthSubmitButton(
                    key: const Key('reset_submit'),
                    label: _codeSent
                        ? l10n.resetSetPassword
                        : l10n.resetSendCode,
                    loadingLabel: l10n.commonPleaseWait,
                    isLoading: _isLoading,
                    onPressed: _codeSent ? _confirm : _requestCode,
                  ),
                  if (_codeSent) ...[
                    const SizedBox(height: Gap.sm),
                    TextButton(
                      onPressed: _isLoading || _resendSeconds > 0
                          ? null
                          : _requestCode,
                      child: Text(
                        _resendSeconds > 0
                            ? l10n.resetResendIn(_resendSeconds)
                            : l10n.resetResend,
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
