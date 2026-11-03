import '../../l10n/app_localizations.dart';

/// Form rules for the auth screens. Kept in sync with backend/auth.py.
class AuthValidators {
  final AppLocalizations l10n;

  const AuthValidators(this.l10n);

  static final RegExp _emailPattern = RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$');
  static final RegExp _letterPattern = RegExp(r'[A-Za-zÇĞİÖŞÜçğıöşü]');
  static final RegExp _digitPattern = RegExp(r'\d');

  static const int minPasswordLength = 8;
  static const int maxPasswordLength = 128;
  static const int maxNameLength = 100;
  static const int maxEmailLength = 254;

  String? fullName(String? value) {
    final name = (value ?? '').trim();
    if (name.isEmpty) return l10n.validationNameRequired;
    final parts = name.split(RegExp(r'\s+'));
    if (parts.length < 2 || parts.any((part) => part.length < 2)) {
      return l10n.validationNameFull;
    }
    return null;
  }

  String? email(String? value) {
    final email = (value ?? '').trim();
    if (email.isEmpty) return l10n.validationEmailRequired;
    if (!_emailPattern.hasMatch(email)) return l10n.validationEmailInvalid;
    return null;
  }

  String? loginPassword(String? value) {
    if ((value ?? '').isEmpty) return l10n.validationPasswordRequired;
    return null;
  }

  String? newPassword(String? value) {
    final password = value ?? '';
    if (password.isEmpty) return l10n.validationPasswordRequired;
    if (password.length < minPasswordLength) {
      return l10n.validationPasswordMin(minPasswordLength);
    }
    if (password.length > maxPasswordLength) {
      return l10n.validationPasswordMax(maxPasswordLength);
    }
    if (!hasLetter(password) || !hasDigit(password)) {
      return l10n.validationPasswordLetterDigit;
    }
    return null;
  }

  String? confirmPassword(String? value, String original) {
    if ((value ?? '').isEmpty) return l10n.validationConfirmRequired;
    if (value != original) return l10n.validationPasswordsMismatch;
    return null;
  }

  String? code(String? value) {
    final code = (value ?? '').trim();
    if (!RegExp(r'^\d{6}$').hasMatch(code)) return l10n.validationCode;
    return null;
  }

  static bool hasLetter(String value) => _letterPattern.hasMatch(value);

  static bool hasDigit(String value) => _digitPattern.hasMatch(value);
}
