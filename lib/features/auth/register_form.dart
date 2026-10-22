import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';

import '../../core/services/auth_service.dart';
import '../../core/state/auth_store.dart';
import '../../models/auth_session_model.dart';
import 'auth_validators.dart';
import 'widgets/auth_feedback.dart';
import 'widgets/auth_palette.dart';
import 'widgets/auth_submit_button.dart';
import 'widgets/auth_text_field.dart';
import 'widgets/social_auth_buttons.dart';

class RegisterForm extends StatefulWidget {
  final void Function(AuthSession session, String message) onAuthenticated;
  final ValueChanged<SocialAuthProvider> onSocialPressed;
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
      ..onTap = () => _showPolicy('Kullanım Koşulları');
    _privacyRecognizer = TapGestureRecognizer()
      ..onTap = () => _showPolicy('Gizlilik Politikası');
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
        'Hesabın oluşturuldu. Hoş geldin, ${session.user.firstName}!',
      );
    } on AuthException catch (error) {
      if (mounted) setState(() => _serverError = error.message);
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _showPolicy(String title) {
    // GEÇİCİ: Yasal metinler henüz eklenmedi. Yayınlandığında bu diyalog
    // ilgili sayfayı açacak şekilde (ör. url_launcher) değiştirilmeli.
    showDialog<void>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(title),
        content: Text(
          '$title metni henüz yayınlanmadı. Yayınlandığında buradan '
          'okuyabileceksin.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Kapat'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final palette = AuthPalette.of(context);

    return Form(
      key: _formKey,
      autovalidateMode: _autovalidateMode,
      child: AutofillGroup(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            AuthTextField(
              key: const Key('register_name'),
              maxLength: AuthValidators.maxNameLength,
              controller: _nameController,
              label: 'Ad soyad',
              hint: 'Ayşe Yılmaz',
              icon: Icons.person_outline_rounded,
              keyboardType: TextInputType.name,
              textCapitalization: TextCapitalization.words,
              autofillHints: const [AutofillHints.name],
              validator: AuthValidators.fullName,
              enabled: !_isLoading,
              onFieldSubmitted: (_) => _emailFocus.requestFocus(),
            ),
            const SizedBox(height: 16),
            AuthTextField(
              key: const Key('register_email'),
              maxLength: AuthValidators.maxEmailLength,
              controller: _emailController,
              focusNode: _emailFocus,
              label: 'E-posta adresi',
              hint: 'ad@ornek.com',
              icon: Icons.mail_outline_rounded,
              keyboardType: TextInputType.emailAddress,
              autofillHints: const [AutofillHints.email],
              validator: AuthValidators.email,
              enabled: !_isLoading,
              onFieldSubmitted: (_) => _passwordFocus.requestFocus(),
            ),
            const SizedBox(height: 16),
            AuthTextField(
              key: const Key('register_password'),
              maxLength: AuthValidators.maxPasswordLength,
              controller: _passwordController,
              focusNode: _passwordFocus,
              label: 'Şifre',
              icon: Icons.lock_outline_rounded,
              isPassword: true,
              autofillHints: const [AutofillHints.newPassword],
              validator: AuthValidators.newPassword,
              enabled: !_isLoading,
              onChanged: (_) => setState(() {}),
              onFieldSubmitted: (_) => _confirmFocus.requestFocus(),
            ),
            const SizedBox(height: 10),
            _PasswordRequirements(password: _passwordController.text),
            const SizedBox(height: 16),
            AuthTextField(
              key: const Key('register_confirm'),
              maxLength: AuthValidators.maxPasswordLength,
              controller: _confirmController,
              focusNode: _confirmFocus,
              label: 'Şifre tekrarı',
              icon: Icons.lock_reset_rounded,
              isPassword: true,
              textInputAction: TextInputAction.done,
              autofillHints: const [AutofillHints.newPassword],
              validator: (value) => AuthValidators.confirmPassword(
                value,
                _passwordController.text,
              ),
              enabled: !_isLoading,
              onFieldSubmitted: (_) => _submit(),
            ),
            const SizedBox(height: 12),
            FormField<bool>(
              initialValue: false,
              validator: (accepted) => accepted == true
                  ? null
                  : 'Devam etmek için koşulları kabul etmelisin.',
              builder: (field) {
                final linkStyle = TextStyle(
                  color: palette.link,
                  fontWeight: FontWeight.w700,
                );

                return Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Tapping the sentence toggles the box; the policy links
                    // keep their own tap handlers.
                    InkWell(
                      borderRadius: BorderRadius.circular(8),
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
                            activeColor: palette.focus,
                            isError: field.hasError,
                            side: BorderSide(
                              color: field.hasError
                                  ? palette.error
                                  : palette.textMuted,
                            ),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(5),
                            ),
                          ),
                          Expanded(
                            child: Padding(
                              padding: const EdgeInsets.only(top: 12),
                              child: Text.rich(
                                TextSpan(
                                  style: TextStyle(
                                    color: palette.textMuted,
                                    fontSize: 13.5,
                                    height: 1.45,
                                  ),
                                  children: [
                                    TextSpan(
                                      text: 'Kullanım Koşulları',
                                      style: linkStyle,
                                      recognizer: _termsRecognizer,
                                    ),
                                    const TextSpan(text: '\'nı ve '),
                                    TextSpan(
                                      text: 'Gizlilik Politikası',
                                      style: linkStyle,
                                      recognizer: _privacyRecognizer,
                                    ),
                                    const TextSpan(
                                      text: '\'nı okudum, kabul ediyorum.',
                                    ),
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
                        padding: const EdgeInsets.only(left: 14, top: 2),
                        child: Text(
                          field.errorText!,
                          style: TextStyle(
                            color: palette.error,
                            fontSize: 12.5,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                  ],
                );
              },
            ),
            if (_serverError != null) ...[
              const SizedBox(height: 12),
              AuthMessageBanner(message: _serverError!),
            ],
            const SizedBox(height: 20),
            AuthSubmitButton(
              key: const Key('register_submit'),
              label: 'Hesap Oluştur',
              loadingLabel: 'Hesap oluşturuluyor…',
              isLoading: _isLoading,
              onPressed: _submit,
            ),
            const SizedBox(height: 24),
            const AuthOrDivider(),
            const SizedBox(height: 24),
            SocialAuthButtons(
              isSignUp: true,
              enabled: !_isLoading,
              onPressed: widget.onSocialPressed,
            ),
            const SizedBox(height: 20),
            AuthSwitchPrompt(
              question: 'Zaten hesabın var mı?',
              action: 'Giriş Yap',
              onPressed: _isLoading ? null : widget.onSwitchToLogin,
            ),
          ],
        ),
      ),
    );
  }
}

class _PasswordRequirements extends StatelessWidget {
  final String password;

  const _PasswordRequirements({required this.password});

  @override
  Widget build(BuildContext context) {
    final palette = AuthPalette.of(context);
    final rules = [
      (
        'En az ${AuthValidators.minPasswordLength} karakter',
        password.length >= AuthValidators.minPasswordLength,
      ),
      ('Bir harf', AuthValidators.hasLetter(password)),
      ('Bir rakam', AuthValidators.hasDigit(password)),
    ];

    return Wrap(
      spacing: 14,
      runSpacing: 6,
      children: [
        for (final (label, met) in rules)
          Semantics(
            label: '$label: ${met ? 'karşılandı' : 'karşılanmadı'}',
            excludeSemantics: true,
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  met
                      ? Icons.check_circle_rounded
                      : Icons.radio_button_unchecked_rounded,
                  size: 16,
                  color: met ? palette.success : palette.textMuted,
                ),
                const SizedBox(width: 6),
                Text(
                  label,
                  style: TextStyle(
                    color: met ? palette.text : palette.textMuted,
                    fontSize: 12.5,
                    fontWeight: met ? FontWeight.w600 : FontWeight.w500,
                  ),
                ),
              ],
            ),
          ),
      ],
    );
  }
}
