import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

import '../../data/analysis_result_mapper.dart';
import '../../data/api_service.dart';
import '../../models/analysis_result_model.dart';
import '../../models/backend_analysis_response.dart';
import '../api_config.dart';

class AnalysisService {
  static const String baseUrl = ApiConfig.baseUrl;

  Future<AnalysisResult> analyzeVideo({
    required File videoFile,
    required String exerciseName,
  }) async {
    final uri = Uri.parse('$baseUrl/upload-video');
    final request = http.MultipartRequest('POST', uri);
    request.headers.addAll(ApiService.authHeaders());

    request.files.add(
      await http.MultipartFile.fromPath('file', videoFile.path),
    );
    request.fields['exercise_type'] = ApiService.normalizeExerciseType(
      exerciseName,
    );

    try {
      final streamedResponse = await request.send();
      final responseBody = await streamedResponse.stream.bytesToString();

      if (streamedResponse.statusCode != 200) {
        throw Exception(
          'Backend hata döndürdü. Status: ${streamedResponse.statusCode}, Body: $responseBody',
        );
      }

      final Map<String, dynamic> data = jsonDecode(responseBody);
      final backend = BackendAnalysisResponse.fromJson(data);
      return AnalysisResultMapper.fromBackend(backend);
    } on SocketException {
      throw Exception(
        'Backend bağlantısı kurulamadı. Backend çalışıyor mu kontrol et: $baseUrl',
      );
    } on FormatException {
      throw Exception('Backend cevabı JSON formatında değil.');
    } catch (e) {
      throw Exception('Analiz sırasında hata oluştu: $e');
    }
  }
}
