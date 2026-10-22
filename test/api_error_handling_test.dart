import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_application_1/core/services/auth_service.dart';
import 'package:flutter_application_1/core/state/auth_store.dart';
import 'package:flutter_application_1/data/api_service.dart';
import 'package:flutter_application_1/features/auth/widgets/auth_text_field.dart';
import 'package:flutter_application_1/models/auth_session_model.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';

const _session = AuthSession(
  accessToken: 'token-123',
  user: AuthUser(id: 1, email: 'a@b.co', fullName: 'Ayşe Yılmaz'),
);

Future<ApiException> _uploadError(http.Response response) async {
  AuthStore.session.value = _session;
  try {
    await http.runWithClient(
      () => ApiService.uploadVideoBytesRaw(
        videoBytes: Uint8List(1),
        fileName: 'v.mp4',
        exerciseName: 'squat',
      ),
      () => MockClient((_) async => response),
    );
  } on ApiException catch (error) {
    return error;
  }
  fail('expected ApiException');
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
    FlutterSecureStorage.setMockInitialValues({});
  });
  tearDown(() => AuthStore.session.value = null);

  group('upload errors never expose server internals', () {
    test('500 with internal details shows a generic message', () async {
      final error = await _uploadError(
        http.Response(
          jsonEncode({'detail': r'Traceback: C:\srv\ait\main.py line 3'}),
          500,
        ),
      );
      expect(error.message, isNot(contains('srv')));
      expect(error.message, contains('Sunucuda bir hata'));
    });

    test('non-JSON body is not shown', () async {
      final error = await _uploadError(
        http.Response('<html>nginx debug page</html>', 502),
      );
      expect(error.message, isNot(contains('nginx')));
    });

    test('safe backend message is shown for client errors', () async {
      final error = await _uploadError(
        http.Response(
          jsonEncode({'detail': 'Dosya geçerli bir video değil.'}),
          415,
          headers: {'content-type': 'application/json; charset=utf-8'},
        ),
      );
      expect(error.message, 'Dosya geçerli bir video değil.');
      expect(error.statusCode, 415);
    });

    test('rate limit gets a friendly message', () async {
      final error = await _uploadError(http.Response('', 429));
      expect(error.message, contains('Çok fazla istek'));
    });
  });

  test('sign out revokes the token on the server', () async {
    final requests = <http.BaseRequest>[];
    await AuthStore.save(_session, remember: true);

    await http.runWithClient(
      AuthStore.signOut,
      () => MockClient((request) async {
        requests.add(request);
        return http.Response('', 204);
      }),
    );

    expect(requests.single.url.path, '/auth/logout');
    expect(requests.single.headers['Authorization'], 'Bearer token-123');
    expect(AuthStore.isSignedIn, isFalse);
  });

  test('sign out still works offline', () async {
    await AuthStore.save(_session, remember: true);

    await http.runWithClient(
      AuthStore.signOut,
      () => MockClient((_) async => throw http.ClientException('offline')),
    );

    expect(AuthStore.isSignedIn, isFalse);
  });

  test('login sends remember_me', () async {
    late Map<String, dynamic> body;

    await http.runWithClient(
      () => AuthService.login(
        email: 'a@b.co',
        password: 'guclu1234',
        rememberMe: false,
      ),
      () => MockClient((request) async {
        body = jsonDecode(request.body) as Map<String, dynamic>;
        return http.Response(
          jsonEncode({
            'access_token': 't',
            'user': {'id': 1, 'email': 'a@b.co', 'full_name': 'A B'},
          }),
          200,
        );
      }),
    );

    expect(body['remember_me'], isFalse);
  });

  testWidgets('text fields enforce their maximum length', (tester) async {
    final controller = TextEditingController();
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: AuthTextField(
            controller: controller,
            label: 'E-posta',
            icon: Icons.mail,
            maxLength: 10,
          ),
        ),
      ),
    );

    await tester.enterText(find.byType(TextFormField), 'x' * 50);

    expect(controller.text.length, 10);
  });
}
