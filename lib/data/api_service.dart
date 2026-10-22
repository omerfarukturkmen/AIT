import 'dart:convert';
import 'dart:typed_data';

import 'package:http/http.dart' as http;

import '../core/api_config.dart';
import '../core/state/auth_store.dart';
import '../models/analysis_result_model.dart';
import '../models/backend_analysis_response.dart';
import 'analysis_result_mapper.dart';

class ApiService {
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
      throw Exception('Analiz için giriş yapmalısın.');
    }
    return {'Authorization': 'Bearer $token'};
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

    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);

    if (response.statusCode == 401) {
      throw Exception('Oturumun sona erdi. Lütfen tekrar giriş yap.');
    }
    if (response.statusCode != 200) {
      throw Exception(
        "Backend hata kodu: ${response.statusCode}\n${response.body}",
      );
    }

    final Map<String, dynamic> data = jsonDecode(response.body);
    return BackendAnalysisResponse.fromJson(data);
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
