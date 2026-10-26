import '../l10n/app_localizations.dart';

enum ErrorKind {
  network,
  timeout,
  unauthorized,
  invalidCredentials,
  emailTaken,
  invalidInput,
  invalidCode,
  tooLarge,
  unsupportedMedia,
  rateLimited,
  notConfigured,
  unavailable,
  analysisFailed,
  server,
  unknown,
}

/// Error with a user-safe message in the current language.
///
/// The backend answers in Turkish; its `detail` is shown only for Turkish
/// and never for 5xx responses (those may describe internals).
class AppException implements Exception {
  final ErrorKind kind;
  final String? serverDetail;

  const AppException(this.kind, [this.serverDetail]);

  factory AppException.fromStatus(int status, [String? detail]) {
    final kind = switch (status) {
      400 => ErrorKind.invalidInput,
      401 => ErrorKind.unauthorized,
      409 => ErrorKind.emailTaken,
      413 => ErrorKind.tooLarge,
      415 => ErrorKind.unsupportedMedia,
      422 => ErrorKind.invalidInput,
      429 => ErrorKind.rateLimited,
      503 => ErrorKind.unavailable,
      >= 500 => ErrorKind.server,
      _ => ErrorKind.unknown,
    };
    return AppException(kind, status < 500 ? detail : null);
  }

  String message(AppLocalizations l10n) {
    final detail = serverDetail;
    if (detail != null &&
        detail.isNotEmpty &&
        l10n.localeName.startsWith('tr')) {
      return detail;
    }
    return switch (kind) {
      ErrorKind.network => l10n.errorNetwork,
      ErrorKind.timeout => l10n.errorTimeout,
      ErrorKind.unauthorized => l10n.errorSessionExpired,
      ErrorKind.invalidCredentials => l10n.errorInvalidCredentials,
      ErrorKind.emailTaken => l10n.errorEmailTaken,
      ErrorKind.invalidInput => l10n.errorInvalidInput,
      ErrorKind.invalidCode => l10n.errorInvalidCode,
      ErrorKind.tooLarge => l10n.errorTooLarge,
      ErrorKind.unsupportedMedia => l10n.errorUnsupportedMedia,
      ErrorKind.rateLimited => l10n.errorRateLimited,
      ErrorKind.notConfigured => l10n.errorNotConfigured,
      ErrorKind.unavailable => l10n.errorUnavailable,
      ErrorKind.analysisFailed => l10n.errorAnalysisFailed,
      ErrorKind.server => l10n.errorServer,
      ErrorKind.unknown => l10n.errorUnknown,
    };
  }

  @override
  String toString() => 'AppException($kind)';
}
