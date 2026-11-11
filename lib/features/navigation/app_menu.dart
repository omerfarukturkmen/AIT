import 'package:flutter/material.dart';

import '../../app.dart';
import '../../core/state/auth_store.dart';
import '../../core/theme/app_theme.dart';
import '../../models/auth_session_model.dart';
import '../../widgets/app_card.dart';
import '../../widgets/common.dart';
import '../history/history_page.dart';
import '../progress/progress_page.dart';
import '../settings/settings_page.dart';

/// Pages reached from the right-hand menu.
enum MenuPage { progress, history, settings }

abstract final class AppMenu {
  static Future<void> open(BuildContext context, MenuPage page) {
    return Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => switch (page) {
          MenuPage.progress => const ProgressPage(),
          MenuPage.history => const HistoryPage(),
          MenuPage.settings => const SettingsPage(),
        },
      ),
    );
  }
}

/// Right-hand drawer: a personal greeting and the secondary pages.
class AppMenuDrawer extends StatelessWidget {
  const AppMenuDrawer({super.key});

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final items = [
      (
        MenuPage.progress,
        Icons.insights_rounded,
        l10n.navProgress,
        l10n.menuProgressBody,
      ),
      (
        MenuPage.history,
        Icons.history_rounded,
        l10n.navHistory,
        l10n.menuHistoryBody,
      ),
      (
        MenuPage.settings,
        Icons.settings_outlined,
        l10n.settingsTitle,
        l10n.menuSettingsBody,
      ),
    ];

    return Drawer(
      key: const Key('app_menu'),
      backgroundColor: context.colors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.horizontal(left: Radius.circular(Radii.lg)),
      ),
      child: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Padding(
              padding: const EdgeInsets.all(Gap.lg),
              child: ValueListenableBuilder<AuthSession?>(
                valueListenable: AuthStore.session,
                builder: (context, session, _) =>
                    _MenuHeader(user: session?.user),
              ),
            ),
            for (final (page, icon, title, body) in items)
              Padding(
                padding: const EdgeInsets.symmetric(
                  horizontal: Gap.sm,
                  vertical: 2,
                ),
                child: ListTile(
                  key: Key('menu_${page.name}'),
                  leading: IconBadge(icon: icon, size: 38),
                  title: Text(title, style: context.text.titleSmall),
                  subtitle: Text(body, style: context.text.bodySmall),
                  trailing: Icon(
                    Icons.chevron_right_rounded,
                    color: context.tokens.textTertiary,
                  ),
                  onTap: () {
                    Navigator.of(context).pop();
                    AppMenu.open(context, page);
                  },
                ),
              ),
            const Spacer(),
            const Divider(),
            Padding(
              padding: const EdgeInsets.all(Gap.lg),
              child: Row(
                children: [
                  const BrandMark(size: 28),
                  const SizedBox(width: Gap.sm),
                  // Shrinks instead of overflowing on narrow screens or large text.
                  const Expanded(
                    child: Align(
                      alignment: AlignmentDirectional.centerStart,
                      child: FittedBox(
                        fit: BoxFit.scaleDown,
                        child: Wordmark(size: 16),
                      ),
                    ),
                  ),
                  Text('v$appVersion', style: context.text.labelSmall),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _MenuHeader extends StatelessWidget {
  final AuthUser? user;

  const _MenuHeader({required this.user});

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final user = this.user;
    return HeroCard(
      padding: const EdgeInsets.all(Gap.lg),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 52,
            height: 52,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: Colors.black.withValues(alpha: 0.35),
              border: Border.all(color: AppTheme.lime, width: 1.5),
            ),
            child: user == null
                ? const Icon(Icons.person_rounded, color: AppTheme.lime)
                : Text(
                    user.initials,
                    style: context.text.titleMedium?.copyWith(
                      color: AppTheme.lime,
                    ),
                  ),
          ),
          const SizedBox(height: Gap.md),
          Text(
            user == null ? l10n.menuTitle : l10n.homeGreeting(user.firstName),
            style: context.text.titleLarge?.copyWith(
              color: HeroCard.foreground,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            l10n.menuSubtitle,
            style: context.text.bodySmall?.copyWith(color: HeroCard.muted),
          ),
        ],
      ),
    );
  }
}
