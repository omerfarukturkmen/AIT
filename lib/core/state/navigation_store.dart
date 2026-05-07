import 'package:flutter/foundation.dart';

class NavigationStore {
  static final ValueNotifier<int> selectedIndex = ValueNotifier<int>(0);

  static void setIndex(int index) {
    selectedIndex.value = index;
  }

  static void goHome() {
    selectedIndex.value = 0;
  }

  static void goProgram() {
    selectedIndex.value = 1;
  }

  static void goProgress() {
    selectedIndex.value = 2;
  }

  static void goHistory() {
    selectedIndex.value = 3;
  }

  static void goProfile() {
    selectedIndex.value = 4;
  }

  static void goSettings() {
    selectedIndex.value = 5;
  }
}
