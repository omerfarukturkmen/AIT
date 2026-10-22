import 'package:flutter_application_1/core/state/analysis_history_store.dart';
import 'package:flutter_application_1/core/state/auth_store.dart';
import 'package:flutter_application_1/models/analysis_result_model.dart';
import 'package:flutter_application_1/models/auth_session_model.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

const _session = AuthSession(
  accessToken: 'secret-token',
  user: AuthUser(id: 1, email: 'a@b.co', fullName: 'Ayşe Yılmaz'),
);

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
    FlutterSecureStorage.setMockInitialValues({});
    AuthStore.session.value = null;
  });

  test(
    'remembered token goes to secure storage, not shared_preferences',
    () async {
      await AuthStore.save(_session, remember: true);

      expect(
        await const FlutterSecureStorage().read(key: 'auth_access_token'),
        'secret-token',
      );
      final prefs = await SharedPreferences.getInstance();
      expect(prefs.getKeys(), isEmpty);
    },
  );

  test('not remembered: nothing is persisted', () async {
    await AuthStore.save(_session, remember: false);

    expect(await const FlutterSecureStorage().readAll(), isEmpty);
    expect(AuthStore.isSignedIn, isTrue);
  });

  test('restore removes a legacy plaintext token', () async {
    SharedPreferences.setMockInitialValues({
      'auth_access_token': 'old-plaintext',
      'auth_user': '{"id":1,"email":"a@b.co","full_name":"A B"}',
    });

    await AuthStore.restore();

    final prefs = await SharedPreferences.getInstance();
    expect(prefs.getString('auth_access_token'), isNull);
    expect(AuthStore.isSignedIn, isFalse);
  });

  test('sign out clears storage and the previous user\'s results', () async {
    await AuthStore.save(_session, remember: true);
    AnalysisHistoryStore.addResult(
      AnalysisResult.fromJson({'exerciseName': 'Squat', 'score': 80}),
    );
    expect(AnalysisHistoryStore.results.value, hasLength(1));

    await AuthStore.signOut();

    expect(await const FlutterSecureStorage().readAll(), isEmpty);
    expect(AuthStore.session.value, isNull);
    expect(AnalysisHistoryStore.results.value, isEmpty);
  });
}
