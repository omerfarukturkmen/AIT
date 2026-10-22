import 'package:flutter/services.dart';
import 'package:flutter_application_1/core/state/auth_store.dart';
import 'package:flutter_application_1/models/auth_session_model.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

// Kept in its own file: other tests replace secure storage with an in-memory
// mock, while this one needs the real channel so it can make it fail.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          const MethodChannel('plugins.it_nomads.com/flutter_secure_storage'),
          (call) async => throw PlatformException(code: 'KeystoreError'),
        );
  });

  test('unreadable secure storage does not block app start', () async {
    await expectLater(AuthStore.restore(), completes);
    expect(AuthStore.isSignedIn, isFalse);
  });

  test('sign-in still works when the session cannot be persisted', () async {
    const session = AuthSession(
      accessToken: 't',
      user: AuthUser(id: 1, email: 'a@b.co', fullName: 'A B'),
    );

    await expectLater(AuthStore.save(session, remember: true), completes);
    expect(AuthStore.isSignedIn, isTrue);
    await expectLater(AuthStore.signOut(), completes);
  });
}
