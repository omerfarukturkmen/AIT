import 'package:flutter/material.dart';

/// Tabs in the bottom bar / side rail. Progress, history and settings live in
/// the menu on the right (see AppMenuDrawer).
enum AppTab { home, program, profile }

class NavigationStore {
  static final ValueNotifier<AppTab> selected = ValueNotifier(AppTab.home);

  /// Key of the app shell's Scaffold, which owns the right-hand menu.
  static final GlobalKey<ScaffoldState> shellKey = GlobalKey<ScaffoldState>();

  static void go(AppTab tab) => selected.value = tab;

  static bool get hasMenu => shellKey.currentState?.hasEndDrawer ?? false;

  static void openMenu() => shellKey.currentState?.openEndDrawer();
}
