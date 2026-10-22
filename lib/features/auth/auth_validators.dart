/// Form rules for the auth screens. Kept in sync with backend/auth.py.
class AuthValidators {
  static final RegExp _emailPattern = RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$');
  static final RegExp _letterPattern = RegExp(r'[A-Za-zÇĞİÖŞÜçğıöşü]');
  static final RegExp _digitPattern = RegExp(r'\d');

  static const int minPasswordLength = 8;
  static const int maxPasswordLength = 128;

  static String? fullName(String? value) {
    final parts = (value ?? '').trim().split(RegExp(r'\s+'));
    if ((value ?? '').trim().isEmpty) return 'Ad soyad gerekli.';
    if (parts.length < 2 || parts.any((part) => part.length < 2)) {
      return 'Lütfen adını ve soyadını gir.';
    }
    return null;
  }

  static String? email(String? value) {
    final email = (value ?? '').trim();
    if (email.isEmpty) return 'E-posta adresi gerekli.';
    if (!_emailPattern.hasMatch(email)) {
      return 'Geçerli bir e-posta adresi gir (ör. ad@ornek.com).';
    }
    return null;
  }

  static String? loginPassword(String? value) {
    if ((value ?? '').isEmpty) return 'Şifre gerekli.';
    return null;
  }

  static String? newPassword(String? value) {
    final password = value ?? '';
    if (password.isEmpty) return 'Şifre gerekli.';
    if (password.length < minPasswordLength) {
      return 'Şifre en az $minPasswordLength karakter olmalı.';
    }
    if (password.length > maxPasswordLength) {
      return 'Şifre en fazla $maxPasswordLength karakter olabilir.';
    }
    if (!hasLetter(password) || !hasDigit(password)) {
      return 'Şifre en az bir harf ve bir rakam içermeli.';
    }
    return null;
  }

  static String? confirmPassword(String? value, String original) {
    if ((value ?? '').isEmpty) return 'Şifreni tekrar gir.';
    if (value != original) return 'Şifreler eşleşmiyor.';
    return null;
  }

  static bool hasLetter(String value) => _letterPattern.hasMatch(value);

  static bool hasDigit(String value) => _digitPattern.hasMatch(value);
}
