import 'dart:ui';

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class AppSettings {
  final ThemeMode themeMode;

  /// 'tr' or 'en'; drives both the interface and the voice language.
  final String languageCode;
  final bool voiceFeedbackEnabled;

  const AppSettings({
    required this.themeMode,
    required this.languageCode,
    required this.voiceFeedbackEnabled,
  });

  Locale get locale => Locale(languageCode);

  /// Text-to-speech voice for the current language.
  String get ttsLanguage => languageCode == 'tr' ? 'tr-TR' : 'en-US';

  AppSettings copyWith({
    ThemeMode? themeMode,
    String? languageCode,
    bool? voiceFeedbackEnabled,
  }) {
    return AppSettings(
      themeMode: themeMode ?? this.themeMode,
      languageCode: languageCode ?? this.languageCode,
      voiceFeedbackEnabled: voiceFeedbackEnabled ?? this.voiceFeedbackEnabled,
    );
  }
}

/// Device-wide preferences, persisted with shared_preferences.
class AppSettingsStore {
  static const _themeKey = 'settings.theme';
  static const _languageKey = 'settings.language';
  static const _voiceKey = 'settings.voice';

  static const supportedLanguages = ['tr', 'en'];

  static final ValueNotifier<AppSettings> settings = ValueNotifier(
    AppSettings(
      // The brand is built on black, so new installs start dark.
      themeMode: ThemeMode.dark,
      languageCode: _deviceLanguage(),
      voiceFeedbackEnabled: true,
    ),
  );

  static String _deviceLanguage() {
    final code = PlatformDispatcher.instance.locale.languageCode;
    return supportedLanguages.contains(code) ? code : 'en';
  }

  static Future<void> load() async {
    final prefs = await SharedPreferences.getInstance();
    final theme = prefs.getString(_themeKey);
    final language = prefs.getString(_languageKey);
    settings.value = settings.value.copyWith(
      themeMode: ThemeMode.values
          .where((mode) => mode.name == theme)
          .firstOrNull,
      languageCode: supportedLanguages.contains(language) ? language : null,
      voiceFeedbackEnabled: prefs.getBool(_voiceKey),
    );
  }

  static Future<void> setThemeMode(ThemeMode mode) async {
    settings.value = settings.value.copyWith(themeMode: mode);
    await (await SharedPreferences.getInstance()).setString(
      _themeKey,
      mode.name,
    );
  }

  static Future<void> setLanguage(String languageCode) async {
    settings.value = settings.value.copyWith(languageCode: languageCode);
    await (await SharedPreferences.getInstance()).setString(
      _languageKey,
      languageCode,
    );
  }

  static Future<void> setVoiceFeedback(bool enabled) async {
    settings.value = settings.value.copyWith(voiceFeedbackEnabled: enabled);
    await (await SharedPreferences.getInstance()).setBool(_voiceKey, enabled);
  }
}
