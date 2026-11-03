import 'package:flutter/material.dart';

import '../../app.dart';
import '../../core/app_exception.dart';
import '../../core/services/auth_service.dart';
import '../../core/state/app_settings_store.dart';
import '../../core/state/auth_store.dart';
import '../../core/state/navigation_store.dart';
import '../../core/state/user_data.dart';
import '../../core/theme/app_theme.dart';
import '../../models/auth_session_model.dart';
import '../../widgets/app_card.dart';
import '../../widgets/page_scaffold.dart';
import '../auth/auth_page.dart';
import '../auth/password_reset_page.dart';
import '../auth/verify_email_sheet.dart';
import '../legal/legal_page.dart';

const String appVersion = '1.0.0';

class SettingsPage extends StatelessWidget {
  const SettingsPage({super.key});

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    return Scaffold(
      appBar: AppBar(title: Text(l10n.settingsTitle)),
      body: ValueListenableBuilder<AppSettings>(
        valueListenable: AppSettingsStore.settings,
        builder: (context, settings, _) {
          return ListView(
            padding: const EdgeInsets.fromLTRB(Gap.page, 0, Gap.page, Gap.xxl),
            children: [
              Center(
                child: ConstrainedBox(
                  constraints: const BoxConstraints(
                    maxWidth: PageScaffold.maxContentWidth,
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      SectionHeader(title: l10n.settingsAppearance),
                      SegmentedButton<ThemeMode>(
                        showSelectedIcon: false,
                        segments: [
                          ButtonSegment(
                            value: ThemeMode.system,
                            label: Text(l10n.settingsThemeSystem),
                            icon: const Icon(Icons.brightness_auto_outlined),
                          ),
                          ButtonSegment(
                            value: ThemeMode.light,
                            label: Text(l10n.settingsThemeLight),
                            icon: const Icon(Icons.light_mode_outlined),
                          ),
                          ButtonSegment(
                            value: ThemeMode.dark,
                            label: Text(l10n.settingsThemeDark),
                            icon: const Icon(Icons.dark_mode_outlined),
                          ),
                        ],
                        selected: {settings.themeMode},
                        onSelectionChanged: (value) =>
                            AppSettingsStore.setThemeMode(value.first),
                      ),
                      SectionHeader(title: l10n.settingsLanguage),
                      SegmentedButton<String>(
                        showSelectedIcon: false,
                        segments: const [
                          ButtonSegment(value: 'tr', label: Text('Türkçe')),
                          ButtonSegment(value: 'en', label: Text('English')),
                        ],
                        selected: {settings.languageCode},
                        onSelectionChanged: (value) =>
                            AppSettingsStore.setLanguage(value.first),
                      ),
                      SectionHeader(title: l10n.settingsVoice),
                      AppCard(
                        padding: EdgeInsets.zero,
                        child: SwitchListTile(
                          value: settings.voiceFeedbackEnabled,
                          onChanged: AppSettingsStore.setVoiceFeedback,
                          title: Text(l10n.settingsVoiceTitle),
                          subtitle: Text(l10n.settingsVoiceBody),
                        ),
                      ),
                      const _AccountSection(),
                      SectionHeader(title: l10n.settingsLegal),
                      AppCard(
                        padding: EdgeInsets.zero,
                        child: Column(
                          children: [
                            for (final document in LegalDocument.values)
                              ListTile(
                                leading: const Icon(Icons.description_outlined),
                                title: Text(document.title(l10n)),
                                trailing: const Icon(
                                  Icons.chevron_right_rounded,
                                ),
                                onTap: () => LegalPage.open(context, document),
                              ),
                          ],
                        ),
                      ),
                      const SizedBox(height: Gap.xl),
                      Center(
                        child: Text(
                          l10n.settingsVersion(appVersion),
                          style: context.text.bodySmall,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}

class _AccountSection extends StatelessWidget {
  const _AccountSection();

  Future<bool> _confirm(
    BuildContext context, {
    required String title,
    required String body,
    required String action,
    bool destructive = false,
  }) async {
    final result = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(title),
        content: Text(body),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: Text(context.l10n.commonCancel),
          ),
          FilledButton(
            style: destructive
                ? FilledButton.styleFrom(
                    backgroundColor: context.colors.error,
                    foregroundColor: context.colors.onError,
                  )
                : null,
            onPressed: () => Navigator.of(context).pop(true),
            child: Text(action),
          ),
        ],
      ),
    );
    return result == true;
  }

  void _toSignIn(BuildContext context, [String? message]) {
    final messenger = ScaffoldMessenger.of(context);
    NavigationStore.go(AppTab.home);
    Navigator.of(context, rootNavigator: true).pushAndRemoveUntil(
      MaterialPageRoute(builder: (_) => const AuthPage()),
      (_) => false,
    );
    if (message != null) {
      messenger.showSnackBar(SnackBar(content: Text(message)));
    }
  }

  Future<void> _signOut(BuildContext context, {bool allDevices = false}) async {
    final l10n = context.l10n;
    final ok = await _confirm(
      context,
      title: allDevices ? l10n.settingsSignOutAll : l10n.settingsSignOut,
      body: allDevices ? l10n.settingsSignOutAllBody : l10n.settingsSignOutBody,
      action: l10n.settingsSignOut,
    );
    if (!ok || !context.mounted) return;
    await AuthStore.signOut(allDevices: allDevices);
    if (context.mounted) _toSignIn(context);
  }

  Future<void> _deleteAccount(BuildContext context) async {
    final l10n = context.l10n;
    final session = AuthStore.session.value;
    if (session == null) return;
    final ok = await _confirm(
      context,
      title: l10n.settingsDeleteTitle,
      body: l10n.settingsDeleteBody,
      action: l10n.settingsDeleteAction,
      destructive: true,
    );
    if (!ok || !context.mounted) return;

    final messenger = ScaffoldMessenger.of(context);
    try {
      await AuthService.deleteAccount(session.accessToken);
      await UserData.deleteForCurrentUser();
      await AuthStore.signOut();
      if (context.mounted) _toSignIn(context, l10n.settingsDeleted);
    } on AppException catch (error) {
      messenger.showSnackBar(SnackBar(content: Text(error.message(l10n))));
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    return ValueListenableBuilder<AuthSession?>(
      valueListenable: AuthStore.session,
      builder: (context, session, _) {
        final user = session?.user;
        if (user == null) return const SizedBox.shrink();
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            SectionHeader(title: l10n.settingsAccount),
            AppCard(
              padding: EdgeInsets.zero,
              child: Column(
                children: [
                  ListTile(
                    leading: const Icon(Icons.mail_outline_rounded),
                    title: Text(
                      user.email,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    subtitle: Text(
                      user.emailVerified
                          ? l10n.profileVerified
                          : l10n.profileNotVerified,
                    ),
                    trailing: user.emailVerified
                        ? Icon(
                            Icons.verified_rounded,
                            color: context.tokens.success,
                          )
                        : TextButton(
                            onPressed: () => VerifyEmailSheet.show(context),
                            child: Text(l10n.verifyAction),
                          ),
                  ),
                  ListTile(
                    leading: const Icon(Icons.password_rounded),
                    title: Text(l10n.resetSetPassword),
                    trailing: const Icon(Icons.chevron_right_rounded),
                    onTap: () => Navigator.of(context).push(
                      MaterialPageRoute(
                        builder: (_) => PasswordResetPage(
                          initialEmail: user.email,
                          lockEmail: true,
                        ),
                      ),
                    ),
                  ),
                  ListTile(
                    leading: const Icon(Icons.devices_rounded),
                    title: Text(l10n.settingsSignOutAll),
                    onTap: () => _signOut(context, allDevices: true),
                  ),
                  ListTile(
                    key: const Key('settings_sign_out'),
                    leading: const Icon(Icons.logout_rounded),
                    title: Text(l10n.settingsSignOut),
                    onTap: () => _signOut(context),
                  ),
                  ListTile(
                    key: const Key('settings_delete_account'),
                    leading: Icon(
                      Icons.delete_forever_outlined,
                      color: context.colors.error,
                    ),
                    title: Text(
                      l10n.settingsDeleteTitle,
                      style: TextStyle(color: context.colors.error),
                    ),
                    onTap: () => _deleteAccount(context),
                  ),
                ],
              ),
            ),
          ],
        );
      },
    );
  }
}
