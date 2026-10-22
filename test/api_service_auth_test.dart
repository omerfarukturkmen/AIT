import 'dart:typed_data';

import 'package:flutter_application_1/core/state/auth_store.dart';
import 'package:flutter_application_1/data/api_service.dart';
import 'package:flutter_application_1/models/auth_session_model.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  tearDown(() => AuthStore.session.value = null);

  test('upload refuses to run without a session', () async {
    AuthStore.session.value = null;

    expect(
      () => ApiService.uploadVideoBytesRaw(
        videoBytes: Uint8List(1),
        fileName: 'v.mp4',
        exerciseName: 'squat',
      ),
      throwsA(isA<Exception>()),
    );
  });

  test('upload sends the bearer token and no user_id', () async {
    AuthStore.session.value = const AuthSession(
      accessToken: 'token-123',
      user: AuthUser(id: 7, email: 'a@b.co', fullName: 'Ayşe Yılmaz'),
    );
    late http.BaseRequest sent;
    late String body;

    await http.runWithClient(
      () async {
        await expectLater(
          ApiService.uploadVideoBytesRaw(
            videoBytes: Uint8List(1),
            fileName: 'v.mp4',
            exerciseName: 'squat',
          ),
          throwsA(predicate((e) => e.toString().contains('Oturum geçersiz'))),
        );
      },
      () => MockClient((request) async {
        sent = request;
        body = request.body;
        return http.Response(
          '{"detail":"Oturum geçersiz."}',
          401,
          headers: {'content-type': 'application/json; charset=utf-8'},
        );
      }),
    );

    expect(sent.headers['Authorization'], 'Bearer token-123');
    expect(body, isNot(contains('user_id')));
  });
}
