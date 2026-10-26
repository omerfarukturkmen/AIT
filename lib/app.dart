import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

import 'core/state/app_settings_store.dart';
import 'core/theme/app_theme.dart';
import 'features/splash/splash_page.dart';
import 'l10n/app_localizations.dart';

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<AppSettings>(
      valueListenable: AppSettingsStore.settings,
      builder: (context, settings, child) {
        return MaterialApp(
          debugShowCheckedModeBanner: false,
          onGenerateTitle: (context) => AppLocalizations.of(context).appName,
          theme: AppTheme.light(),
          darkTheme: AppTheme.dark(),
          themeMode: settings.themeMode,
          locale: settings.locale,
          supportedLocales: AppLocalizations.supportedLocales,
          localizationsDelegates: const [
            AppLocalizations.delegate,
            GlobalMaterialLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
            GlobalCupertinoLocalizations.delegate,
          ],
          // Snackbars span the screen on phones but stay compact and centered
          // on wide screens.
          builder: (context, child) {
            final width = MediaQuery.sizeOf(context).width;
            if (width < 600) return child!;
            final theme = Theme.of(context);
            return Theme(
              data: theme.copyWith(
                snackBarTheme: theme.snackBarTheme.copyWith(width: 480),
              ),
              child: child!,
            );
          },
          home: const SplashPage(),
        );
      },
    );
  }
}

extension L10nContext on BuildContext {
  AppLocalizations get l10n => AppLocalizations.of(this);
}
