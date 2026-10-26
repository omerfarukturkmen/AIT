import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';

import '../../app.dart';
import '../../core/app_exception.dart';
import '../../core/services/auth_service.dart';
import '../../core/services/social_sign_in.dart';
import '../../core/state/auth_store.dart';
import '../../core/theme/app_theme.dart';
import '../../models/auth_session_model.dart';
import '../legal/legal_page.dart';
import 'auth_validators.dart';
import 'widgets/auth_feedback.dart';
import 'widgets/auth_text_field.dart';
import 'widgets/social_auth_buttons.dart';

class RegisterForm extends StatefulWidget {
  final void Function(AuthSession session, String message) onAuthenticated;
  final ValueChanged<SocialProvider> onSocialPressed;
  final VoidCallback onSwitchToLogin;

  const RegisterForm({
    super.key,
    required this.onAuthenticated,
    required this.onSocialPressed,
    required this.onSwitchToLogin,
  });

  @override
  State<RegisterForm> createState() => _RegisterFormState();
}

class _RegisterFormState extends State<RegisterForm> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmController = TextEditingController();
  final _emailFocus = FocusNode();
  final _passwordFocus = FocusNode();
  final _confirmFocus = FocusNode();
  late final TapGestureRecognizer _termsRecognizer;
  late final TapGestureRecognizer _privacyRecognizer;

  AutovalidateMode _autovalidateMode = AutovalidateMode.disabled;
  bool _isLoading = false;
  String? _serverError;

  @override
  void initState() {
    super.initState();
    _termsRecognizer = TapGestureRecognizer()
      ..onTap = () => LegalPage.open(context, LegalDocument.terms);
    _privacyRecognizer = TapGestureRecognizer()
      ..onTap = () => LegalPage.open(context, LegalDocument.privacy);
  }

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    _confirmController.dispose();
    _emailFocus.dispose();
    _passwordFocus.dispose();
    _confirmFocus.dispose();
    _termsRecognizer.dispose();
    _privacyRecognizer.dispose();
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
      final session = await AuthService.register(
        fullName: _nameController.text,
        email: _emailController.text,
        password: _passwordController.text,
      );
      await AuthStore.save(session, remember: true);
      if (!mounted) return;
      widget.onAuthenticated(
        session,
        l10n.authAccountCreated(session.user.firstName),
      );
    } on AppException catch (error) {
      if (mounted) setState(() => _serverError = error.message(l10n));
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
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
              key: const Key('register_name'),
              controller: _nameController,
              label: l10n.authFullName,
              hint: l10n.authFullNameHint,
              icon: Icons.person_outline_rounded,
              keyboardType: TextInputType.name,
              textCapitalization: TextCapitalization.words,
              autofillHints: const [AutofillHints.name],
              maxLength: AuthValidators.maxNameLength,
              validator: validators.fullName,
              enabled: !_isLoading,
              onFieldSubmitted: (_) => _emailFocus.requestFocus(),
            ),
            const SizedBox(height: Gap.lg),
            AuthTextField(
              key: const Key('register_email'),
              controller: _emailController,
              focusNode: _emailFocus,
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
              key: const Key('register_password'),
              controller: _passwordController,
              focusNode: _passwordFocus,
              label: l10n.authPassword,
              icon: Icons.lock_outline_rounded,
              isPassword: true,
              autofillHints: const [AutofillHints.newPassword],
              maxLength: AuthValidators.maxPasswordLength,
              validator: validators.newPassword,
              enabled: !_isLoading,
              onChanged: (_) => setState(() {}),
              onFieldSubmitted: (_) => _confirmFocus.requestFocus(),
            ),
            const SizedBox(height: Gap.sm + 2),
            PasswordRequirements(password: _passwordController.text),
            const SizedBox(height: Gap.lg),
            AuthTextField(
              key: const Key('register_confirm'),
              controller: _confirmController,
              focusNode: _confirmFocus,
              label: l10n.authConfirmPassword,
              icon: Icons.lock_reset_rounded,
              isPassword: true,
              textInputAction: TextInputAction.done,
              autofillHints: const [AutofillHints.newPassword],
              maxLength: AuthValidators.maxPasswordLength,
              validator: (value) =>
                  validators.confirmPassword(value, _passwordController.text),
              enabled: !_isLoading,
              onFieldSubmitted: (_) => _submit(),
            ),
            const SizedBox(height: Gap.md),
            FormField<bool>(
              initialValue: false,
              validator: (accepted) =>
                  accepted == true ? null : l10n.authTermsRequired,
              builder: (field) {
                final linkStyle = TextStyle(
                  color: context.colors.primary,
                  fontWeight: FontWeight.w600,
                );
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Tapping the sentence toggles the box; the policy links
                    // keep their own tap handlers.
                    InkWell(
                      borderRadius: BorderRadius.circular(Radii.sm),
                      onTap: _isLoading
                          ? null
                          : () => field.didChange(!(field.value ?? false)),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Checkbox(
                            key: const Key('register_terms'),
                            value: field.value ?? false,
                            onChanged: _isLoading ? null : field.didChange,
                            isError: field.hasError,
                          ),
                          Expanded(
                            child: Padding(
                              padding: const EdgeInsets.only(top: Gap.md),
                              child: Text.rich(
                                TextSpan(
                                  style: context.text.bodySmall,
                                  children: [
                                    TextSpan(text: l10n.authTermsPrefix),
                                    TextSpan(
                                      text: l10n.legalTermsTitle,
                                      style: linkStyle,
                                      recognizer: _termsRecognizer,
                                    ),
                                    TextSpan(text: l10n.authTermsMiddle),
                                    TextSpan(
                                      text: l10n.legalPrivacyTitle,
                                      style: linkStyle,
                                      recognizer: _privacyRecognizer,
                                    ),
                                    TextSpan(text: l10n.authTermsSuffix),
                                  ],
                                ),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                    if (field.hasError)
                      Padding(
                        padding: const EdgeInsets.only(
                          left: Gap.md + 2,
                          top: 2,
                        ),
                        child: Text(
                          field.errorText!,
                          style: context.text.bodySmall?.copyWith(
                            color: context.colors.error,
                          ),
                        ),
                      ),
                  ],
                );
              },
            ),
            if (_serverError != null) ...[
              const SizedBox(height: Gap.md),
              AuthMessageBanner(message: _serverError!),
            ],
            const SizedBox(height: Gap.lg),
            AuthSubmitButton(
              key: const Key('register_submit'),
              label: l10n.authCreateAccount,
              loadingLabel: l10n.authCreatingAccount,
              isLoading: _isLoading,
              onPressed: _submit,
            ),
            const SizedBox(height: Gap.xl),
            const AuthOrDivider(),
            const SizedBox(height: Gap.xl),
            SocialAuthButtons(
              isSignUp: true,
              enabled: !_isLoading,
              onPressed: widget.onSocialPressed,
            ),
            const SizedBox(height: Gap.lg),
            AuthSwitchPrompt(
              question: l10n.authHaveAccount,
              action: l10n.authSignIn,
              onPressed: _isLoading ? null : widget.onSwitchToLogin,
            ),
          ],
        ),
      ),
    );
  }
}

