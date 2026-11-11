import 'package:flutter/material.dart';

import '../../app.dart';
import '../../core/state/navigation_store.dart';
import '../../core/theme/app_theme.dart';
import '../../widgets/common.dart';
import '../home/home_page.dart';
import '../profile/profile_page.dart';
import '../program/program_page.dart';
import 'app_menu.dart';

/// App shell: bottom navigation on phones, a side rail on wide screens, and
/// the right-hand menu (progress, history, settings).
class MainNavigationPage extends StatelessWidget {
  const MainNavigationPage({super.key});

  static const double _railBreakpoint = 840;

  static const _pages = [HomePage(), ProgramPage(), ProfilePage()];

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
            key: NavigationStore.shellKey,
            endDrawer: const AppMenuDrawer(),
            body: Row(
              children: [
                Theme(
                  data: _navTheme(),
                  child: NavigationRail(
                    selectedIndex: index,
                    onDestinationSelected: (i) =>
                        NavigationStore.go(AppTab.values[i]),
                    labelType: NavigationRailLabelType.all,
                    backgroundColor: AppTheme.ink,
                    indicatorColor: AppTheme.lime,
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
                ),
                Expanded(child: body),
              ],
            ),
          );
        }

        return Scaffold(
          key: NavigationStore.shellKey,
          endDrawer: const AppMenuDrawer(),
          body: body,
          bottomNavigationBar: Theme(
            data: _navTheme(),
            child: NavigationBar(
              backgroundColor: AppTheme.ink,
              indicatorColor: AppTheme.lime,
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

/// Navigation is always black with a lime pill, as in the logo, in both
/// light and dark mode.
ThemeData _navTheme() {
  final dark = AppTheme.dark();
  const muted = Color(0xFF8E8E93);
  return dark.copyWith(
    navigationBarTheme: dark.navigationBarTheme.copyWith(
      backgroundColor: AppTheme.ink,
      indicatorColor: AppTheme.lime,
      iconTheme: WidgetStateProperty.resolveWith(
        (states) => IconThemeData(
          color: states.contains(WidgetState.selected) ? AppTheme.ink : muted,
        ),
      ),
      labelTextStyle: WidgetStateProperty.resolveWith(
        (states) => TextStyle(
          fontSize: 12,
          fontWeight: states.contains(WidgetState.selected)
              ? FontWeight.w700
              : FontWeight.w500,
          color: states.contains(WidgetState.selected) ? Colors.white : muted,
        ),
      ),
    ),
    navigationRailTheme: dark.navigationRailTheme.copyWith(
      backgroundColor: AppTheme.ink,
      indicatorColor: AppTheme.lime,
      selectedIconTheme: const IconThemeData(color: AppTheme.ink),
      unselectedIconTheme: const IconThemeData(color: muted),
      selectedLabelTextStyle: const TextStyle(
        fontSize: 12,
        fontWeight: FontWeight.w700,
        color: Colors.white,
      ),
      unselectedLabelTextStyle: const TextStyle(fontSize: 12, color: muted),
    ),
  );
}
