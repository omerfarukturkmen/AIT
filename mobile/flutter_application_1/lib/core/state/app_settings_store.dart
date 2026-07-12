import 'package:flutter/foundation.dart';

class AppSettings {
  final bool voiceFeedbackEnabled;
  final String languageCode;
  final int feedbackIntervalSeconds;
  final bool demoModeEnabled;
  final bool backendReady;
  final bool isDarkMode;

  const AppSettings({
    required this.voiceFeedbackEnabled,
    required this.languageCode,
    required this.feedbackIntervalSeconds,
    required this.demoModeEnabled,
    required this.backendReady,
    required this.isDarkMode,
  });

  AppSettings copyWith({
    bool? voiceFeedbackEnabled,
    String? languageCode,
    int? feedbackIntervalSeconds,
    bool? demoModeEnabled,
    bool? backendReady,
    bool? isDarkMode,
  }) {
    return AppSettings(
      voiceFeedbackEnabled: voiceFeedbackEnabled ?? this.voiceFeedbackEnabled,
      languageCode: languageCode ?? this.languageCode,
      feedbackIntervalSeconds:
          feedbackIntervalSeconds ?? this.feedbackIntervalSeconds,
      demoModeEnabled: demoModeEnabled ?? this.demoModeEnabled,
      backendReady: backendReady ?? this.backendReady,
      isDarkMode: isDarkMode ?? this.isDarkMode,
    );
  }
}

class AppSettingsStore {
  static final ValueNotifier<AppSettings> settings = ValueNotifier<AppSettings>(
    const AppSettings(
      voiceFeedbackEnabled: true,
      languageCode: 'tr-TR',
      feedbackIntervalSeconds: 2,
      demoModeEnabled: true,
      backendReady: false,
      isDarkMode: true,
    ),
  );

  static void updateVoiceFeedback(bool value) {
    settings.value = settings.value.copyWith(voiceFeedbackEnabled: value);
  }

  static void updateLanguage(String languageCode) {
    settings.value = settings.value.copyWith(languageCode: languageCode);
  }

  static void updateFeedbackInterval(int seconds) {
    settings.value = settings.value.copyWith(feedbackIntervalSeconds: seconds);
  }

  static void updateDemoMode(bool value) {
    settings.value = settings.value.copyWith(demoModeEnabled: value);
  }

  static void updateBackendReady(bool value) {
    settings.value = settings.value.copyWith(backendReady: value);
  }

  static void updateThemeMode(bool isDarkMode) {
    settings.value = settings.value.copyWith(isDarkMode: isDarkMode);
  }
}
