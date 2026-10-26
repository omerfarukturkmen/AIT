import 'package:flutter/material.dart';

import '../../app.dart';
import '../../core/state/navigation_store.dart';
import '../../core/theme/app_theme.dart';
import '../../widgets/common.dart';
import '../history/history_page.dart';
import '../home/home_page.dart';
import '../profile/profile_page.dart';
import '../program/program_page.dart';
import '../progress/progress_page.dart';

/// App shell: bottom navigation on phones, a side rail on wide screens.
class MainNavigationPage extends StatelessWidget {
  const MainNavigationPage({super.key});

  static const double _railBreakpoint = 840;

  static const _pages = [
    HomePage(),
    ProgramPage(),
    ProgressPage(),
    HistoryPage(),
    ProfilePage(),
  ];

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final destinations = [
      (Icons.home_outlined, Icons.home_rounded, l10n.navHome),
      (
        Icons.calendar_month_outlined,
        Icons.calendar_month_rounded,
        l10n.navProgram,
      ),
      (Icons.insights_outlined, Icons.insights_rounded, l10n.navProgress),
      (Icons.history_rounded, Icons.history_rounded, l10n.navHistory),
      (Icons.person_outline_rounded, Icons.person_rounded, l10n.navProfile),
    ];

    return ValueListenableBuilder<AppTab>(
      valueListenable: NavigationStore.selected,
      builder: (context, tab, _) {
        final index = tab.index;
        final body = IndexedStack(index: index, children: _pages);
        final isWide = MediaQuery.sizeOf(context).width >= _railBreakpoint;

        if (isWide) {
          return Scaffold(
            body: Row(
              children: [
                NavigationRail(
                  selectedIndex: index,
                  onDestinationSelected: (i) =>
                      NavigationStore.go(AppTab.values[i]),
                  labelType: NavigationRailLabelType.all,
                  backgroundColor: context.colors.surface,
                  indicatorColor: context.colors.primaryContainer,
                  leading: const Padding(
                    padding: EdgeInsets.symmetric(vertical: Gap.lg),
                    child: BrandMark(size: 40),
                  ),
                  destinations: [
                    for (final (icon, selectedIcon, label) in destinations)
                      NavigationRailDestination(
                        icon: Icon(icon),
                        selectedIcon: Icon(selectedIcon),
                        label: Text(label),
                      ),
                  ],
                ),
                const VerticalDivider(width: 1),
                Expanded(child: body),
              ],
            ),
          );
        }

        return Scaffold(
          body: body,
          bottomNavigationBar: DecoratedBox(
            decoration: BoxDecoration(
              border: Border(top: BorderSide(color: context.tokens.border)),
            ),
            child: NavigationBar(
              selectedIndex: index,
              onDestinationSelected: (i) =>
                  NavigationStore.go(AppTab.values[i]),
              destinations: [
                for (final (icon, selectedIcon, label) in destinations)
                  NavigationDestination(
                    icon: Icon(icon),
                    selectedIcon: Icon(selectedIcon),
                    label: label,
                  ),
              ],
            ),
          ),
        );
      },
    );
  }
}
