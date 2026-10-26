import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter_application_1/core/app_exception.dart';
import 'package:flutter_application_1/core/state/auth_store.dart';
import 'package:flutter_application_1/data/api_service.dart';
import 'package:flutter_application_1/data/exercise_catalog.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'helpers.dart';

http.Response _json(Object body, int status) => http.Response(
  jsonEncode(body),
  status,
  headers: {'content-type': 'application/json; charset=utf-8'},
);

Future<AppException> _uploadError(http.Response response) async {
  try {
    await http.runWithClient(
      () => ApiService.uploadVideo(
        videoBytes: Uint8List(1),
        fileName: 'v.mp4',
        exercise: ExerciseId.squat,
      ),
      () => MockClient((_) async => response),
    );
  } on AppException catch (error) {
    return error;
  }
  fail('expected AppException');
}

void main() {
  setUp(() {
    signInForTest();
    ApiService.pollInterval = Duration.zero;
  });
  tearDown(() => AuthStore.session.value = null);

  group('upload', () {
    test('requires a session', () async {
      AuthStore.session.value = null;
      expect(
        () => ApiService.uploadVideo(
          videoBytes: Uint8List(1),
          fileName: 'v.mp4',
          exercise: ExerciseId.squat,
        ),
        throwsA(
          isA<AppException>().having(
            (e) => e.kind,
            'kind',
            ErrorKind.unauthorized,
          ),
        ),
      );
    });

    test('sends the bearer token and exercise, never a user id', () async {
      late http.BaseRequest sent;
      late String body;

      final id = await http.runWithClient(
        () => ApiService.uploadVideo(
          videoBytes: Uint8List(4),
          fileName: 'v.mp4',
          exercise: ExerciseId.pushUp,
        ),
        () => MockClient((request) async {
          sent = request;
          body = request.body;
          return _json({
            'status': 'pending',
            'data': {'analysis_id': 42},
          }, 202);
        }),
      );

      expect(id, 42);
      expect(sent.headers['Authorization'], 'Bearer test-token');
      expect(body, contains('push-up'));
      expect(body, isNot(contains('user_id')));
    });

    test('exercises the AI cannot analyze are rejected locally', () {
      expect(
        () => ApiService.uploadVideo(
          videoBytes: Uint8List(1),
          fileName: 'v.mp4',
          exercise: ExerciseId.plank,
        ),
        throwsA(isA<AppException>()),
      );
    });
  });

  group('error messages never expose server internals', () {
    test('5xx details are hidden in every language', () async {
      final error = await _uploadError(
        _json({'detail': r'Traceback C:\srv\ait\main.py'}, 500),
      );
      expect(error.kind, ErrorKind.server);
      expect(error.message(trL10n), isNot(contains('srv')));
      expect(error.message(enL10n), isNot(contains('srv')));
    });

    test(
      'safe Turkish detail is shown in Turkish, translated in English',
      () async {
        final error = await _uploadError(
          _json({'detail': 'Dosya geçerli bir video değil.'}, 415),
        );
        expect(error.kind, ErrorKind.unsupportedMedia);
        expect(error.message(trL10n), 'Dosya geçerli bir video değil.');
        expect(error.message(enL10n), enL10n.errorUnsupportedMedia);
      },
    );

    test('non-JSON bodies are not shown', () async {
      final error = await _uploadError(
        http.Response('<html>nginx</html>', 502),
      );
      expect(error.message(trL10n), isNot(contains('nginx')));
    });

    test('rate limiting is explained', () async {
      final error = await _uploadError(http.Response('', 429));
      expect(error.kind, ErrorKind.rateLimited);
    });
  });

  group('waitForResult', () {
    test('polls until the analysis completes and reports stages', () async {
      final replies = [
        _json({
          'status': 'pending',
          'data': {'analysis_status': 'pending'},
        }, 200),
        _json({
          'status': 'processing',
          'data': {'analysis_status': 'processing'},
        }, 200),
        _json(resultPayload(analysisId: 9, score: 90, reps: 2), 200),
      ];
      final stages = <AnalysisStage>[];

      final result = await http.runWithClient(
        () => ApiService.waitForResult(9, onStage: stages.add),
        () => MockClient((request) async {
          expect(request.url.path, '/analysis/9');
          return replies.removeAt(0);
        }),
      );

      expect(result.score, 90);
      expect(result.repetitionCount, 2);
      expect(stages, [
        AnalysisStage.queued,
        AnalysisStage.processing,
        AnalysisStage.completed,
      ]);
    });

    test('a failed analysis surfaces the safe server message', () async {
      final future = http.runWithClient(
        () => ApiService.waitForResult(3),
        () => MockClient(
          (_) async => _json({
            'status': 'failed',
            'data': {'feedback': 'Video okunamadı.'},
          }, 200),
        ),
      );
      await expectLater(
        future,
        throwsA(
          isA<AppException>()
              .having((e) => e.kind, 'kind', ErrorKind.analysisFailed)
              .having((e) => e.message(trL10n), 'tr', 'Video okunamadı.'),
        ),
      );
    });

    test('rides out short connection drops', () async {
      var calls = 0;
      final result = await http.runWithClient(
        () => ApiService.waitForResult(4),
        () => MockClient((_) async {
          calls++;
          if (calls <= 2) throw http.ClientException('offline');
          return _json(resultPayload(analysisId: 4), 200);
        }),
      );
      expect(result.id, 4);
      expect(calls, 3);
    });
  });

  test('history keeps only completed analyses, newest first', () async {
    final history = await http.runWithClient(
      () => ApiService.fetchHistory(),
      () => MockClient(
        (_) async => _json({
          'analyses': [
            {'analysis_id': 2, 'analysis_status': 'processing', 'result': null},
            {'analysis_id': 1, 'result': resultPayload(analysisId: 1)},
          ],
        }, 200),
      ),
    );
    expect(history.map((r) => r.id), [1]);
  });
}
