class ApiConfig {
  // Override per device, e.g. Android emulator:
  // flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: "http://127.0.0.1:8000",
  );
}
