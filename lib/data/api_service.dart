import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:http/http.dart' as http;

import '../core/api_config.dart';
import '../core/app_exception.dart';
import '../core/state/auth_store.dart';
import '../models/analysis_result_model.dart';
import 'exercise_catalog.dart';

enum AnalysisStage { uploading, queued, processing, completed, failed }

/// Talks to the analysis endpoints. Video analysis runs in the background:
/// upload returns an id, then [waitForResult] polls until it is done.
class ApiService {
  static const Duration _uploadTimeout = Duration(minutes: 5);
  static const Duration _requestTimeout = Duration(seconds: 20);
  static Duration pollInterval = const Duration(seconds: 2);
  static const Duration maxWait = Duration(minutes: 10);

  /// Bearer header for the signed-in user; the backend derives the owner of
  /// every upload from this token.
  static Map<String, String> authHeaders() {
    final token = AuthStore.session.value?.accessToken;
    if (token == null) {
      throw const AppException(ErrorKind.unauthorized);
    }
    return {'Authorization': 'Bearer $token'};
  }

  static String? _detail(http.Response response) {
    try {
      final body = jsonDecode(utf8.decode(response.bodyBytes));
      final detail = body is Map ? body['detail'] : null;
      return detail is String ? detail : null;
    } on FormatException {
      return null;
    }
  }

  static Map<String, dynamic> _json(http.Response response) {
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw AppException.fromStatus(response.statusCode, _detail(response));
    }
    try {
      return jsonDecode(utf8.decode(response.bodyBytes))
          as Map<String, dynamic>;
    } on FormatException {
      throw const AppException(ErrorKind.server);
    }
  }

  static Future<http.Response> _send(
    Future<http.Response> request,
    Duration timeout,
  ) async {
    try {
      return await request.timeout(timeout);
    } on TimeoutException {
      throw const AppException(ErrorKind.timeout);
    } on AppException {
      rethrow;
    } on Exception {
      throw const AppException(ErrorKind.network);
    }
  }

  /// Uploads a video and returns the id of the queued analysis.
  static Future<int> uploadVideo({
    required Uint8List videoBytes,
    required String fileName,
    required ExerciseId exercise,
  }) async {
    final apiKey = exercise.apiKey;
    if (apiKey == null) throw const AppException(ErrorKind.invalidInput);

    final request =
        http.MultipartRequest(
            'POST',
            Uri.parse('${ApiConfig.baseUrl}/upload-video'),
          )
          ..headers.addAll(authHeaders())
          ..fields['exercise_type'] = apiKey
          ..files.add(
            http.MultipartFile.fromBytes(
              'file',
              videoBytes,
              filename: fileName,
            ),
          );

    final response = await _send(
      request.send().then(http.Response.fromStream),
      _uploadTimeout,
    );
    final data = _json(response)['data'] as Map<String, dynamic>;
    return data['analysis_id'] as int;
  }

  /// Polls the analysis until it completes or fails. [onStage] reports
  /// queued/processing so the UI can show real progress.
  static Future<AnalysisResult> waitForResult(
    int analysisId, {
    void Function(AnalysisStage stage)? onStage,
  }) async {
    final deadline = DateTime.now().add(maxWait);
    var networkFailures = 0;

    while (true) {
      try {
        final response = await _send(
          http.get(
            Uri.parse('${ApiConfig.baseUrl}/analysis/$analysisId'),
            headers: authHeaders(),
          ),
          _requestTimeout,
        );
        final body = _json(response);
        networkFailures = 0;

        final status = body['status'];
        if (status == 'success') {
          onStage?.call(AnalysisStage.completed);
          return AnalysisResult.fromPayload(body);
        }
        if (status == 'failed') {
          onStage?.call(AnalysisStage.failed);
          final data = body['data'];
          final feedback = data is Map ? data['feedback'] as String? : null;
          final code = data is Map ? data['error_code'] as String? : null;
          throw AppException(ErrorKind.analysisFailed, feedback, code);
        }
        onStage?.call(
          status == 'processing'
              ? AnalysisStage.processing
              : AnalysisStage.queued,
        );
      } on AppException catch (error) {
        // Ride out short connection drops while the server keeps working.
        final transient =
            error.kind == ErrorKind.network || error.kind == ErrorKind.timeout;
        if (!transient || ++networkFailures > 5) rethrow;
      }

      if (DateTime.now().isAfter(deadline)) {
        throw const AppException(ErrorKind.timeout);
      }
      await Future<void>.delayed(pollInterval);
    }
  }

  /// The signed-in user's completed analyses, newest first.
  static Future<List<AnalysisResult>> fetchHistory({int limit = 100}) async {
    final response = await _send(
      http.get(
        Uri.parse('${ApiConfig.baseUrl}/analyses?limit=$limit'),
        headers: authHeaders(),
      ),
      _requestTimeout,
    );
    final items = (_json(response)['analyses'] as List)
        .cast<Map<String, dynamic>>();
    return [
      for (final item in items)
        if (item['result'] is Map<String, dynamic>)
          AnalysisResult.fromPayload(item['result'] as Map<String, dynamic>),
    ];
  }
}
