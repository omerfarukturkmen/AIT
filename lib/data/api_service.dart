import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:http/http.dart' as http;

import '../core/api_config.dart';
import '../core/state/auth_store.dart';
import '../models/analysis_result_model.dart';
import '../models/backend_analysis_response.dart';
import 'analysis_result_mapper.dart';

/// Error with a message that is safe to show to the user. Raw backend
/// bodies are never shown, since they may contain internal details.
class ApiException implements Exception {
  final String message;
  final int? statusCode;

  const ApiException(this.message, {this.statusCode});

  @override
  String toString() => message;
}

class ApiService {
  static const Duration _uploadTimeout = Duration(minutes: 5);

  static String normalizeExerciseType(String exerciseName) {
    final normalized = exerciseName.trim().toLowerCase().replaceAll('_', '-');
    if (normalized == 'pushup' || normalized == 'push up') {
      return 'push-up';
    }
    return normalized;
  }

  /// Bearer header for the signed-in user; the backend derives the owner of
  /// every upload from this token.
  static Map<String, String> authHeaders() {
    final token = AuthStore.session.value?.accessToken;
    if (token == null) {
      throw const ApiException('Analiz için giriş yapmalısın.');
    }
    return {'Authorization': 'Bearer $token'};
  }

  /// User-facing text for a failed response: the backend's `detail` when it
  /// is a plain message, otherwise a generic text for the status code.
  static String errorMessage(http.Response response) {
    try {
      final body = jsonDecode(utf8.decode(response.bodyBytes));
      final detail = body is Map ? body['detail'] : null;
      if (detail is String && detail.isNotEmpty && response.statusCode < 500) {
        return detail;
      }
    } on FormatException {
      // Not JSON; fall back to the status-based message.
    }
    return switch (response.statusCode) {
      401 => 'Oturumun sona erdi. Lütfen tekrar giriş yap.',
      413 => 'Video dosyası çok büyük.',
      415 => 'Dosya geçerli bir video değil.',
      429 => 'Çok fazla istek gönderildi. Lütfen biraz sonra tekrar dene.',
      >= 500 => 'Sunucuda bir hata oluştu. Lütfen tekrar dene.',
      _ => 'İşlem tamamlanamadı. Lütfen tekrar dene.',
    };
  }

  static Future<BackendAnalysisResponse> uploadVideoBytesRaw({
    required Uint8List videoBytes,
    required String fileName,
    required String exerciseName,
  }) async {
    final url = Uri.parse("${ApiConfig.baseUrl}/upload-video");
    final request = http.MultipartRequest("POST", url);
    request.headers.addAll(authHeaders());
    request.fields["exercise_type"] = normalizeExerciseType(exerciseName);
    request.files.add(
      http.MultipartFile.fromBytes("file", videoBytes, filename: fileName),
    );

    final http.Response response;
    try {
      final streamedResponse = await request.send().timeout(_uploadTimeout);
      response = await http.Response.fromStream(streamedResponse);
    } on TimeoutException {
      throw const ApiException(
        'Sunucu zamanında yanıt vermedi. Lütfen tekrar dene.',
      );
    } on Exception {
      throw const ApiException(
        'Sunucuya ulaşılamadı. İnternet bağlantını kontrol et.',
      );
    }

    if (response.statusCode != 200) {
      throw ApiException(
        errorMessage(response),
        statusCode: response.statusCode,
      );
    }

    try {
      final Map<String, dynamic> data = jsonDecode(
        utf8.decode(response.bodyBytes),
      );
      return BackendAnalysisResponse.fromJson(data);
    } on FormatException {
      throw const ApiException('Sunucudan beklenmeyen bir yanıt alındı.');
    }
  }

  /// Uploads video and returns the UI [AnalysisResult] via a single mapper.
  static Future<AnalysisResult> uploadVideoBytes({
    required Uint8List videoBytes,
    required String fileName,
    required String exerciseName,
  }) async {
    final backend = await uploadVideoBytesRaw(
      videoBytes: videoBytes,
      fileName: fileName,
      exerciseName: exerciseName,
    );
    return AnalysisResultMapper.fromBackend(backend);
  }
}
