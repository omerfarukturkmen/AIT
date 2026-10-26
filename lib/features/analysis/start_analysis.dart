import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../../app.dart';
import '../../data/exercise_catalog.dart';
import 'analysis_progress_page.dart';
import 'record_page.dart';

/// Entry points for a new analysis: pick a video or record one.
abstract final class StartAnalysis {
  static const _maxBytes = 200 * 1024 * 1024;

  static Future<void> fromGallery(
    BuildContext context,
    ExerciseId exercise,
  ) async {
    final l10n = context.l10n;
    final messenger = ScaffoldMessenger.of(context);
    final navigator = Navigator.of(context);

    final video = await ImagePicker().pickVideo(source: ImageSource.gallery);
    if (video == null) return;

    final bytes = await video.readAsBytes();
    if (bytes.lengthInBytes > _maxBytes) {
      messenger.showSnackBar(SnackBar(content: Text(l10n.errorTooLarge)));
      return;
    }
    final name = video.name.isNotEmpty ? video.name : 'video.mp4';
    await navigator.push(
      MaterialPageRoute(
        builder: (_) => AnalysisProgressPage(
          exercise: exercise,
          videoBytes: bytes,
          fileName: name,
        ),
      ),
    );
  }

  static Future<void> withCamera(BuildContext context, ExerciseId exercise) {
    return Navigator.of(
      context,
    ).push(MaterialPageRoute(builder: (_) => RecordPage(exercise: exercise)));
  }
}
