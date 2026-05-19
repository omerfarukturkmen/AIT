import 'dart:io';
import 'dart:math';

import '../../models/analysis_result_model.dart';

class AnalysisService {
  Future<AnalysisResult> analyzeVideo({
    required File videoFile,
    required String exerciseName,
  }) async {
    await Future.delayed(const Duration(seconds: 3));

    final random = Random();

    final score = 72 + random.nextInt(20);
    final repetitionCount = 8 + random.nextInt(8);
    final confidence = 86 + random.nextDouble() * 10;

    return AnalysisResult(
      exerciseName: exerciseName,
      score: score,
      movementAngle: '${72 + random.nextInt(18)}°',
      repetitionCount: repetitionCount,
      confidence: double.parse(confidence.toStringAsFixed(1)),
      duration: '00:${25 + random.nextInt(25)}',
      mistakes: _getMistakesByExercise(exerciseName),
      recommendations: _getRecommendationsByExercise(exerciseName),
    );
  }

  List<String> _getMistakesByExercise(String exerciseName) {
    switch (exerciseName) {
      case 'Squat':
        return const [
          'Diz hizası ayak parmaklarıyla tam korunmuyor.',
          'Gövde bazı tekrarlarda öne fazla eğiliyor.',
          'İniş fazında kalça derinliği yetersiz kalıyor.',
        ];

      case 'Push-up':
        return const [
          'Kalça seviyesi bazı tekrarlarda aşağı düşüyor.',
          'Dirsek açısı fazla dışa açılıyor.',
          'Gövde stabilitesi hareket boyunca korunmuyor.',
        ];

      case 'Plank':
        return const [
          'Bel bölgesinde hafif çökme gözlemleniyor.',
          'Core aktivasyonu yeterince stabil değil.',
          'Omuz ve dirsek hizası zaman zaman bozuluyor.',
        ];

      case 'Lunge':
        return const [
          'Öndeki diz ayak hizasının dışına çıkıyor.',
          'Denge kontrolü bazı tekrarlarda zayıf.',
          'Gövde dik pozisyonunu tam koruyamıyor.',
        ];

      default:
        return const [
          'Hareket sırasında eklem hizası tam korunmuyor.',
          'Gövde kontrolü bazı anlarda zayıflıyor.',
          'Hareket temposu fazla hızlı ilerliyor.',
        ];
    }
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