/// Live checklist of the password rules under the password field.
class PasswordRequirements extends StatelessWidget {
  final String password;

  const PasswordRequirements({super.key, required this.password});

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final rules = [
      (
        l10n.passwordRuleLength(AuthValidators.minPasswordLength),
        password.length >= AuthValidators.minPasswordLength,
      ),
      (l10n.passwordRuleLetter, AuthValidators.hasLetter(password)),
      (l10n.passwordRuleDigit, AuthValidators.hasDigit(password)),
    ];

    return Wrap(
      spacing: Gap.md + 2,
      runSpacing: Gap.xs + 2,
      children: [
        for (final (label, met) in rules)
          Semantics(
            label:
                '$label: ${met ? l10n.passwordRuleMet : l10n.passwordRuleUnmet}',
            excludeSemantics: true,
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  met
                      ? Icons.check_circle_rounded
                      : Icons.radio_button_unchecked_rounded,
                  size: 16,
                  color: met
                      ? context.tokens.success
                      : context.tokens.textTertiary,
                ),
                const SizedBox(width: Gap.xs + 2),
                Text(
                  label,
                  style: context.text.bodySmall?.copyWith(
                    color: met ? context.colors.onSurface : null,
                  ),
                ),
              ],
            ),
          ),
      ],
    );
  }
}
