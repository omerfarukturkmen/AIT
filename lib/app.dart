import 'package:flutter/material.dart';

import 'core/constants/app_colors.dart';
import 'core/state/app_settings_store.dart';
import 'features/splash/splash_page.dart';

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  ThemeData _darkTheme() {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: AppColors.bg1,
      colorScheme: ColorScheme.fromSeed(
        seedColor: AppColors.primary,
        brightness: Brightness.dark,
      ),
      fontFamily: 'Roboto',
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: true,
        foregroundColor: AppColors.text,
      ),
      textTheme: const TextTheme(
        bodyMedium: TextStyle(color: AppColors.text),
        bodyLarge: TextStyle(color: AppColors.text),
      ),
      snackBarTheme: SnackBarThemeData(
        backgroundColor: AppColors.card,
        contentTextStyle: const TextStyle(
          color: AppColors.text,
          fontWeight: FontWeight.w700,
        ),
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      ),
    );
  }

  ThemeData _lightTheme() {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      scaffoldBackgroundColor: const Color(0xFFEFF4FA),
      colorScheme: ColorScheme.fromSeed(
        seedColor: AppColors.primary,
        brightness: Brightness.light,
        primary: AppColors.primary,
        secondary: AppColors.electricBlue,
        surface: const Color(0xFFF8FAFC),
      ),
      fontFamily: 'Roboto',
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: true,
        foregroundColor: Color(0xFF111827),
      ),
      textTheme: const TextTheme(
        bodyMedium: TextStyle(color: Color(0xFF111827)),
        bodyLarge: TextStyle(color: Color(0xFF111827)),
        titleMedium: TextStyle(color: Color(0xFF111827)),
        titleLarge: TextStyle(color: Color(0xFF111827)),
      ),
      snackBarTheme: SnackBarThemeData(
        backgroundColor: const Color(0xFFFFFFFF),
        contentTextStyle: const TextStyle(
          color: Color(0xFF111827),
          fontWeight: FontWeight.w700,
        ),
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<AppSettings>(
      valueListenable: AppSettingsStore.settings,
      builder: (context, settings, child) {
        return MaterialApp(
          debugShowCheckedModeBanner: false,
          title: 'AIT',
          theme: _lightTheme(),
          darkTheme: _darkTheme(),
          themeMode: settings.isDarkMode ? ThemeMode.dark : ThemeMode.light,
          home: const SplashPage(),
        );
      },
    );
  }
}
