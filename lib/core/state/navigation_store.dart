import 'package:flutter/foundation.dart';

enum AppTab { home, program, progress, history, profile }

class NavigationStore {
  static final ValueNotifier<AppTab> selected = ValueNotifier(AppTab.home);

  static void go(AppTab tab) => selected.value = tab;
}
