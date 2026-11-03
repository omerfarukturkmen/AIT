import 'package:flutter/material.dart';

import '../../app.dart';
import '../../core/app_exception.dart';
import '../../core/services/auth_service.dart';
import '../../core/services/social_sign_in.dart';
import '../../core/state/auth_store.dart';
import '../../core/theme/app_theme.dart';
import '../../models/auth_session_model.dart';
import 'auth_validators.dart';
import 'password_reset_page.dart';
import 'widgets/auth_feedback.dart';
import 'widgets/auth_text_field.dart';
import 'widgets/social_auth_buttons.dart';

class LoginForm extends StatefulWidget {
  final void Function(AuthSession session, String message) onAuthenticated;
  final ValueChanged<SocialProvider> onSocialPressed;
  final VoidCallback onSwitchToRegister;

  const LoginForm({
    super.key,
    required this.onAuthenticated,
    required this.onSocialPressed,
    required this.onSwitchToRegister,
  });

  @override
  State<LoginForm> createState() => _LoginFormState();
}

class _LoginFormState extends State<LoginForm> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _passwordFocus = FocusNode();

  AutovalidateMode _autovalidateMode = AutovalidateMode.disabled;
  bool _rememberMe = true;
  bool _isLoading = false;
  String? _serverError;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    _passwordFocus.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (_isLoading) return;
    FocusScope.of(context).unfocus();
    setState(() {
      _serverError = null;
      _autovalidateMode = AutovalidateMode.onUserInteraction;
    });
    if (!_formKey.currentState!.validate()) return;

    final l10n = context.l10n;
    setState(() => _isLoading = true);
    try {
      final session = await AuthService.login(
        email: _emailController.text,
        password: _passwordController.text,
        rememberMe: _rememberMe,
      );
      await AuthStore.save(session, remember: _rememberMe);
      if (!mounted) return;
      widget.onAuthenticated(
        session,
        l10n.authWelcomeBack(session.user.firstName),
      );
    } on AppException catch (error) {
      if (mounted) setState(() => _serverError = error.message(l10n));
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _openPasswordReset() {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => PasswordResetPage(initialEmail: _emailController.text),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final validators = AuthValidators(l10n);

    return Form(
      key: _formKey,
      autovalidateMode: _autovalidateMode,
      child: AutofillGroup(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            AuthTextField(
              key: const Key('login_email'),
              controller: _emailController,
              label: l10n.authEmail,
              hint: l10n.authEmailHint,
              icon: Icons.mail_outline_rounded,
              keyboardType: TextInputType.emailAddress,
              autofillHints: const [AutofillHints.email],
              maxLength: AuthValidators.maxEmailLength,
              validator: validators.email,
              enabled: !_isLoading,
              onFieldSubmitted: (_) => _passwordFocus.requestFocus(),
            ),
            const SizedBox(height: Gap.lg),
            AuthTextField(
              key: const Key('login_password'),
              controller: _passwordController,
              focusNode: _passwordFocus,
              label: l10n.authPassword,
              icon: Icons.lock_outline_rounded,
              isPassword: true,
              textInputAction: TextInputAction.done,
              autofillHints: const [AutofillHints.password],
              maxLength: AuthValidators.maxPasswordLength,
              validator: validators.loginPassword,
              enabled: !_isLoading,
              onFieldSubmitted: (_) => _submit(),
            ),
            const SizedBox(height: Gap.xs),
            Row(
              children: [
                Expanded(
                  child: MergeSemantics(
                    child: InkWell(
                      borderRadius: BorderRadius.circular(Radii.sm),
                      onTap: _isLoading
                          ? null
                          : () => setState(() => _rememberMe = !_rememberMe),
                      child: Row(
                        children: [
                          Checkbox(
                            value: _rememberMe,
                            onChanged: _isLoading
                                ? null
                                : (value) => setState(
                                    () => _rememberMe = value ?? false,
                                  ),
                          ),
                          Flexible(child: Text(l10n.authRememberMe)),
                        ],
                      ),
                    ),
                  ),
                ),
                TextButton(
                  onPressed: _isLoading ? null : _openPasswordReset,
                  child: Text(l10n.authForgotPassword),
                ),
              ],
            ),
            if (_serverError != null) ...[
              const SizedBox(height: Gap.md),
              AuthMessageBanner(message: _serverError!),
            ],
            const SizedBox(height: Gap.lg),
            AuthSubmitButton(
              key: const Key('login_submit'),
              label: l10n.authSignIn,
              loadingLabel: l10n.authSigningIn,
              isLoading: _isLoading,
              onPressed: _submit,
            ),
            const SizedBox(height: Gap.xl),
            const AuthOrDivider(),
            const SizedBox(height: Gap.xl),
            SocialAuthButtons(
              isSignUp: false,
              enabled: !_isLoading,
              onPressed: widget.onSocialPressed,
            ),
            const SizedBox(height: Gap.lg),
            AuthSwitchPrompt(
              question: l10n.authNoAccount,
              action: l10n.authSignUp,
              onPressed: _isLoading ? null : widget.onSwitchToRegister,
            ),
          ],
        ),
      ),
    );
  }
}
