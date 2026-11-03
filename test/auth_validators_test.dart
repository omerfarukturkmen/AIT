import 'package:flutter_application_1/features/auth/auth_validators.dart';
import 'package:flutter_test/flutter_test.dart';

import 'helpers.dart';

void main() {
  final tr = AuthValidators(trL10n);
  final en = AuthValidators(enL10n);

  group('AuthValidators', () {
    test('email', () {
      expect(tr.email(''), 'E-posta adresi gerekli.');
      expect(tr.email('ayse@'), isNotNull);
      expect(tr.email('ayse example.com'), isNotNull);
      expect(tr.email(' ayse@example.com '), isNull);
      expect(en.email(''), 'E-mail address is required.');
    });

    test('full name requires first and last name', () {
      expect(tr.fullName(''), 'Ad soyad gerekli.');
      expect(tr.fullName('Ayşe'), isNotNull);
      expect(tr.fullName('Ayşe Yılmaz'), isNull);
    });

    test('new password rules', () {
      expect(tr.newPassword(''), 'Şifre gerekli.');
      expect(tr.newPassword('abc123'), contains('8 karakter'));
      expect(tr.newPassword('sadeceharf'), contains('rakam'));
      expect(tr.newPassword('12345678'), contains('harf'));
      expect(tr.newPassword('güçlü1234'), isNull);
      expect(en.newPassword('abc123'), contains('at least 8'));
    });

    test('confirm password must match', () {
      expect(tr.confirmPassword('', 'abc12345'), isNotNull);
      expect(
        tr.confirmPassword('abc12346', 'abc12345'),
        'Şifreler eşleşmiyor.',
      );
      expect(tr.confirmPassword('abc12345', 'abc12345'), isNull);
    });

    test('verification code is six digits', () {
      expect(tr.code('12345'), isNotNull);
      expect(tr.code('12a456'), isNotNull);
      expect(tr.code(' 123456 '), isNull);
    });
  });
}
