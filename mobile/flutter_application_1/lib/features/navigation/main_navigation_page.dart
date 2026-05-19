import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/state/navigation_store.dart';
import '../history/history_page.dart';
import '../home/home_page.dart';
import '../profile/profile_page.dart';
import '../program/program_page.dart';
import '../progress/progress_page.dart';
import '../settings/settings_page.dart';

class MainNavigationPage extends StatelessWidget {
  const MainNavigationPage({super.key});

  static const List<Widget> pages = [
    HomePage(),
    ProgramPage(),
    ProgressPage(),
    HistoryPage(),
    ProfilePage(),
    SettingsPage(),
  ];

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<int>(
      valueListenable: NavigationStore.selectedIndex,
      builder: (context, selectedIndex, child) {
        return Scaffold(
          body: pages[selectedIndex],
          bottomNavigationBar: Container(
            decoration: BoxDecoration(
              color: AppColors.bg2.withValues(alpha: 0.96),
              border: Border(
                top: BorderSide(
                  color: AppColors.purpleGlow.withValues(alpha: 0.25),
                ),
              ),
            ),
            child: BottomNavigationBar(
              currentIndex: selectedIndex,
              backgroundColor: Colors.transparent,
              elevation: 0,
              selectedItemColor: AppColors.purpleGlow,
              unselectedItemColor: AppColors.textSoft,
              type: BottomNavigationBarType.fixed,
              selectedFontSize: 10,
              unselectedFontSize: 9,
              onTap: NavigationStore.setIndex,
              items: const [
                BottomNavigationBarItem(
                  icon: Icon(Icons.home_rounded),
                  label: 'Ana',
                ),
                BottomNavigationBarItem(
                  icon: Icon(Icons.calendar_month_rounded),
                  label: 'Program',
                ),
                BottomNavigationBarItem(
                  icon: Icon(Icons.trending_down_rounded),
                  label: 'Gelişim',
                ),
                BottomNavigationBarItem(
                  icon: Icon(Icons.history_rounded),
                  label: 'Geçmiş',
                ),
                BottomNavigationBarItem(
                  icon: Icon(Icons.person_rounded),
                  label: 'Profil',
                ),
                BottomNavigationBarItem(
                  icon: Icon(Icons.settings_rounded),
                  label: 'Ayarlar',
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}
