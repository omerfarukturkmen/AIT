import 'package:flutter/material.dart';

import '../models/achievement_model.dart';
import '../models/analysis_result_model.dart';
import '../models/exercise_model.dart';

final List<Exercise> exercises = [
  const Exercise(name: 'Squat', icon: Icons.fitness_center_rounded),
  const Exercise(name: 'Push-up', icon: Icons.accessibility_new_rounded),
  const Exercise(name: 'Plank', icon: Icons.self_improvement_rounded),
  const Exercise(name: 'Lunge', icon: Icons.directions_run_rounded),
  const Exercise(name: 'Deadlift', icon: Icons.sports_gymnastics_rounded),
  const Exercise(
    name: 'Shoulder Press',
    icon: Icons.sports_martial_arts_rounded,
  ),
];

final List<AnalysisResult> fakeHistory = [
  const AnalysisResult(
    exerciseName: 'Squat',
    score: 82,
    movementAngle: '86°',
    repetitionCount: 12,
    confidence: 91.4,
    duration: '00:38',
    mistakes: ['Diz hizası bozuluyor.', 'Gövde kontrolü zayıf.'],
    recommendations: ['Hareketi yavaşlat.', 'Diz ve ayak hizasını koru.'],
  ),
  const AnalysisResult(
    exerciseName: 'Push-up',
    score: 76,
    movementAngle: '72°',
    repetitionCount: 10,
    confidence: 88.2,
    duration: '00:31',
    mistakes: ['Kalça seviyesi düşüyor.', 'Dirsek açısı fazla açılıyor.'],
    recommendations: [
      'Core bölgesini sıkı tut.',
      'Dirsekleri gövdeye yakın tut.',
    ],
  ),
];

const List<Achievement> achievements = [
  Achievement(
    title: 'İlk Analiz',
    icon: Icons.verified_rounded,
    isUnlocked: true,
  ),
  Achievement(
    title: '10 Antrenman',
    icon: Icons.local_fire_department_rounded,
    isUnlocked: true,
  ),
  Achievement(
    title: '90+ Skor',
    icon: Icons.emoji_events_rounded,
    isUnlocked: false,
  ),
  Achievement(
    title: 'Gelişim Serisi',
    icon: Icons.trending_up_rounded,
    isUnlocked: true,
  ),
];
