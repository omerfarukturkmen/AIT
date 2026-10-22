import 'package:flutter_application_1/features/auth/auth_validators.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('AuthValidators', () {
    test('email', () {
      expect(AuthValidators.email(''), 'E-posta adresi gerekli.');
      expect(AuthValidators.email('ayse@'), isNotNull);
      expect(AuthValidators.email('ayse example.com'), isNotNull);
      expect(AuthValidators.email(' ayse@example.com '), isNull);
    });

    test('full name requires first and last name', () {
      expect(AuthValidators.fullName(''), 'Ad soyad gerekli.');
      expect(AuthValidators.fullName('Ayşe'), isNotNull);
      expect(AuthValidators.fullName('Ayşe Yılmaz'), isNull);
    });

    test('new password rules', () {
      expect(AuthValidators.newPassword(''), 'Şifre gerekli.');
      expect(AuthValidators.newPassword('abc123'), contains('8 karakter'));
      expect(AuthValidators.newPassword('sadeceharf'), contains('rakam'));
      expect(AuthValidators.newPassword('12345678'), contains('harf'));
      expect(AuthValidators.newPassword('güçlü1234'), isNull);
    });

    test('confirm password must match', () {
      expect(AuthValidators.confirmPassword('', 'abc12345'), isNotNull);
      expect(
        AuthValidators.confirmPassword('abc12346', 'abc12345'),
        'Şifreler eşleşmiyor.',
      );
      expect(AuthValidators.confirmPassword('abc12345', 'abc12345'), isNull);
    });
  });
}
