import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

import '../../models/analysis_result_model.dart';

class AnalysisService {
  static const String baseUrl = 'http://127.0.0.1:8000';

  Future<AnalysisResult> analyzeVideo({
    required File videoFile,
    required String exerciseName,
  }) async {
    final uri = Uri.parse('$baseUrl/upload-video');

    final request = http.MultipartRequest('POST', uri);

    request.files.add(
      await http.MultipartFile.fromPath('video', videoFile.path),
    );

    request.fields['exercise_type'] = exerciseName.toLowerCase();

    try {
      final streamedResponse = await request.send();
      final responseBody = await streamedResponse.stream.bytesToString();

      if (streamedResponse.statusCode != 200) {
        throw Exception(
          'Backend hata döndürdü. Status: ${streamedResponse.statusCode}, Body: $responseBody',
        );
      }

      final Map<String, dynamic> data = jsonDecode(responseBody);

      final Map<String, dynamic> analysis =
          data['analysis'] is Map<String, dynamic>
          ? data['analysis'] as Map<String, dynamic>
          : data;

      final accuracy = analysis['accuracy'];
      final feedback = analysis['feedback'];
      final averageMotion = analysis['average_motion'];
      final totalFrames = analysis['total_frames'];

      return AnalysisResult(
        exerciseName: exerciseName,
        score: _parseInt(accuracy),
        movementAngle: averageMotion != null ? averageMotion.toString() : '-',
        repetitionCount: _parseInt(totalFrames),
        confidence: _parseDouble(accuracy),
        duration: '-',
        mistakes: _parseStringList(feedback),
        recommendations: _getRecommendationsByExercise(exerciseName),
      );
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

  int _parseInt(dynamic value) {
    if (value == null) return 0;

    if (value is int) return value;

    if (value is double) return value.round();

    return int.tryParse(value.toString()) ?? 0;
  }

  double _parseDouble(dynamic value) {
    if (value == null) return 0.0;

    if (value is double) return value;

    if (value is int) return value.toDouble();

    return double.tryParse(value.toString()) ?? 0.0;
  }

  List<String> _parseStringList(dynamic value) {
    if (value == null) return const [];

    if (value is List) {
      return value.map((item) => item.toString()).toList();
    }

    if (value is String) {
      if (value.trim().isEmpty) return const [];
      return [value];
    }

    return [value.toString()];
  }

  List<String> _getRecommendationsByExercise(String exerciseName) {
    switch (exerciseName) {
      case 'Squat':
        return const [
          'Dizlerini ayak parmaklarınla aynı hizada tut.',
          'Göğsünü açık tutarak gövdeni daha stabil koru.',
          'İniş aşamasını daha kontrollü ve yavaş yap.',
        ];

      case 'Push-up':
        return const [
          'Core bölgesini sıkı tutarak kalçanın düşmesini engelle.',
          'Dirseklerini gövdeye daha yakın konumlandır.',
          'Her tekrar sırasında omuz, kalça ve ayak hizasını koru.',
        ];

      case 'Plank':
        return const [
          'Karın kaslarını aktif tutarak bel çökmesini engelle.',
          'Dirseklerini omuzların tam altında konumlandır.',
          'Boyun pozisyonunu nötr hatta koru.',
        ];

      case 'Lunge':
        return const [
          'Öndeki dizini ayak bileği hizasında tut.',
          'Adım mesafeni biraz artırarak dengeyi iyileştir.',
          'Gövdeni dik tutup hareketi kontrollü yap.',
        ];

      default:
        return const [
          'Hareketi daha kontrollü ve dengeli yap.',
          'Eklem hizalarını korumaya dikkat et.',
          'Tekrar sırasında gövde stabilitesini artır.',
        ];
    }
  }
}
