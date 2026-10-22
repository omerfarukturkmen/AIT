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

class LoginForm extends StatefulWidget {
  final void Function(AuthSession session, String message) onAuthenticated;
  final ValueChanged<SocialAuthProvider> onSocialPressed;
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

    setState(() => _isLoading = true);
    try {
      final session = await AuthService.login(
        email: _emailController.text,
        password: _passwordController.text,
      );
      await AuthStore.save(session, remember: _rememberMe);
      if (!mounted) return;
      widget.onAuthenticated(
        session,
        'Tekrar hoş geldin, ${session.user.firstName}!',
      );
    } on AuthException catch (error) {
      if (mounted) setState(() => _serverError = error.message);
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _showForgotPassword() {
    // GEÇİCİ: Backend'de şifre sıfırlama uç noktası (ör. POST
    // /auth/password-reset) ve e-posta gönderimi yok. Eklendiğinde bu
    // diyalog e-posta alıp isteği gönderecek şekilde değiştirilmeli.
    showDialog<void>(
      context: context,
      builder: (context) => AlertDialog(
        icon: const Icon(Icons.lock_reset_rounded),
        title: const Text('Şifre sıfırlama'),
        content: const Text(
          'Şifre sıfırlama bağlantısı gönderme özelliği henüz '
          'kullanılamıyor. Hesabına erişemiyorsan lütfen destek ekibiyle '
          'iletişime geç.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Tamam'),
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
              key: const Key('login_email'),
              controller: _emailController,
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
              key: const Key('login_password'),
              controller: _passwordController,
              focusNode: _passwordFocus,
              label: 'Şifre',
              icon: Icons.lock_outline_rounded,
              isPassword: true,
              textInputAction: TextInputAction.done,
              autofillHints: const [AutofillHints.password],
              validator: AuthValidators.loginPassword,
              enabled: !_isLoading,
              onFieldSubmitted: (_) => _submit(),
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: MergeSemantics(
                    child: InkWell(
                      borderRadius: BorderRadius.circular(8),
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
                            activeColor: palette.focus,
                            side: BorderSide(color: palette.textMuted),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(5),
                            ),
                          ),
                          Flexible(
                            child: Text(
                              'Beni hatırla',
                              style: TextStyle(
                                color: palette.text,
                                fontSize: 14,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
                AuthLinkButton(
                  label: 'Şifremi unuttum',
                  onPressed: _isLoading ? null : _showForgotPassword,
                ),
              ],
            ),
            if (_serverError != null) ...[
              const SizedBox(height: 12),
              AuthMessageBanner(message: _serverError!),
            ],
            const SizedBox(height: 20),
            AuthSubmitButton(
              key: const Key('login_submit'),
              label: 'Giriş Yap',
              loadingLabel: 'Giriş yapılıyor…',
              isLoading: _isLoading,
              onPressed: _submit,
            ),
            const SizedBox(height: 24),
            const AuthOrDivider(),
            const SizedBox(height: 24),
            SocialAuthButtons(
              isSignUp: false,
              enabled: !_isLoading,
              onPressed: widget.onSocialPressed,
            ),
            const SizedBox(height: 20),
            AuthSwitchPrompt(
              question: 'Hesabın yok mu?',
              action: 'Kayıt Ol',
              onPressed: _isLoading ? null : widget.onSwitchToRegister,
            ),
          ],
        ),
      ),
    );
  }
}
