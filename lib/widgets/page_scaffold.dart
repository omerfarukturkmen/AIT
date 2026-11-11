import 'package:flutter/material.dart';

import '../app.dart';
import '../core/state/navigation_store.dart';
import '../core/theme/app_theme.dart';
import 'common.dart';

/// Standard page: large title, optional subtitle and actions, and a
/// scrollable body constrained to a readable width on wide screens. Pushed
/// pages get a back button; tab pages get the menu button.
class PageScaffold extends StatelessWidget {
  final String title;
  final String? subtitle;
  final List<Widget> actions;
  final List<Widget> children;
  final Future<void> Function()? onRefresh;

  const PageScaffold({
    super.key,
    required this.title,
    required this.children,
    this.subtitle,
    this.actions = const [],
    this.onRefresh,
  });

  static const double maxContentWidth = 720;

  /// Width from which the app shows a side rail instead of a bottom bar.
  static const double wideBreakpoint = 840;

  @override
  Widget build(BuildContext context) {
    // Not ModalRoute.canPop: an open drawer also makes that true.
    final route = ModalRoute.of(context);
    final canPop = route != null && !route.isFirst;
    // Tab pages carry the brand bar (logo, wordmark, menu); on wide screens
    // the side rail shows the logo instead.
    final showBrandBar =
        !canPop && MediaQuery.sizeOf(context).width < wideBreakpoint;
    final list = CustomScrollView(
      physics: const AlwaysScrollableScrollPhysics(),
      slivers: [
        SliverSafeArea(
          bottom: false,
          sliver: SliverPadding(
            padding: const EdgeInsets.fromLTRB(
              Gap.page,
              Gap.lg,
              Gap.page,
              Gap.xxl,
            ),
            sliver: SliverToBoxAdapter(
              child: Center(
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: maxContentWidth),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      if (showBrandBar) ...[
                        const _BrandBar(),
                        const SizedBox(height: Gap.xl),
                      ],
                      if (canPop)
                        const Align(
                          alignment: AlignmentDirectional.centerStart,
                          child: Padding(
                            padding: EdgeInsets.only(bottom: Gap.sm),
                            child: BackButton(),
                          ),
                        ),
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Semantics(
                                  header: true,
                                  child: Text(
                                    title,
                                    style: context.text.headlineMedium,
                                  ),
                                ),
                                if (subtitle != null) ...[
                                  const SizedBox(height: Gap.xs),
                                  Text(
                                    subtitle!,
                                    style: context.text.bodyMedium?.copyWith(
                                      color: context.tokens.textSecondary,
                                    ),
                                  ),
                                ],
                              ],
                            ),
                          ),
                          ...actions,
                          if (!canPop &&
                              !showBrandBar &&
                              NavigationStore.hasMenu)
                            const MenuButton(),
                        ],
                      ),
                      const SizedBox(height: Gap.xl),
                      ...children,
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ],
    );

    return Scaffold(
      body: onRefresh == null
          ? list
          : RefreshIndicator(onRefresh: onRefresh!, child: list),
    );
  }
}

/// Upper-cases with the Turkish dotted/dotless i rules when needed
/// ("analiz" -> "ANALİZ", not "ANALIZ").
String displayUpper(String text, Locale locale) {
  if (locale.languageCode != 'tr') return text.toUpperCase();
  return text.replaceAll('i', 'İ').replaceAll('ı', 'I').toUpperCase();
}

/// Small, letter-spaced label above a group of cards, with an optional
/// trailing action.
class SectionHeader extends StatelessWidget {
  final String title;
  final String? actionLabel;
  final VoidCallback? onAction;

  const SectionHeader({
    super.key,
    required this.title,
    this.actionLabel,
    this.onAction,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: Gap.xl, bottom: Gap.md),
      child: Row(
        children: [
          Expanded(
            child: Semantics(
              header: true,
              child: Text(
                displayUpper(title, Localizations.localeOf(context)),
                style: context.text.labelLarge?.copyWith(
                  fontSize: 12.5,
                  letterSpacing: 1.4,
                  fontWeight: FontWeight.w700,
                  color: context.tokens.textTertiary,
                ),
              ),
            ),
          ),
          if (actionLabel != null)
            TextButton(onPressed: onAction, child: Text(actionLabel!)),
        ],
      ),
    );
  }
}

/// Hamburger button that opens the right-hand menu.
class MenuButton extends StatelessWidget {
  const MenuButton({super.key});

  @override
  Widget build(BuildContext context) {
    return IconButton(
      key: const Key('open_menu'),
      tooltip: context.l10n.menuOpen,
      icon: const Icon(Icons.menu_rounded),
      onPressed: NavigationStore.openMenu,
    );
  }
}

/// Top of every tab page: the AIT COACH logo and the menu button.
class _BrandBar extends StatelessWidget {
  const _BrandBar();

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        const BrandMark(size: 38),
        const SizedBox(width: Gap.md),
        const Expanded(
          child: Align(
            alignment: AlignmentDirectional.centerStart,
            child: FittedBox(fit: BoxFit.scaleDown, child: Wordmark(size: 24)),
          ),
        ),
        if (NavigationStore.hasMenu) const MenuButton(),
      ],
    );
  }
}
