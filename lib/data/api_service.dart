import 'dart:convert';
import 'dart:typed_data';

import 'package:http/http.dart' as http;

import '../core/api_config.dart';
import '../models/analysis_result.dart';

class ApiService {
  static Future<AnalysisResult> uploadVideoBytes({
    required Uint8List videoBytes,
    required String fileName,
    int userId = 1,
  }) async {
    final url = Uri.parse("${ApiConfig.baseUrl}/upload-video");

    final request = http.MultipartRequest("POST", url);

    request.fields["user_id"] = userId.toString();

    request.files.add(
      http.MultipartFile.fromBytes("file", videoBytes, filename: fileName),
    );

    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);

    if (response.statusCode == 200) {
      final Map<String, dynamic> data = jsonDecode(response.body);
      final Map<String, dynamic> analysis = data["analysis"];

      return AnalysisResult.fromJson(analysis);
    } else {
      throw Exception(
        "Backend hata kodu: ${response.statusCode}\n${response.body}",
      );
    }
  }
}
