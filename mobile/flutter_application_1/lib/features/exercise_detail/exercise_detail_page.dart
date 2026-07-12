import 'package:flutter/material.dart';

import '../../data/exercise_details_data.dart';
import '../../models/exercise_detail_model.dart';
import '../../widgets/glass_card.dart';
import '../../widgets/premium_background.dart';
import '../../core/constants/app_colors.dart';
import '../../core/state/favorite_exercises_store.dart';
class ExerciseDetailPage extends StatelessWidget {
  final String exerciseName;

  const ExerciseDetailPage({super.key, required this.exerciseName});

  @override
  Widget build(BuildContext context) {
    final ExerciseDetail detail = getExerciseDetailByName(exerciseName);

    return Scaffold(
      body: PremiumBackground(
        child: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(16, 18, 16, 24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Row(
  children: [
    IconButton(
      onPressed: () => Navigator.pop(context),
      icon: const Icon(Icons.arrow_back_rounded),
    ),
    Expanded(
      child: Text(
        detail.name,
        textAlign: TextAlign.center,
        style: const TextStyle(
          fontSize: 22,
          fontWeight: FontWeight.w900,
        ),
      ),
    ),
    ValueListenableBuilder<Set<String>>(
      valueListenable: FavoriteExercisesStore.favorites,
      builder: (context, favorites, child) {
        final isFavorite = favorites.contains(detail.name);

        return IconButton(
          onPressed: () {
            FavoriteExercisesStore.toggleFavorite(detail.name);

            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(
                  isFavorite
                      ? '${detail.name} favorilerden çıkarıldı.'
                      : '${detail.name} favorilere eklendi.',
                ),
              ),
            );
          },
          icon: Icon(
            isFavorite ? Icons.favorite_rounded : Icons.favorite_border_rounded,
            color: isFavorite ? Colors.redAccent : AppColors.textSoft,
          ),
        );
      },
    ),
  ],
),
                const SizedBox(height: 16),
                GlassCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Egzersiz Açıklaması',
                        style: TextStyle(
                          fontSize: 19,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                      const SizedBox(height: 10),
                      Text(
                        detail.description,
                        style: const TextStyle(
                          color: AppColors.textSoft,
                          height: 1.5,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
                _DetailListCard(
                  title: 'Hedef Kaslar',
                  icon: Icons.fitness_center_rounded,
                  items: detail.targetMuscles,
                ),
                const SizedBox(height: 16),
                _DetailListCard(
                  title: 'Yaygın Form Hataları',
                  icon: Icons.warning_amber_rounded,
                  items: detail.commonMistakes,
                ),
                const SizedBox(height: 16),
                _DetailListCard(
                  title: 'Uygulama İpuçları',
                  icon: Icons.lightbulb_rounded,
                  items: detail.tips,
                ),
                const SizedBox(height: 16),
                GlassCard(
                  child: Row(
                    children: const [
                      Icon(
                        Icons.psychology_rounded,
                        color: AppColors.purpleGlow,
                        size: 30,
                      ),
                      SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          'Bu bilgiler analiz sonucunu daha iyi yorumlaman için hazırlanmıştır.',
                          style: TextStyle(
                            color: AppColors.textSoft,
                            height: 1.4,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _DetailListCard extends StatelessWidget {
  final String title;
  final IconData icon;
  final List<String> items;

  const _DetailListCard({
    required this.title,
    required this.icon,
    required this.items,
  });

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, color: AppColors.purpleGlow),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  title,
                  style: const TextStyle(
                    fontSize: 19,
                    fontWeight: FontWeight.w900,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          ...items.map(
            (item) => Padding(
              padding: const EdgeInsets.only(bottom: 9),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(
                    Icons.check_circle_rounded,
                    color: AppColors.purpleGlow,
                    size: 18,
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(item, style: const TextStyle(height: 1.4)),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
