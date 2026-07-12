import 'dart:convert';
import 'dart:typed_data';

import 'package:http/http.dart' as http;

import '../core/api_config.dart';
import '../models/analysis_result.dart';

class ApiService {
  static Future<AnalysisResult> uploadVideoBytes({
    required Uint8List videoBytes,
    required String fileName,
    required String exerciseName,
    int userId = 1,
  }) async {
    final url = Uri.parse("${ApiConfig.baseUrl}/upload-video");

    final request = http.MultipartRequest("POST", url);

    request.fields["user_id"] = userId.toString();

    // Seçilen hareket bilgisini backend'e gönderiyoruz.
    // Örnek: Squat -> squat
    request.fields["exercise_type"] = exerciseName.toLowerCase();

    request.files.add(
      http.MultipartFile.fromBytes("file", videoBytes, filename: fileName),
    );

    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);

    if (response.statusCode == 200) {
      final Map<String, dynamic> data = jsonDecode(response.body);

      final Map<String, dynamic> analysis =
          data["analysis"] is Map<String, dynamic>
          ? data["analysis"] as Map<String, dynamic>
          : data;

      return AnalysisResult.fromJson(analysis);
    } else {
      throw Exception(
        "Backend hata kodu: ${response.statusCode}\n${response.body}",
      );
    }
  }
}
