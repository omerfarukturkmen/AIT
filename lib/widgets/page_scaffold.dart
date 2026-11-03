import 'package:flutter/material.dart';

import '../app.dart';
import '../core/state/navigation_store.dart';
import '../core/theme/app_theme.dart';

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

  @override
  Widget build(BuildContext context) {
    // Not ModalRoute.canPop: an open drawer also makes that true.
    final route = ModalRoute.of(context);
    final canPop = route != null && !route.isFirst;
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
                          if (!canPop && NavigationStore.hasMenu)
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

/// Small heading above a group of cards, with an optional trailing action.
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
              child: Text(title, style: context.text.titleMedium),
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
